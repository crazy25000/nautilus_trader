from collections import defaultdict
from collections import namedtuple
from itertools import takewhile
import os
import pathlib
import re
from typing import Generator

import fsspec
import orjson
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from tqdm import tqdm

from nautilus_trader.backtest.storage.parsing import _unparse
from nautilus_trader.backtest.storage.parsing import _unparse_value
from nautilus_trader.backtest.storage.parsing import dictionary_columns
from nautilus_trader.backtest.storage.parsing import nautilus_to_dict
from nautilus_trader.model.events import InstrumentStatusEvent
from nautilus_trader.model.instruments.betting import BettingInstrument
from nautilus_trader.model.orderbook.book import OrderBookDelta
from nautilus_trader.model.orderbook.book import OrderBookDeltas
from nautilus_trader.model.orderbook.book import OrderBookSnapshot
from nautilus_trader.model.tick import QuoteTick
from nautilus_trader.model.tick import TradeTick


NewFile = namedtuple("NewFile", "name")
EOStream = namedtuple("EOStream", "")

# TODO (bm) - Line preprocessor not called / used - implement a simple log example
# TODO (bm) - Implement chunking in CSVParser
# TODO (bm) - Implement chunking in ParquetParser


class ByteParser:
    def __init__(
        self,
        instrument_provider_update: callable = None,
    ):
        self.instrument_provider_update = instrument_provider_update

    def read(self, stream: Generator, instrument_provider=None) -> Generator:
        raise NotImplementedError


class CSVParser(ByteParser):
    def read(self, stream: Generator, instrument_provider=None) -> Generator:
        for chunk in stream:
            yield pd.read_csv(chunk)


class TextParser(ByteParser):
    def __init__(
        self,
        line_parser: callable,
        line_preprocessor=None,
        instrument_provider_update=None,
    ):
        """
        Parse bytes of json into nautilus objects

        :param line_parser: Callable that takes a JSON object and yields nautilus objects
        :param line_preprocessor: A context manager for doing any preprocessing (cleaning log lines) of lines before
               json.loads is called. Nautilus objects are returned to the context manager for any post-processing also
               (For example, setting the `timestamp_origin_ns`)
        :param instrument_provider_update (Optional) : An optional hook/callable to update instrument provider before
               data is passed to `line_parser` (in many cases instruments need to be known ahead of parsing)
        """
        self.line_parser = line_parser
        self.line_preprocessor = line_preprocessor
        super().__init__(instrument_provider_update=instrument_provider_update)

    def read(self, stream: Generator, instrument_provider=None) -> Generator:
        raw = b""
        fn = None
        for chunk in stream:
            if isinstance(chunk, NewFile):
                # New file, yield any remaining data, reset bytes
                assert not raw, f"Data remaining at end of file: {fn}"
                fn = chunk.name
                raw = b""
                yield chunk
                continue
            elif chunk is EOStream:
                yield EOStream
                return
            elif chunk is None:
                yield
                continue
            if chunk == b"":
                # This is probably EOF? Append a newline to ensure we emit the previous line
                chunk = b"\n"
            raw += chunk

            lines = raw.split(b"\n")
            raw = lines[-1]
            for line in lines[:-1]:
                if not line:
                    continue
                if self.instrument_provider_update is not None:
                    self.instrument_provider_update(instrument_provider, line)
                yield from self.line_parser(line)


class ParquetParser(ByteParser):
    def read(self, stream: Generator, instrument_provider=None) -> Generator:
        for chunk in stream:
            df = pd.read_parquet(chunk)
            yield df


