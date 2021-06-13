import pyarrow as pa
import pyarrow.parquet as pq

# TODO - use cytoolz?
from toolz.dicttoolz import merge_with

from nautilus_trader.serialization.arrow.schemas import SCHEMA_TO_TYPE
from nautilus_trader.serialization.arrow.schemas import TYPE_TO_SCHEMA


class ArrowSerializer:
    """
    Provides a serializer for the MessagePack specification.

    """

    @staticmethod
    def to_parquet(buff, objects: list):
        schema = TYPE_TO_SCHEMA[objects[0].__class__]
        mapping = merge_with(list, *[obj.to_dict() for obj in objects])
        table = pa.Table.from_pydict(mapping=mapping, schema=schema)

        with pq.ParquetWriter(buff, schema) as writer:
            writer.write_table(table)
        return buff

    @staticmethod
    def from_parquet(message_bytes, **kwargs):
        table = pq.read_table(message_bytes, **kwargs)
        data = table.to_pydict()
        type_ = SCHEMA_TO_TYPE[table.schema.metadata[b"type"]]
        values = list(
            map(dict, zip(*([(key, val) for val in data[key]] for key in data.keys())))
        )
        return [type_.from_dict_py(v) for v in values]

    # TODO (bm) - Implement for IPC / streaming. See https://arrow.apache.org/docs/python/ipc.html
    # @staticmethod
    # def to_arrow(message: bytes):
    #     """
    #     Serialize the given message to `MessagePack` specification bytes.
    #
    #     Parameters
    #     ----------
    #     message : dict
    #         The message to serialize.
    #
    #     Returns
    #     -------
    #     bytes
    #
    #     """
    #     Condition.not_none(message, "message")
    #
    #     batch = pa.record_batch(data, names=['f0', 'f1', 'f2'])
    #
    #     sink = pa.BufferOutputStream()
    #
    #     writer = pa.ipc.new_stream(sink, batch.schema)
    #     return msgpack.packb(message)
    #
    # @staticmethod
    # def from_arrow(message_bytes: bytes):
    #     """
    #     Deserialize the given `MessagePack` specification bytes to a dictionary.
    #
    #     Parameters
    #     ----------
    #     message_bytes : bytes
    #         The message bytes to deserialize.
    #
    #     Returns
    #     -------
    #     dict[str, object]
    #
    #     """
    #     Condition.not_none(message_bytes, "message_bytes")
    #
    #     return msgpack.unpackb(message_bytes)
