# -------------------------------------------------------------------------------------------------
#  Copyright (C) 2015-2021 Nautech Systems Pty Ltd. All rights reserved.
#  https://nautechsystems.io
#
#  Licensed under the GNU Lesser General Public License Version 3.0 (the "License");
#  You may not use this file except in compliance with the License.
#  You may obtain a copy of the License at https://www.gnu.org/licenses/lgpl-3.0.en.html
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# -------------------------------------------------------------------------------------------------

from decimal import Decimal

import pytest

from nautilus_trader.adapters.betfair.common import BETFAIR_VENUE
from nautilus_trader.common.clock import TestClock
from nautilus_trader.common.factories import OrderFactory
from nautilus_trader.common.logging import Logger
from nautilus_trader.core.uuid import uuid4
from nautilus_trader.execution.engine import ExecutionEngine
from nautilus_trader.model.c_enums.order_side import OrderSide
from nautilus_trader.model.currencies import BTC
from nautilus_trader.model.currencies import ETH
from nautilus_trader.model.currencies import GBP
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.currencies import USDT
from nautilus_trader.model.data.tick import QuoteTick
from nautilus_trader.model.enums import AccountType
from nautilus_trader.model.events.account import AccountState
from nautilus_trader.model.identifiers import AccountId
from nautilus_trader.model.identifiers import PositionId
from nautilus_trader.model.identifiers import StrategyId
from nautilus_trader.model.identifiers import TraderId
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.identifiers import VenueOrderId
from nautilus_trader.model.objects import AccountBalance
from nautilus_trader.model.objects import Money
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity
from nautilus_trader.model.position import Position
from nautilus_trader.msgbus.message_bus import MessageBus
from nautilus_trader.risk.engine import RiskEngine
from nautilus_trader.trading.portfolio import Portfolio
from nautilus_trader.trading.portfolio import PortfolioFacade
from tests.test_kit.providers import TestInstrumentProvider
from tests.test_kit.stubs import TestStubs


SIM = Venue("SIM")
BINANCE = Venue("BINANCE")
BITMEX = Venue("BITMEX")
BETFAIR = BETFAIR_VENUE

AUDUSD_SIM = TestInstrumentProvider.default_fx_ccy("AUD/USD")
GBPUSD_SIM = TestInstrumentProvider.default_fx_ccy("GBP/USD")
USDJPY_SIM = TestInstrumentProvider.default_fx_ccy("USD/JPY")
BTCUSDT_BINANCE = TestInstrumentProvider.btcusdt_binance()
BTCUSD_BITMEX = TestInstrumentProvider.xbtusd_bitmex()
ETHUSD_BITMEX = TestInstrumentProvider.ethusd_bitmex()
BETTING_INSTRUMENT = TestInstrumentProvider.betting_instrument()


class TestPortfolioFacade:
    def test_account_raises_not_implemented_error(self):
        # Arrange
        portfolio = PortfolioFacade()

        # Act
        # Assert
        with pytest.raises(NotImplementedError):
            portfolio.account(SIM)

    def test_order_margin_raises_not_implemented_error(self):
        # Arrange
        portfolio = PortfolioFacade()

        # Act
        # Assert
        with pytest.raises(NotImplementedError):
            portfolio.initial_margins(SIM)

    def test_position_margin_raises_not_implemented_error(self):
        # Arrange
        portfolio = PortfolioFacade()

        # Act
        # Assert
        with pytest.raises(NotImplementedError):
            portfolio.maint_margins(SIM)

    def test_unrealized_pnl_for_venue_raises_not_implemented_error(self):
        # Arrange
        portfolio = PortfolioFacade()

        # Act
        # Assert
        with pytest.raises(NotImplementedError):
            portfolio.unrealized_pnls(SIM)

    def test_unrealized_pnl_for_instrument_raises_not_implemented_error(self):
        # Arrange
        portfolio = PortfolioFacade()

        # Act
        # Assert
        with pytest.raises(NotImplementedError):
            portfolio.unrealized_pnl(BTCUSDT_BINANCE.id)

    def test_market_value_raises_not_implemented_error(self):
        # Arrange
        portfolio = PortfolioFacade()

        # Act
        # Assert
        with pytest.raises(NotImplementedError):
            portfolio.net_exposure(AUDUSD_SIM.id)

    def test_market_values_raises_not_implemented_error(self):
        # Arrange
        portfolio = PortfolioFacade()

        # Act
        # Assert
        with pytest.raises(NotImplementedError):
            portfolio.net_exposures(BITMEX)

    def test_net_position_raises_not_implemented_error(self):
        # Arrange
        portfolio = PortfolioFacade()

        # Act
        # Assert
        with pytest.raises(NotImplementedError):
            portfolio.net_position(GBPUSD_SIM.id)

    def test_is_net_long_raises_not_implemented_error(self):
        # Arrange
        portfolio = PortfolioFacade()

        # Act
        # Assert
        with pytest.raises(NotImplementedError):
            portfolio.is_net_long(GBPUSD_SIM.id)

    def test_is_net_short_raises_not_implemented_error(self):
        # Arrange
        portfolio = PortfolioFacade()

        # Act
        # Assert
        with pytest.raises(NotImplementedError):
            portfolio.is_net_short(GBPUSD_SIM.id)

    def test_is_flat_raises_not_implemented_error(self):
        # Arrange
        portfolio = PortfolioFacade()

        # Act
        # Assert
        with pytest.raises(NotImplementedError):
            portfolio.is_flat(GBPUSD_SIM.id)

    def test_is_completely_flat_raises_not_implemented_error(self):
        # Arrange
        portfolio = PortfolioFacade()

        # Act
        # Assert
        with pytest.raises(NotImplementedError):
            portfolio.is_completely_flat()