class DataLoader:
    def __init__(
        self,
        path: str,
        parser: ByteParser,
        fs_protocol="file",
        glob_pattern="**",
        progress=False,
        line_preprocessor: callable = None,
        chunksize=-1,
        compression="infer",
        instrument_provider=None,
        instrument_loader: callable = None,
    ):
        """
        Discover files and stream bytes of data from a local or remote filesystem

        :param path: A resolvable path; a file, folder, or a remote location via fsspec
        :param parser: A `BaseReader` subclass that can convert bytes into nautilus objects.
        :param fs_protocol: fsspec protocol; allows remote access - defaults to `file`
        :param progress: Show progress when loading individual files
        :param glob_pattern: Glob pattern to search for files
        :param glob_pattern: Glob pattern to search for files
        :param compression: The file compression, defaults to 'infer' by file extension
        :param line_preprocessor: A callable that handles any preprocessing of the data
        :param chunksize: Chunk size (in bytes) for processing data, -1 for no limit (will chunk per file).
        """
        self._path = path
        self.parser = parser
        self.fs_protocol = fs_protocol
        self.progress = progress
        self.chunk_size = chunksize
        self.compression = compression
        self.glob_pattern = glob_pattern
        self.line_preprocessor = line_preprocessor
        self.fs = fsspec.filesystem(self.fs_protocol)
        self.instrument_provider = instrument_provider
        self.instrument_loader = instrument_loader
        self.path = sorted(self._resolve_path(path=self._path))

    def _resolve_path(self, path: str):
        if self.fs.isfile(path):
            return [path]
        # We have a directory
        if not path.endswith("/"):
            path += "/"
        if self.fs.isdir(path):
            files = self.fs.glob(f"{path}{self.glob_pattern}")
            assert (
                files
            ), f"Found no files with path={str(path)}, glob={self.glob_pattern}"
            return [f for f in files if self.fs.isfile(f)]
        else:
            raise ValueError("path argument must be str and a valid directory or file")

    def stream_bytes(self, progress=False):
        path = self.path if not progress else tqdm(self.path)
        for fn in path:
            with fsspec.open(fn, compression=self.compression) as f:
                yield NewFile(fn)
                data = 1
                while data:
                    data = f.read(self.chunk_size)
                    yield data
                    yield None  # this is a chunk
        yield EOStream

    def run(self, progress=False):
        stream = self.parser.read(
            stream=self.stream_bytes(progress=progress),
            instrument_provider=self.instrument_provider,
        )
        while 1:
            chunk = list(takewhile(lambda x: x is not None, stream))
            if chunk == [EOStream]:
                break
            if not chunk:
                continue
            # TODO (bm): shithacks - We need a better way to generate instruments?
            if self.instrument_provider is not None:
                # Find any instrument status updates, if we have some, emit instruments first
                instruments = [
                    self.instrument_provider.find(s.instrument_id)
                    for s in chunk
                    if isinstance(s, InstrumentStatusEvent)
                ]
                chunk = instruments + chunk
            yield chunk


