from decimal import Decimal
from functools import partial
import os
import pathlib
import pickle

import fsspec
import pandas as pd
import pytest

from nautilus_trader.backtest.config import BacktestConfig
from nautilus_trader.backtest.config import BacktestDataConfig
from nautilus_trader.backtest.config import BacktestVenueConfig
from nautilus_trader.backtest.config import build_graph
from nautilus_trader.backtest.data_loader import CSVParser
from nautilus_trader.backtest.data_loader import DataCatalog
from nautilus_trader.backtest.data_loader import DataLoader
from nautilus_trader.common.providers import InstrumentProvider
from nautilus_trader.core.datetime import millis_to_nanos
from nautilus_trader.indicators.average.ema import ExponentialMovingAverage
from nautilus_trader.model.bar import BarSpecification
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.enums import BarAggregation
from nautilus_trader.model.enums import PriceType
from nautilus_trader.model.objects import Money
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity
from nautilus_trader.model.tick import QuoteTick
from tests.test_kit import PACKAGE_ROOT
from tests.test_kit.providers import TestInstrumentProvider
from tests.test_kit.strategies import EMACross
from tests.test_kit.stubs import TestStubs


TEST_DATA_DIR = str(pathlib.Path(PACKAGE_ROOT).joinpath("data"))
CATALOG_DIR = TEST_DATA_DIR + "/catalog"


@pytest.fixture(scope="module")
def catalog_dir():
    # Ensure we have a catalog directory, and its cleaned up after use
    fs = fsspec.filesystem("file")
    catalog = str(pathlib.Path(CATALOG_DIR))
    os.environ.update({"NAUTILUS_BACKTEST_DIR": str(catalog)})
    if fs.exists(catalog):
        fs.rm(catalog, recursive=True)
    fs.mkdir(catalog)
    yield
    fs.rm(catalog, recursive=True)


@pytest.fixture(scope="module")
def data_loader():
    def parse_csv_tick(df, instrument_id, state=None):
        yield TestInstrumentProvider.default_fx_ccy("AUD/USD")
        for r in df.values:
            ts = millis_to_nanos(pd.Timestamp(r[0]).timestamp())
            tick = QuoteTick(
                instrument_id=instrument_id,
                bid=Price.from_str(str(r[1])),
                ask=Price.from_str(str(r[2])),
                bid_size=Quantity.from_int(1_000_000),
                ask_size=Quantity.from_int(1_000_000),
                ts_event_ns=ts,
                ts_recv_ns=ts,
            )
            yield tick

    instrument_provider = InstrumentProvider()
    instrument_provider.add(TestInstrumentProvider.default_fx_ccy("AUD/USD"))
    loader = DataLoader(
        path=TEST_DATA_DIR,
        parser=CSVParser(
            parser=partial(parse_csv_tick, instrument_id=TestStubs.audusd_id())
        ),
        glob_pattern="truefx-audusd-ticks.csv",
        instrument_provider=instrument_provider,
    )
    return loader


@pytest.fixture(scope="module")
def catalog(catalog_dir, data_loader):
    catalog = DataCatalog()
    catalog.import_from_data_loader(loader=data_loader)
    assert len(catalog.instruments()) == 1
    assert len(catalog.quote_ticks()) == 100000
    return catalog


@pytest.fixture(scope="module")
def backtest_config(catalog):
    instrument = TestInstrumentProvider.default_fx_ccy("AUD/USD")
    return BacktestConfig(
        venues=[
            BacktestVenueConfig(
                name="SIM",
                venue_type="ECN",
                oms_type="HEDGING",
                account_type="MARGIN",
                base_currency=USD,
                starting_balances=[Money(1_000_000, USD)],
            )
        ],
        instruments=[instrument],
        data_config=[
            BacktestDataConfig(
                data_type=QuoteTick,
                instrument_id=instrument.id.value,
                start_time=1580398089820000,
                end_time=1580504394501000,
            )
        ],
        strategies=[
            (
                EMACross,
                dict(
                    instrument_id=instrument.id,
                    bar_spec=BarSpecification(15, BarAggregation.MINUTE, PriceType.BID),
                    trade_size=Decimal(1_000_000),
                    fast_ema=10,
                    slow_ema=20,
                ),
            )
        ],
    )


def test_backtest_config_pickle(backtest_config):
    pickle.loads(pickle.dumps(backtest_config))  # noqa: S301


def test_backtest_data_config_load(catalog):
    instrument = TestInstrumentProvider.default_fx_ccy("AUD/USD")
    c = BacktestDataConfig(
        data_type=QuoteTick,
        instrument_id=instrument.id.value,
        start_time=1580398089820000,
        end_time=1580504394501000,
    )
    result = c.query
    expected = {
        "as_nautilus": True,
        "cls": QuoteTick,
        "instrument_ids": ["AUD/USD.SIM"],
        "start": 1580398089820000,
        "end": 1580504394501000,
    }
    assert result == expected


@pytest.mark.skip
def test_backtest_config_replace(backtest_config):
    new = backtest_config.replace(path="strategies.AUDUSD.slow_ewma", value=50)
    assert new.strategies[0].slow_ema == ExponentialMovingAverage(50)


def test_backtest_run(backtest_config):
    # TODO (bm) - Not working with distributed yet
    # from distributed import Client
    # client = Client()
    tasks = build_graph([backtest_config])
    result = tasks[0].compute()
    assert result