class TestPortfolio:
    def setup(self):
        # Fixture Setup
        clock = TestClock()
        logger = Logger(clock)
        trader_id = TraderId("TESTER-000")

        self.order_factory = OrderFactory(
            trader_id=trader_id,
            strategy_id=StrategyId("S-001"),
            clock=TestClock(),
        )

        self.msgbus = MessageBus(
            clock=clock,
            logger=logger,
        )

        self.cache = TestStubs.cache()

        self.portfolio = Portfolio(
            msgbus=self.msgbus,
            cache=self.cache,
            clock=clock,
            logger=logger,
        )

        self.exec_engine = ExecutionEngine(
            trader_id=trader_id,
            msgbus=self.msgbus,
            cache=self.cache,
            clock=clock,
            logger=logger,
        )

        self.risk_engine = RiskEngine(
            exec_engine=self.exec_engine,
            msgbus=self.msgbus,
            cache=self.cache,
            clock=clock,
            logger=logger,
        )

        # Prepare components
        self.cache.add_instrument(AUDUSD_SIM)
        self.cache.add_instrument(GBPUSD_SIM)
        self.cache.add_instrument(BTCUSDT_BINANCE)
        self.cache.add_instrument(BTCUSD_BITMEX)
        self.cache.add_instrument(ETHUSD_BITMEX)
        self.cache.add_instrument(BETTING_INSTRUMENT)

    def test_account_when_no_account_returns_none(self):
        # Arrange
        # Act
        # Assert
        assert self.portfolio.account(SIM) is None

    def test_account_when_account_returns_the_account_facade(self):
        # Arrange
        account_state = AccountState(
            account_id=AccountId("BINANCE", "1513111"),
            account_type=AccountType.CASH,
            base_currency=None,
            reported=True,
            balances=[
                AccountBalance(
                    BTC,
                    Money(10.00000000, BTC),
                    Money(0.00000000, BTC),
                    Money(10.00000000, BTC),
                )
            ],
            info={},
            event_id=uuid4(),
            ts_updated_ns=0,
            timestamp_ns=0,
        )
        self.exec_engine.process(account_state)

        # Act
        result = self.portfolio.account(BINANCE)

        # Assert
        assert result.id.issuer == "BINANCE"

    def test_net_position_when_no_positions_returns_zero(self):
        # Arrange
        # Act
        # Assert
        assert self.portfolio.net_position(AUDUSD_SIM.id) == Decimal(0)

    def test_is_net_long_when_no_positions_returns_false(self):
        # Arrange
        # Act
        # Assert
        assert self.portfolio.is_net_long(AUDUSD_SIM.id) is False

    def test_is_net_short_when_no_positions_returns_false(self):
        # Arrange
        # Act
        # Assert
        assert self.portfolio.is_net_short(AUDUSD_SIM.id) is False

    def test_is_flat_when_no_positions_returns_true(self):
        # Arrange
        # Act
        # Assert
        assert self.portfolio.is_flat(AUDUSD_SIM.id) is True

    def test_is_completely_flat_when_no_positions_returns_true(self):
        # Arrange
        # Act
        # Assert
        assert self.portfolio.is_flat(AUDUSD_SIM.id) is True

    def test_unrealized_pnl_for_instrument_when_no_instrument_returns_none(self):
        # Arrange
        # Act
        # Assert
        assert self.portfolio.unrealized_pnl(USDJPY_SIM.id) is None

    def test_unrealized_pnl_for_venue_when_no_account_returns_empty_dict(self):
        # Arrange
        # Act
        # Assert
        assert self.portfolio.unrealized_pnls(SIM) == {}

    def test_initial_margins_when_no_account_returns_none(self):
        # Arrange
        # Act
        # Assert
        assert self.portfolio.initial_margins(SIM) is None

    def test_maint_margins_when_no_account_returns_none(self):
        # Arrange
        # Act
        # Assert
        assert self.portfolio.maint_margins(SIM) is None

    def test_open_value_when_no_account_returns_none(self):
        # Arrange
        # Act
        # Assert
        assert self.portfolio.net_exposures(SIM) is None

    def test_update_tick(self):
        # Arrange
        tick = TestStubs.quote_tick_5decimal(GBPUSD_SIM.id)

        # Act
        self.portfolio.update_tick(tick)

        # Assert
        assert self.portfolio.unrealized_pnl(GBPUSD_SIM.id) is None

    def test_update_orders_working(self):
        # Arrange
        state = AccountState(
            account_id=AccountId("BINANCE", "01234"),
            account_type=AccountType.CASH,
            base_currency=None,  # Multi-currency account
            reported=True,
            balances=[
                AccountBalance(
                    BTC,
                    Money(10.00000000, BTC),
                    Money(0.00000000, BTC),
                    Money(10.00000000, BTC),
                ),
                AccountBalance(
                    ETH,
                    Money(20.00000000, ETH),
                    Money(0.00000000, ETH),
                    Money(20.00000000, ETH),
                ),
            ],
            info={},
            event_id=uuid4(),
            ts_updated_ns=0,
            timestamp_ns=0,
        )

        self.exec_engine.process(state)

        # Create two working orders
        order1 = self.order_factory.stop_market(
            BTCUSDT_BINANCE.id,
            OrderSide.BUY,
            Quantity.from_str("10.5"),
            Price.from_str("25000.00"),
        )

        order2 = self.order_factory.stop_market(
            BTCUSDT_BINANCE.id,
            OrderSide.BUY,
            Quantity.from_str("10.5"),
            Price.from_str("25000.00"),
        )

        self.exec_engine.cache.add_order(order1, PositionId.null())
        self.exec_engine.cache.add_order(order2, PositionId.null())

        # Push states to ACCEPTED
        order1.apply(TestStubs.event_order_submitted(order1))
        self.exec_engine.cache.update_order(order1)
        order1.apply(TestStubs.event_order_accepted(order1))
        self.exec_engine.cache.update_order(order1)

        filled1 = TestStubs.event_order_filled(
            order1,
            instrument=BTCUSDT_BINANCE,
            position_id=PositionId("P-1"),
            strategy_id=StrategyId("S-1"),
            last_px=Price.from_str("25000.00"),
        )
        self.exec_engine.process(filled1)

        # Update the last quote
        last = QuoteTick(
            BTCUSDT_BINANCE.id,
            Price.from_str("25001.00"),
            Price.from_str("25002.00"),
            Quantity.from_int(1),
            Quantity.from_int(1),
            0,
            0,
        )

        # Act
        self.portfolio.update_tick(last)
        self.portfolio.initialize_orders()

        # Assert
        assert self.portfolio.initial_margins(BINANCE) == {}

    def test_order_accept_updates_initial_margin(self):
        # Arrange
        state = AccountState(
            account_id=AccountId("BETFAIR", "01234"),
            account_type=AccountType.CASH,
            base_currency=None,  # Multi-currency account
            reported=True,
            balances=[
                AccountBalance(
                    currency=GBP,
                    total=Money(1000, GBP),
                    free=Money(1000, GBP),
                    locked=Money(0, GBP),
                ),
            ],
            info={},
            event_id=uuid4(),
            ts_updated_ns=0,
            timestamp_ns=0,
        )

        self.exec_engine.process(state)

        # Create a passive order
        order1 = self.order_factory.limit(
            BETTING_INSTRUMENT.id,
            OrderSide.BUY,
            Quantity.from_str("100"),
            Price.from_str("0.5"),
        )

        self.exec_engine.cache.add_order(order1, PositionId.null())

        # Push states to ACCEPTED
        order1.apply(TestStubs.event_order_submitted(order1))
        order1.apply(TestStubs.event_order_accepted(order1, venue_order_id=VenueOrderId("1")))
        self.exec_engine.cache.update_order(order1)

        # Act
        self.portfolio.initialize_orders()

        # Assert
        assert self.portfolio.initial_margins(BETFAIR)[GBP] == Money(200, GBP)

    def test_update_positions(self):
        # Arrange
        state = AccountState(
            account_id=AccountId("BINANCE", "01234"),
            account_type=AccountType.CASH,
            base_currency=None,  # Multi-currency account
            reported=True,
            balances=[
                AccountBalance(
                    BTC,
                    Money(10.00000000, BTC),
                    Money(0.00000000, BTC),
                    Money(10.00000000, BTC),
                ),
                AccountBalance(
                    ETH,
                    Money(20.00000000, ETH),
                    Money(0.00000000, ETH),
                    Money(20.00000000, ETH),
                ),
            ],
            info={},
            event_id=uuid4(),
            ts_updated_ns=0,
            timestamp_ns=0,
        )

        self.exec_engine.process(state)

        # Create a closed position
        order1 = self.order_factory.market(
            BTCUSDT_BINANCE.id,
            OrderSide.BUY,
            Quantity.from_str("10.50000000"),
        )

        order2 = self.order_factory.market(
            BTCUSDT_BINANCE.id,
            OrderSide.SELL,
            Quantity.from_str("10.50000000"),
        )

        self.exec_engine.cache.add_order(order1, PositionId.null())
        self.exec_engine.cache.add_order(order2, PositionId.null())

        # Push states to ACCEPTED
        order1.apply(TestStubs.event_order_submitted(order1))
        self.exec_engine.cache.update_order(order1)
        order1.apply(TestStubs.event_order_accepted(order1))
        self.exec_engine.cache.update_order(order1)

        fill1 = TestStubs.event_order_filled(
            order1,
            instrument=BTCUSDT_BINANCE,
            position_id=PositionId("P-1"),
            strategy_id=StrategyId("S-1"),
            last_px=Price.from_str("25000.00"),
        )

        fill2 = TestStubs.event_order_filled(
            order2,
            instrument=BTCUSDT_BINANCE,
            position_id=PositionId("P-1"),
            strategy_id=StrategyId("S-1"),
            last_px=Price.from_str("25000.00"),
        )

        position1 = Position(instrument=BTCUSDT_BINANCE, fill=fill1)
        position1.apply(fill2)

        order3 = self.order_factory.market(
            BTCUSDT_BINANCE.id,
            OrderSide.BUY,
            Quantity.from_str("10.00000000"),
        )

        fill3 = TestStubs.event_order_filled(
            order3,
            instrument=BTCUSDT_BINANCE,
            position_id=PositionId("P-2"),
            strategy_id=StrategyId("S-1"),
            last_px=Price.from_str("25000.00"),
        )

        position2 = Position(instrument=BTCUSDT_BINANCE, fill=fill3)

        # Update the last quote
        last = QuoteTick(
            BTCUSDT_BINANCE.id,
            Price.from_str("25001.00"),
            Price.from_str("25002.00"),
            Quantity.from_int(1),
            Quantity.from_int(1),
            0,
            0,
        )

        # Act
        self.cache.add_position(position1)
        self.cache.add_position(position2)
        self.portfolio.initialize_positions()
        self.portfolio.update_tick(last)

        # Assert
        assert self.portfolio.is_net_long(BTCUSDT_BINANCE.id)

    def test_opening_one_long_position_updates_portfolio(self):
        # Arrange
        state = AccountState(
            account_id=AccountId("BINANCE", "01234"),
            account_type=AccountType.CASH,
            base_currency=None,  # Multi-currency account
            reported=True,
            balances=[
                AccountBalance(
                    BTC,
                    Money(10.00000000, BTC),
                    Money(0.00000000, BTC),
                    Money(10.00000000, BTC),
                ),
                AccountBalance(
                    ETH,
                    Money(20.00000000, ETH),
                    Money(0.00000000, ETH),
                    Money(20.00000000, ETH),
                ),
            ],
            info={},
            event_id=uuid4(),
            ts_updated_ns=0,
            timestamp_ns=0,
        )

        self.exec_engine.process(state)

        order = self.order_factory.market(
            BTCUSDT_BINANCE.id,
            OrderSide.BUY,
            Quantity.from_str("10.000000"),
        )

        fill = TestStubs.event_order_filled(
            order=order,
            instrument=BTCUSDT_BINANCE,
            position_id=PositionId("P-123456"),
            strategy_id=StrategyId("S-001"),
            last_px=Price.from_str("10500.00"),
        )

        last = QuoteTick(
            BTCUSDT_BINANCE.id,
            Price.from_str("10510.00"),
            Price.from_str("10511.00"),
            Quantity.from_str("1.000000"),
            Quantity.from_str("1.000000"),
            0,
            0,
        )

        self.cache.add_quote_tick(last)
        self.portfolio.update_tick(last)

        position = Position(instrument=BTCUSDT_BINANCE, fill=fill)

        # Act
        self.cache.add_position(position)
        self.portfolio.update_position(TestStubs.event_position_opened(position))

        # Assert
        assert self.portfolio.net_exposures(BINANCE) == {USDT: Money(105100.00000000, USDT)}
        assert self.portfolio.unrealized_pnls(BINANCE) == {USDT: Money(100.00000000, USDT)}
        assert self.portfolio.maint_margins(BINANCE) == {USDT: Money(105.10000000, USDT)}
        assert self.portfolio.net_exposure(BTCUSDT_BINANCE.id) == Money(105100.00000000, USDT)
        assert self.portfolio.unrealized_pnl(BTCUSDT_BINANCE.id) == Money(100.00000000, USDT)
        assert self.portfolio.net_position(order.instrument_id) == Decimal("10.00000000")
        assert self.portfolio.is_net_long(order.instrument_id)
        assert not self.portfolio.is_net_short(order.instrument_id)
        assert not self.portfolio.is_flat(order.instrument_id)
        assert not self.portfolio.is_completely_flat()

    def test_opening_one_short_position_updates_portfolio(self):
        # Arrange
        state = AccountState(
            account_id=AccountId("BINANCE", "01234"),
            account_type=AccountType.CASH,
            base_currency=None,  # Multi-currency account
            reported=True,
            balances=[
                AccountBalance(
                    BTC,
                    Money(10.00000000, BTC),
                    Money(0.00000000, BTC),
                    Money(10.00000000, BTC),
                ),
                AccountBalance(
                    ETH,
                    Money(20.00000000, ETH),
                    Money(0.00000000, ETH),
                    Money(20.00000000, ETH),
                ),
            ],
            info={},
            event_id=uuid4(),
            ts_updated_ns=0,
            timestamp_ns=0,
        )

        self.exec_engine.process(state)

        order = self.order_factory.market(
            BTCUSDT_BINANCE.id,
            OrderSide.SELL,
            Quantity.from_str("0.515"),
        )

        fill = TestStubs.event_order_filled(
            order=order,
            instrument=BTCUSDT_BINANCE,
            position_id=PositionId("P-123456"),
            strategy_id=StrategyId("S-001"),
            last_px=Price.from_str("15000.00"),
        )

        last = QuoteTick(
            BTCUSDT_BINANCE.id,
            Price.from_str("15510.15"),
            Price.from_str("15510.25"),
            Quantity.from_str("12.62"),
            Quantity.from_str("3.1"),
            0,
            0,
        )

        self.cache.add_quote_tick(last)
        self.portfolio.update_tick(last)

        position = Position(instrument=BTCUSDT_BINANCE, fill=fill)

        # Act
        self.cache.add_position(position)
        self.portfolio.update_position(TestStubs.event_position_opened(position))

        # Assert
        assert self.portfolio.net_exposures(BINANCE) == {USDT: Money(7987.77875000, USDT)}
        assert self.portfolio.unrealized_pnls(BINANCE) == {USDT: Money(-262.77875000, USDT)}
        assert self.portfolio.maint_margins(BINANCE) == {USDT: Money(7.98777875, USDT)}
        assert self.portfolio.net_exposure(BTCUSDT_BINANCE.id) == Money(7987.77875000, USDT)
        assert self.portfolio.unrealized_pnl(BTCUSDT_BINANCE.id) == Money(-262.77875000, USDT)
        assert self.portfolio.net_position(order.instrument_id) == Decimal("-0.515")
        assert not self.portfolio.is_net_long(order.instrument_id)
        assert self.portfolio.is_net_short(order.instrument_id)
        assert not self.portfolio.is_flat(order.instrument_id)
        assert not self.portfolio.is_completely_flat()

    def test_opening_positions_with_multi_asset_account(self):
        # Arrange
        state = AccountState(
            account_id=AccountId("BITMEX", "01234"),
            account_type=AccountType.CASH,
            base_currency=None,  # Multi-currency account
            reported=True,
            balances=[
                AccountBalance(
                    BTC,
                    Money(10.00000000, BTC),
                    Money(0.00000000, BTC),
                    Money(10.00000000, BTC),
                ),
                AccountBalance(
                    ETH,
                    Money(20.00000000, ETH),
                    Money(0.00000000, ETH),
                    Money(20.00000000, ETH),
                ),
            ],
            info={},
            event_id=uuid4(),
            ts_updated_ns=0,
            timestamp_ns=0,
        )

        self.exec_engine.process(state)

        last_ethusd = QuoteTick(
            ETHUSD_BITMEX.id,
            Price.from_str("376.05"),
            Price.from_str("377.10"),
            Quantity.from_str("16"),
            Quantity.from_str("25"),
            0,
            0,
        )

        last_btcusd = QuoteTick(
            BTCUSD_BITMEX.id,
            Price.from_str("10500.05"),
            Price.from_str("10501.51"),
            Quantity.from_str("2.54"),
            Quantity.from_str("0.91"),
            0,
            0,
        )

        self.cache.add_quote_tick(last_ethusd)
        self.cache.add_quote_tick(last_btcusd)
        self.portfolio.update_tick(last_ethusd)
        self.portfolio.update_tick(last_btcusd)

        order = self.order_factory.market(
            ETHUSD_BITMEX.id,
            OrderSide.BUY,
            Quantity.from_int(10000),
        )

        fill = TestStubs.event_order_filled(
            order=order,
            instrument=ETHUSD_BITMEX,
            position_id=PositionId("P-123456"),
            strategy_id=StrategyId("S-001"),
            last_px=Price.from_str("376.05"),
        )

        position = Position(instrument=ETHUSD_BITMEX, fill=fill)

        # Act
        self.cache.add_position(position)
        self.portfolio.update_position(TestStubs.event_position_opened(position))

        # Assert
        assert self.portfolio.net_exposures(BITMEX) == {ETH: Money(26.59220848, ETH)}
        assert self.portfolio.maint_margins(BITMEX) == {ETH: Money(0.20608962, ETH)}
        assert self.portfolio.net_exposure(ETHUSD_BITMEX.id) == Money(26.59220848, ETH)
        assert self.portfolio.unrealized_pnl(ETHUSD_BITMEX.id) == Money(0.00000000, ETH)

    def test_unrealized_pnl_when_insufficient_data_for_xrate_returns_none(self):
        # Arrange
        state = AccountState(
            account_id=AccountId("BITMEX", "01234"),
            account_type=AccountType.MARGIN,
            base_currency=BTC,
            reported=True,
            balances=[
                AccountBalance(
                    BTC,
                    Money(10.00000000, BTC),
                    Money(0.00000000, BTC),
                    Money(10.00000000, BTC),
                ),
                AccountBalance(
                    ETH,
                    Money(20.00000000, ETH),
                    Money(0.00000000, ETH),
                    Money(20.00000000, ETH),
                ),
            ],
            info={},
            event_id=uuid4(),
            ts_updated_ns=0,
            timestamp_ns=0,
        )

        self.exec_engine.process(state)

        order = self.order_factory.market(
            ETHUSD_BITMEX.id,
            OrderSide.BUY,
            Quantity.from_int(100),
        )

        self.exec_engine.cache.add_order(order, PositionId.null())
        self.exec_engine.process(TestStubs.event_order_submitted(order))
        self.exec_engine.process(TestStubs.event_order_accepted(order))

        fill = TestStubs.event_order_filled(
            order=order,
            instrument=ETHUSD_BITMEX,
            position_id=PositionId("P-123456"),
            strategy_id=StrategyId("S-001"),
            last_px=Price.from_str("376.05"),
        )

        self.exec_engine.process(fill)

        position = Position(instrument=ETHUSD_BITMEX, fill=fill)

        self.portfolio.update_position(TestStubs.event_position_opened(position))

        # Act
        result = self.portfolio.unrealized_pnls(BITMEX)

        # # Assert
        assert result == {}

    def test_market_value_when_insufficient_data_for_xrate_returns_none(self):
        # Arrange
        state = AccountState(
            account_id=AccountId("BITMEX", "01234"),
            account_type=AccountType.MARGIN,
            base_currency=BTC,
            reported=True,
            balances=[
                AccountBalance(
                    BTC,
                    Money(10.00000000, BTC),
                    Money(0.00000000, BTC),
                    Money(10.00000000, BTC),
                ),
            ],
            info={},
            event_id=uuid4(),
            ts_updated_ns=0,
            timestamp_ns=0,
        )

        self.exec_engine.process(state)

        order = self.order_factory.market(
            ETHUSD_BITMEX.id,
            OrderSide.BUY,
            Quantity.from_int(100),
        )

        fill = TestStubs.event_order_filled(
            order=order,
            instrument=ETHUSD_BITMEX,
            position_id=PositionId("P-123456"),
            strategy_id=StrategyId("S-001"),
            last_px=Price.from_str("376.05"),
        )

        last_ethusd = QuoteTick(
            ETHUSD_BITMEX.id,
            Price.from_str("376.05"),
            Price.from_str("377.10"),
            Quantity.from_str("16"),
            Quantity.from_str("25"),
            0,
            0,
        )

        last_xbtusd = QuoteTick(
            BTCUSD_BITMEX.id,
            Price.from_str("50000.00"),
            Price.from_str("50000.00"),
            Quantity.from_str("1"),
            Quantity.from_str("1"),
            0,
            0,
        )

        position = Position(instrument=ETHUSD_BITMEX, fill=fill)

        self.portfolio.update_position(TestStubs.event_position_opened(position))
        self.cache.add_position(position)
        self.cache.add_quote_tick(last_ethusd)
        self.cache.add_quote_tick(last_xbtusd)
        self.portfolio.update_tick(last_ethusd)
        self.portfolio.update_tick(last_xbtusd)

        # Act
        result = self.portfolio.net_exposures(BITMEX)

        # Assert
        assert result == {BTC: Money(0.00200000, BTC)}

    def test_opening_several_positions_updates_portfolio(self):
        # Arrange
        state = AccountState(
            account_id=AccountId("SIM", "01234"),
            account_type=AccountType.MARGIN,
            base_currency=USD,
            reported=True,
            balances=[
                AccountBalance(
                    USD,
                    Money(1_000_000, USD),
                    Money(0, USD),
                    Money(1_000_000, USD),
                ),
            ],
            info={},
            event_id=uuid4(),
            ts_updated_ns=0,
            timestamp_ns=0,
        )

        self.exec_engine.process(state)

        last_audusd = QuoteTick(
            AUDUSD_SIM.id,
            Price.from_str("0.80501"),
            Price.from_str("0.80505"),
            Quantity.from_int(1),
            Quantity.from_int(1),
            0,
            0,
        )

        last_gbpusd = QuoteTick(
            GBPUSD_SIM.id,
            Price.from_str("1.30315"),
            Price.from_str("1.30317"),
            Quantity.from_int(1),
            Quantity.from_int(1),
            0,
            0,
        )

        self.cache.add_quote_tick(last_audusd)
        self.cache.add_quote_tick(last_gbpusd)
        self.portfolio.update_tick(last_audusd)
        self.portfolio.update_tick(last_gbpusd)

        order1 = self.order_factory.market(
            AUDUSD_SIM.id,
            OrderSide.BUY,
            Quantity.from_int(100000),
        )

        order2 = self.order_factory.market(
            GBPUSD_SIM.id,
            OrderSide.BUY,
            Quantity.from_int(100000),
        )

        self.exec_engine.cache.add_order(order1, PositionId.null())
        self.exec_engine.cache.add_order(order2, PositionId.null())

        fill1 = TestStubs.event_order_filled(
            order1,
            instrument=AUDUSD_SIM,
            position_id=PositionId("P-1"),
            strategy_id=StrategyId("S-1"),
            last_px=Price.from_str("1.00000"),
        )

        fill2 = TestStubs.event_order_filled(
            order2,
            instrument=GBPUSD_SIM,
            position_id=PositionId("P-2"),
            strategy_id=StrategyId("S-1"),
            last_px=Price.from_str("1.00000"),
        )

        self.exec_engine.cache.update_order(order1)
        self.exec_engine.cache.update_order(order2)

        position1 = Position(instrument=AUDUSD_SIM, fill=fill1)
        position2 = Position(instrument=GBPUSD_SIM, fill=fill2)
        position_opened1 = TestStubs.event_position_opened(position1)
        position_opened2 = TestStubs.event_position_opened(position2)

        # Act
        self.cache.add_position(position1)
        self.cache.add_position(position2)
        self.portfolio.update_position(position_opened1)
        self.portfolio.update_position(position_opened2)

        # Assert
        assert self.portfolio.net_exposures(SIM) == {USD: Money(210816.00, USD)}
        assert self.portfolio.unrealized_pnls(SIM) == {USD: Money(10816.00, USD)}
        assert self.portfolio.maint_margins(SIM) == {USD: Money(3912.06, USD)}
        assert self.portfolio.net_exposure(AUDUSD_SIM.id) == Money(80501.00, USD)
        assert self.portfolio.net_exposure(GBPUSD_SIM.id) == Money(130315.00, USD)
        assert self.portfolio.unrealized_pnl(AUDUSD_SIM.id) == Money(-19499.00, USD)
        assert self.portfolio.unrealized_pnl(GBPUSD_SIM.id) == Money(30315.00, USD)
        assert self.portfolio.net_position(AUDUSD_SIM.id) == Decimal(100000)
        assert self.portfolio.net_position(GBPUSD_SIM.id) == Decimal(100000)
        assert self.portfolio.is_net_long(AUDUSD_SIM.id)
        assert not self.portfolio.is_net_short(AUDUSD_SIM.id)
        assert not self.portfolio.is_flat(AUDUSD_SIM.id)
        assert not self.portfolio.is_completely_flat()

    def test_modifying_position_updates_portfolio(self):
        # Arrange
        state = AccountState(
            account_id=AccountId("SIM", "01234"),
            account_type=AccountType.MARGIN,
            base_currency=USD,
            reported=True,
            balances=[
                AccountBalance(
                    USD,
                    Money(1_000_000, USD),
                    Money(0, USD),
                    Money(1_000_000, USD),
                ),
            ],
            info={},
            event_id=uuid4(),
            ts_updated_ns=0,
            timestamp_ns=0,
        )

        self.exec_engine.process(state)

        last_audusd = QuoteTick(
            AUDUSD_SIM.id,
            Price.from_str("0.80501"),
            Price.from_str("0.80505"),
            Quantity.from_int(1),
            Quantity.from_int(1),
            0,
            0,
        )

        self.cache.add_quote_tick(last_audusd)
        self.portfolio.update_tick(last_audusd)

        order1 = self.order_factory.market(
            AUDUSD_SIM.id,
            OrderSide.BUY,
            Quantity.from_int(100000),
        )

        fill1 = TestStubs.event_order_filled(
            order1,
            instrument=AUDUSD_SIM,
            position_id=PositionId("P-123456"),
            strategy_id=StrategyId("S-1"),
            last_px=Price.from_str("1.00000"),
        )

        position = Position(instrument=AUDUSD_SIM, fill=fill1)
        self.exec_engine.cache.add_position(position)
        self.portfolio.update_position(TestStubs.event_position_opened(position))

        order2 = self.order_factory.market(
            AUDUSD_SIM.id,
            OrderSide.SELL,
            Quantity.from_int(50000),
        )

        order2_filled = TestStubs.event_order_filled(
            order2,
            instrument=AUDUSD_SIM,
            position_id=PositionId("P-123456"),
            strategy_id=StrategyId("S-1"),
            last_px=Price.from_str("1.00000"),
        )

        position.apply(order2_filled)

        # Act
        self.portfolio.update_position(TestStubs.event_position_changed(position))

        # Assert
        assert self.portfolio.net_exposures(SIM) == {USD: Money(40250.50, USD)}
        assert self.portfolio.unrealized_pnls(SIM) == {USD: Money(-9749.50, USD)}
        assert self.portfolio.maint_margins(SIM) == {USD: Money(1208.32, USD)}
        assert self.portfolio.net_exposure(AUDUSD_SIM.id) == Money(40250.50, USD)
        assert self.portfolio.unrealized_pnl(AUDUSD_SIM.id) == Money(-9749.50, USD)
        assert self.portfolio.net_position(AUDUSD_SIM.id) == Decimal(50000)
        assert self.portfolio.is_net_long(AUDUSD_SIM.id)
        assert not self.portfolio.is_net_short(AUDUSD_SIM.id)
        assert not self.portfolio.is_flat(AUDUSD_SIM.id)
        assert not self.portfolio.is_completely_flat()
        assert self.portfolio.unrealized_pnls(BINANCE) == {}
        assert self.portfolio.net_exposures(BINANCE) is None

    def test_closing_position_updates_portfolio(self):
        # Arrange
        state = AccountState(
            account_id=AccountId("SIM", "01234"),
            account_type=AccountType.MARGIN,
            base_currency=USD,
            reported=True,
            balances=[
                AccountBalance(
                    USD,
                    Money(1_000_000, USD),
                    Money(0, USD),
                    Money(1_000_000, USD),
                ),
            ],
            info={},
            event_id=uuid4(),
            ts_updated_ns=0,
            timestamp_ns=0,
        )

        self.exec_engine.process(state)

        order1 = self.order_factory.market(
            AUDUSD_SIM.id,
            OrderSide.BUY,
            Quantity.from_int(100000),
        )

        fill1 = TestStubs.event_order_filled(
            order1,
            instrument=AUDUSD_SIM,
            position_id=PositionId("P-123456"),
            strategy_id=StrategyId("S-1"),
            last_px=Price.from_str("1.00000"),
        )

        position = Position(instrument=AUDUSD_SIM, fill=fill1)
        self.exec_engine.cache.add_position(position)
        self.portfolio.update_position(TestStubs.event_position_opened(position))

        order2 = self.order_factory.market(
            AUDUSD_SIM.id,
            OrderSide.SELL,
            Quantity.from_int(100000),
        )

        order2_filled = TestStubs.event_order_filled(
            order2,
            instrument=AUDUSD_SIM,
            position_id=PositionId("P-123456"),
            strategy_id=StrategyId("S-1"),
            last_px=Price.from_str("1.00010"),
        )

        position.apply(order2_filled)
        self.exec_engine.cache.update_position(position)

        # Act
        self.portfolio.update_position(TestStubs.event_position_closed(position))

        # Assert
        assert self.portfolio.net_exposures(SIM) == {}
        assert self.portfolio.unrealized_pnls(SIM) == {}
        assert self.portfolio.maint_margins(SIM) == {}
        assert self.portfolio.net_exposure(AUDUSD_SIM.id) == Money(0, USD)
        assert self.portfolio.unrealized_pnl(AUDUSD_SIM.id) == Money(0, USD)
        assert self.portfolio.net_position(AUDUSD_SIM.id) == Decimal(0)
        assert not self.portfolio.is_net_long(AUDUSD_SIM.id)
        assert not self.portfolio.is_net_short(AUDUSD_SIM.id)
        assert self.portfolio.is_flat(AUDUSD_SIM.id)
        assert self.portfolio.is_completely_flat()

    def test_several_positions_with_different_instruments_updates_portfolio(self):
        # Arrange
        state = AccountState(
            account_id=AccountId("SIM", "01234"),
            account_type=AccountType.MARGIN,
            base_currency=USD,
            reported=True,
            balances=[
                AccountBalance(
                    USD,
                    Money(1_000_000, USD),
                    Money(0, USD),
                    Money(1_000_000, USD),
                ),
            ],
            info={},
            event_id=uuid4(),
            ts_updated_ns=0,
            timestamp_ns=0,
        )

        self.exec_engine.process(state)

        order1 = self.order_factory.market(
            AUDUSD_SIM.id,
            OrderSide.BUY,
            Quantity.from_int(100000),
        )

        order2 = self.order_factory.market(
            AUDUSD_SIM.id,
            OrderSide.BUY,
            Quantity.from_int(100000),
        )

        order3 = self.order_factory.market(
            GBPUSD_SIM.id,
            OrderSide.BUY,
            Quantity.from_int(100000),
        )

        order4 = self.order_factory.market(
            GBPUSD_SIM.id,
            OrderSide.SELL,
            Quantity.from_int(100000),
        )

        fill1 = TestStubs.event_order_filled(
            order1,
            instrument=AUDUSD_SIM,
            position_id=PositionId("P-1"),
            strategy_id=StrategyId("S-1"),
            last_px=Price.from_str("1.00000"),
        )

        fill2 = TestStubs.event_order_filled(
            order2,
            instrument=AUDUSD_SIM,
            position_id=PositionId("P-2"),
            strategy_id=StrategyId("S-1"),
            last_px=Price.from_str("1.00000"),
        )

        fill3 = TestStubs.event_order_filled(
            order3,
            instrument=GBPUSD_SIM,
            position_id=PositionId("P-3"),
            strategy_id=StrategyId("S-1"),
            last_px=Price.from_str("1.00000"),
        )

        fill4 = TestStubs.event_order_filled(
            order4,
            instrument=GBPUSD_SIM,
            position_id=PositionId("P-3"),
            strategy_id=StrategyId("S-1"),
            last_px=Price.from_str("1.00100"),
        )

        position1 = Position(instrument=AUDUSD_SIM, fill=fill1)
        position2 = Position(instrument=AUDUSD_SIM, fill=fill2)
        position3 = Position(instrument=GBPUSD_SIM, fill=fill3)

        last_audusd = QuoteTick(
            AUDUSD_SIM.id,
            Price.from_str("0.80501"),
            Price.from_str("0.80505"),
            Quantity.from_int(1),
            Quantity.from_int(1),
            0,
            0,
        )

        last_gbpusd = QuoteTick(
            GBPUSD_SIM.id,
            Price.from_str("1.30315"),
            Price.from_str("1.30317"),
            Quantity.from_int(1),
            Quantity.from_int(1),
            0,
            0,
        )

        self.cache.add_quote_tick(last_audusd)
        self.cache.add_quote_tick(last_gbpusd)
        self.portfolio.update_tick(last_audusd)
        self.portfolio.update_tick(last_gbpusd)

        self.cache.add_position(position1)
        self.cache.add_position(position2)
        self.cache.add_position(position3)

        # Act
        self.portfolio.update_position(TestStubs.event_position_opened(position1))
        self.portfolio.update_position(TestStubs.event_position_opened(position2))
        self.portfolio.update_position(TestStubs.event_position_opened(position3))

        position3.apply(fill4)
        self.cache.update_position(position3)
        self.portfolio.update_position(TestStubs.event_position_closed(position3))

        # Assert
        assert {USD: Money(-38998.00, USD)} == self.portfolio.unrealized_pnls(SIM)
        assert {USD: Money(161002.00, USD)} == self.portfolio.net_exposures(SIM)
        assert self.portfolio.maint_margins(SIM) == {USD: Money(3912.06, USD)}
        assert Money(161002.00, USD) == self.portfolio.net_exposure(AUDUSD_SIM.id)
        assert Money(-38998.00, USD) == self.portfolio.unrealized_pnl(AUDUSD_SIM.id)
        assert self.portfolio.unrealized_pnl(GBPUSD_SIM.id) == Money(0, USD)
        assert self.portfolio.net_position(AUDUSD_SIM.id) == Decimal(200000)
        assert self.portfolio.net_position(GBPUSD_SIM.id) == Decimal(0)
        assert self.portfolio.is_net_long(AUDUSD_SIM.id)
        assert self.portfolio.is_flat(GBPUSD_SIM.id)
        assert not self.portfolio.is_completely_flat()