class DataCatalog:
    def __init__(self, path=None, fs_protocol=None):
        self.fs = fsspec.filesystem(
            fs_protocol or os.environ.get("NAUTILUS_BACKTEST_FS_PROTOCOL", "file")
        )
        self.root = pathlib.Path(path or os.environ["NAUTILUS_BACKTEST_DIR"])
        self._processed_files_fn = f"{self.root}/.processed_raw_files.json"

    # ---- Loading data ---------------------------------------------------------------------------------------- #

    def import_from_data_loader(self, loader: DataLoader, append_only=False, **kwargs):
        """
        Load data from a DataLoader instance into the backtest catalogue

        :param loader: A DataLoader instance
        :param append_only: Don't read existing data to dedupe + sort. Use this is you're confident your data is ordered
        :param kwargs: kwargs passed through to `ParquetWriter`

        :return:
        """
        for chunk in loader.run(progress=kwargs.pop("progress", False)):
            self._write_chunks(chunk=chunk, append_only=append_only, **kwargs)

    def _save_processed_raw_files(self, files):
        # TODO (bm) - we should save a hash of the contents alongside the filename to check for changes
        # load existing
        existing = self._load_processed_raw_files()
        new = set(files + existing)
        with self.fs.open(self._processed_files_fn, "wb") as f:
            return f.write(orjson.dumps(sorted(new)))

    def _load_processed_raw_files(self):
        if self.fs.exists(self._processed_files_fn):
            with self.fs.open(self._processed_files_fn, "rb") as f:
                return orjson.loads(f.read())
        else:
            return []

    def _write_chunks(self, chunk, append_only=False, **kwargs):  # noqa: C901
        processed_raw_files = self._load_processed_raw_files()
        log_filenames = kwargs.pop("log_filenames", False)

        # Split objects into their respective tables
        type_conv = {OrderBookDeltas: OrderBookDelta, OrderBookSnapshot: OrderBookDelta}
        tables = defaultdict(dict)
        skip_file = False
        for obj in chunk:
            if skip_file:
                continue
            if isinstance(obj, NewFile):
                if log_filenames:
                    print(obj.name)
                if obj.name in processed_raw_files:
                    skip_file = True
                else:
                    skip_file = False
                    processed_raw_files.append(obj.name)
                continue

            # TODO (bm) - better handling of instruments -> currency we're writing a file per instrument
            cls = type_conv.get(type(obj), type(obj))
            for data in nautilus_to_dict(obj):
                instrument_id = data["instrument_id"]
                if instrument_id not in tables[cls]:
                    tables[cls][instrument_id] = []
                tables[cls][instrument_id].append(data)

        for cls in tables:
            for ins_id in tables[cls]:
                fn = self.root.joinpath(f"{camel_to_snake_case(cls.__name__)}.parquet")

                df = pd.DataFrame(tables[cls][ins_id])

                if df.empty:
                    continue

                # Load any existing data, drop dupes
                if not append_only:
                    if self.fs.exists(fn):
                        existing = pd.read_parquet(
                            str(fn),
                            fs=self.fs,
                            filters=[("instrument_id", "=", ins_id)],
                        )
                        df = df.append(existing).drop_duplicates()
                        # Remove file, will be written again
                        self.fs.rm(fn, recursive=True)

                df = df.astype(
                    {k: "category" for k in dictionary_columns.get(cls, [])}
                ).sort_values("timestamp_ns")
                table = pa.Table.from_pandas(df)
                pq.write_to_dataset(
                    table=table,
                    root_path=str(fn),
                    filesystem=self.fs,
                    partition_cols=["instrument_id"],
                    use_legacy_dataset=True,
                    version="2.0",
                    **kwargs,
                )

            # Save any new processed files
        self._save_processed_raw_files(files=processed_raw_files)

    def clear_cache(self, **kwargs):
        force = kwargs.get("FORCE", False)
        if not force:
            print(
                "Are you sure you want to clear the WHOLE BACKTEST CACHE?, if so, call clear_cache(FORCE=True)"
            )
        else:
            self.fs.rm(self.root, recursive=True)

    # ---- Queries ---------------------------------------------------------------------------------------- #

    def load_backtest_data(
        self,
        instrument_ids=None,
        start_timestamp=None,
        end_timestamp=None,
        order_book_deltas=True,
        trade_ticks=True,
        quote_ticks=False,
        instrument_status_events=True,
        chunksize=None,
    ):
        """
        Load backtest data objects from the catalogue

        :param instrument_ids: A list of instrument_ids to load data for
        :param start_timestamp: The starting timestamp of the data to load
        :param end_timestamp: The ending timestamp of the data to load
        :param order_book_deltas: Whether to load order book delta
        :param trade_ticks: Whether to load trade ticks
        :param instrument_status_events: Whether to load instrument status events
        :param chunksize: The chunksize to return (used for streaming backtest). Use None for a loading all the data.
        :return:
        """
        assert instrument_ids is None or isinstance(
            instrument_ids, list
        ), "instrument_ids must be list"
        queries = [
            (order_book_deltas, self.order_book_deltas),
            (trade_ticks, self.trade_ticks),
            (instrument_status_events, self.instrument_status_events),
            (quote_ticks, self.quote_ticks),
        ]
        data = []
        start_timestamp_filter = (
            [("timestamp_ns", ">=", parse_timestamp(start_timestamp))]
            if start_timestamp
            else []
        )
        end_timestamp_filter = (
            [("timestamp_ns", "<=", parse_timestamp(end_timestamp))]
            if end_timestamp
            else []
        )
        filters = (start_timestamp_filter + end_timestamp_filter) or None
        for to_load, query in queries:
            if to_load:
                data.extend(query(instrument_ids=instrument_ids, filters=filters))

        return data

    def _query(self, filename, filters=None, instrument_ids=None):
        if instrument_ids is not None and not isinstance(instrument_ids, list):
            instrument_ids = [instrument_ids]
        instrument_filter = (
            [("instrument_id", "isin", instrument_ids)] if instrument_ids else []
        )
        filters = (filters or []) + instrument_filter

        return pd.read_parquet(
            path=f"{self.root}/{filename}.parquet",
            filesystem=self.fs,
            filters=filters or None,
        )

    @staticmethod
    def _make_objects(df, cls, ignore_keys=None):
        rows = [
            {
                k: _unparse_value(cls=cls, k=k, v=v)
                for k, v in r.items()
                if k not in (ignore_keys or ())
            }
            for _, r in df.iterrows()
        ]
        return [_unparse(cls, r) for r in rows]

    def instruments(self, filters=None):
        """
        :param filters: A list of tuple arrow filters, ie [("instrument_id", "=", "BTCUSD")]
        :return:
        """
        df = self._query("betting_instrument", filters=filters)
        return self._make_objects(
            df=df, cls=BettingInstrument, ignore_keys=("instrument_id",)
        )

    def instrument_status_events(self, instrument_ids=None, filters=None):
        df = self._query(
            "instrument_status_event", instrument_ids=instrument_ids, filters=filters
        )
        return self._make_objects(df=df, cls=InstrumentStatusEvent, ignore_keys=None)

    def trade_ticks(self, instrument_ids=None, filters=None):
        df = self._query("trade_tick", instrument_ids=instrument_ids, filters=filters)
        return self._make_objects(df=df, cls=TradeTick, ignore_keys=None)

    def quote_ticks(self, instrument_ids=None, filters=None):
        df = self._query("quote_tick", instrument_ids=instrument_ids, filters=filters)
        return self._make_objects(df=df, cls=QuoteTick, ignore_keys=None)

    def order_book_deltas(self, instrument_ids=None, filters=None):
        df = self._query(
            "order_book_delta", instrument_ids=instrument_ids, filters=filters
        )
        return self._make_objects(df=df, cls=OrderBookDelta, ignore_keys=None)


def camel_to_snake_case(s):
    return re.sub(r"(?<!^)(?=[A-Z])", "_", s).lower()


def parse_timestamp(t):
    return int(pd.Timestamp(t).timestamp() * 1e9)


# def get_digest(fs, path):
#     h = hashlib.sha256()
#
#     with fs.open(path, 'rb') as file:
#         while True:
#             # Reading is buffered, so we can read smaller chunks.
#             chunk = file.read(h.block_size)
#             if not chunk:
#                 break
#             h.update(chunk)
#
#     return h.hexdigest()
