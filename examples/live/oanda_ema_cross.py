from decimal import Decimal
import os
import sys


sys.path.insert(0, str(os.path.abspath(__file__ + "/../../../")))

from examples.strategies.ema_cross_simple import EMACross
from nautilus_trader.adapters.oanda.factories import OandaDataClientFactory
from nautilus_trader.live.node import TradingNode
from nautilus_trader.model.data.bar import BarSpecification
from nautilus_trader.model.enums import BarAggregation
from nautilus_trader.model.enums import PriceType
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import Symbol
from nautilus_trader.model.identifiers import Venue


config = dict(
    trader={"name": "TESTER", "id_tag": "001"},
    system={
        "loop_debug": True,
        "timeout_connection": 100000000.0,
        "timeout_reconciliation": 100000000.0,
        "timeout_portfolio": 100000000.0,
        "timeout_disconnection": 5.0,
        "check_residuals_delay": 5.0,
    },
    logging={"level_stdout": "INF"},
    database={
        "type": "redis",
        "host": "localhost",
        "port": 6379,
    },
    data_engine={},
    risk_engine={},
    exec_engine={},
    strategy={
        "load_state": False,
        "save_state": False,
    },
    data_clients={
        "OANDA": {
            "api_token": "OANDA_API_TOKEN",
            "account_id": "OANDA_ACCOUNT_ID",
        },
    },
    exec_clients={},
)

instrument1 = InstrumentId(
    symbol=Symbol("AUD/USD"),
    venue=Venue("OANDA"),
)

strategy1 = EMACross(
    instrument_id=instrument1,
    bar_spec=BarSpecification(1, BarAggregation.MINUTE, PriceType.MID),
    fast_ema_period=10,
    slow_ema_period=20,
    trade_size=Decimal(10000),
    order_id_tag="001",
)
print(config)
node = TradingNode(strategies=[strategy1], config={**config})  # type: ignore
node.add_data_client_factory("OANDA", OandaDataClientFactory)
node.build()


if __name__ == "__main__":
    try:
        node.start()
    finally:
        node.dispose()
