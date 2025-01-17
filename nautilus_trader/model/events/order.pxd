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

from libc.stdint cimport int64_t

from nautilus_trader.core.message cimport Event
from nautilus_trader.model.c_enums.liquidity_side cimport LiquiditySide
from nautilus_trader.model.c_enums.order_side cimport OrderSide
from nautilus_trader.model.c_enums.order_type cimport OrderType
from nautilus_trader.model.c_enums.time_in_force cimport TimeInForce
from nautilus_trader.model.currency cimport Currency
from nautilus_trader.model.identifiers cimport AccountId
from nautilus_trader.model.identifiers cimport ClientOrderId
from nautilus_trader.model.identifiers cimport ExecutionId
from nautilus_trader.model.identifiers cimport InstrumentId
from nautilus_trader.model.identifiers cimport PositionId
from nautilus_trader.model.identifiers cimport StrategyId
from nautilus_trader.model.identifiers cimport TraderId
from nautilus_trader.model.identifiers cimport VenueOrderId
from nautilus_trader.model.objects cimport Money
from nautilus_trader.model.objects cimport Price
from nautilus_trader.model.objects cimport Quantity


cdef class OrderEvent(Event):
    cdef readonly TraderId trader_id
    """The trader ID associated with the event.\n\n:returns: `TraderId`"""
    cdef readonly StrategyId strategy_id
    """The strategy ID associated with the event.\n\n:returns: `StrategyId`"""
    cdef readonly InstrumentId instrument_id
    """The instrument ID associated with the event.\n\n:returns: `InstrumentId`"""
    cdef readonly ClientOrderId client_order_id
    """The client order ID associated with the event.\n\n:returns: `ClientOrderId`"""
    cdef readonly VenueOrderId venue_order_id
    """The venue order ID associated with the event.\n\n:returns: `VenueOrderId`"""


cdef class OrderInitialized(OrderEvent):
    cdef readonly OrderSide side
    """The order side.\n\n:returns: `OrderSide`"""
    cdef readonly OrderType type
    """The order type.\n\n:returns: `OrderType`"""
    cdef readonly Quantity quantity
    """The order quantity.\n\n:returns: `Quantity`"""
    cdef readonly TimeInForce time_in_force
    """The order time-in-force.\n\n:returns: `TimeInForce`"""
    cdef readonly dict options
    """The order initialization options.\n\n:returns: `dict`"""

    @staticmethod
    cdef OrderInitialized from_dict_c(dict values)

    @staticmethod
    cdef dict to_dict_c(OrderInitialized obj)


cdef class OrderDenied(OrderEvent):
    cdef readonly str reason
    """The reason the order was denied.\n\n:returns: `str`"""

    @staticmethod
    cdef OrderDenied from_dict_c(dict values)

    @staticmethod
    cdef dict to_dict_c(OrderDenied obj)


cdef class OrderSubmitted(OrderEvent):
    cdef readonly AccountId account_id
    """The account ID associated with the event.\n\n:returns: `AccountId`"""
    cdef readonly int64_t ts_submitted_ns
    """The order submitted time.\n\n:returns: `int64`"""

    @staticmethod
    cdef OrderSubmitted from_dict_c(dict values)

    @staticmethod
    cdef dict to_dict_c(OrderSubmitted obj)


cdef class OrderAccepted(OrderEvent):
    cdef readonly AccountId account_id
    """The account ID associated with the event.\n\n:returns: `AccountId`"""
    cdef readonly int64_t ts_accepted_ns
    """The UNIX timestamp (nanoseconds) when the order was accepted.\n\n:returns: `int64`"""

    @staticmethod
    cdef OrderAccepted from_dict_c(dict values)

    @staticmethod
    cdef dict to_dict_c(OrderAccepted obj)


cdef class OrderRejected(OrderEvent):
    cdef readonly AccountId account_id
    """The account ID associated with the event.\n\n:returns: `AccountId`"""
    cdef readonly str reason
    """The reason the order was rejected.\n\n:returns: `str`"""
    cdef readonly int64_t ts_rejected_ns
    """The UNIX timestamp (nanoseconds) when the order was rejected.\n\n:returns: `int64`"""

    @staticmethod
    cdef OrderRejected from_dict_c(dict values)

    @staticmethod
    cdef dict to_dict_c(OrderRejected obj)


cdef class OrderCanceled(OrderEvent):
    cdef readonly AccountId account_id
    """The account ID associated with the event.\n\n:returns: `AccountId`"""
    cdef readonly int64_t ts_canceled_ns
    """The UNIX timestamp (nanoseconds) when the order was canceled.\n\n:returns: `int64`"""

    @staticmethod
    cdef OrderCanceled from_dict_c(dict values)

    @staticmethod
    cdef dict to_dict_c(OrderCanceled obj)


cdef class OrderExpired(OrderEvent):
    cdef readonly AccountId account_id
    """The account ID associated with the event.\n\n:returns: `AccountId`"""
    cdef readonly int64_t ts_expired_ns
    """The UNIX timestamp (nanoseconds) when the order expired.\n\n:returns: `int64`"""

    @staticmethod
    cdef OrderExpired from_dict_c(dict values)

    @staticmethod
    cdef dict to_dict_c(OrderExpired obj)


cdef class OrderTriggered(OrderEvent):
    cdef readonly AccountId account_id
    """The account ID associated with the event.\n\n:returns: `AccountId`"""
    cdef readonly int64_t ts_triggered_ns
    """The UNIX timestamp (nanoseconds) when the order was triggered.\n\n:returns: `int64`"""

    @staticmethod
    cdef OrderTriggered from_dict_c(dict values)

    @staticmethod
    cdef dict to_dict_c(OrderTriggered obj)


cdef class OrderPendingUpdate(OrderEvent):
    cdef readonly AccountId account_id
    """The account ID associated with the event.\n\n:returns: `AccountId`"""
    cdef readonly int64_t ts_pending_ns
    """The timestamp from which the replace was pending.\n\n:returns: `int64`"""

    @staticmethod
    cdef OrderPendingUpdate from_dict_c(dict values)

    @staticmethod
    cdef dict to_dict_c(OrderPendingUpdate obj)


cdef class OrderPendingCancel(OrderEvent):
    cdef readonly AccountId account_id
    """The account ID associated with the event.\n\n:returns: `AccountId`"""
    cdef readonly int64_t ts_pending_ns
    """The timestamp from which the cancel was pending.\n\n:returns: `int64`"""

    @staticmethod
    cdef OrderPendingCancel from_dict_c(dict values)

    @staticmethod
    cdef dict to_dict_c(OrderPendingCancel obj)


cdef class OrderUpdateRejected(OrderEvent):
    cdef readonly AccountId account_id
    """The account ID associated with the event.\n\n:returns: `AccountId`"""
    cdef readonly str response_to
    """The update rejection response to.\n\n:returns: `str`"""
    cdef readonly str reason
    """The reason for order update rejection.\n\n:returns: `str`"""
    cdef readonly int64_t ts_rejected_ns
    """The UNIX timestamp (nanoseconds) when the update was rejected.\n\n:returns: `int64`"""

    @staticmethod
    cdef OrderUpdateRejected from_dict_c(dict values)

    @staticmethod
    cdef dict to_dict_c(OrderUpdateRejected obj)


cdef class OrderCancelRejected(OrderEvent):
    cdef readonly AccountId account_id
    """The account ID associated with the event.\n\n:returns: `AccountId`"""
    cdef readonly str response_to
    """The cancel rejection response to.\n\n:returns: `str`"""
    cdef readonly str reason
    """The reason for order cancel rejection.\n\n:returns: `str`"""
    cdef readonly int64_t ts_rejected_ns
    """The UNIX timestamp (nanoseconds) when the cancel was rejected.\n\n:returns: `int64`"""

    @staticmethod
    cdef OrderCancelRejected from_dict_c(dict values)

    @staticmethod
    cdef dict to_dict_c(OrderCancelRejected obj)


cdef class OrderUpdated(OrderEvent):
    cdef readonly AccountId account_id
    """The account ID associated with the event.\n\n:returns: `AccountId`"""
    cdef readonly Quantity quantity
    """The orders current quantity.\n\n:returns: `Quantity`"""
    cdef readonly Price price
    """The orders current price.\n\n:returns: `Price`"""
    cdef readonly Price trigger
    """The orders current price.\n\n:returns: `Price` or None"""
    cdef readonly int64_t ts_updated_ns
    """The UNIX timestamp (nanoseconds) when the order was updated.\n\n:returns: `int64`"""

    @staticmethod
    cdef OrderUpdated from_dict_c(dict values)

    @staticmethod
    cdef dict to_dict_c(OrderUpdated obj)


cdef class OrderFilled(OrderEvent):
    cdef readonly AccountId account_id
    """The account ID associated with the event.\n\n:returns: `AccountId`"""
    cdef readonly ExecutionId execution_id
    """The execution ID associated with the event.\n\n:returns: `ExecutionId`"""
    cdef readonly PositionId position_id
    """The position ID associated with the event.\n\n:returns: `PositionId`"""
    cdef readonly OrderSide side
    """The order side.\n\n:returns: `OrderSide`"""
    cdef readonly OrderType type
    """The order type.\n\n:returns: `OrderType`"""
    cdef readonly Quantity last_qty
    """The fill quantity.\n\n:returns: `Quantity`"""
    cdef readonly Price last_px
    """The fill price for this execution.\n\n:returns: `Price`"""
    cdef readonly Currency currency
    """The currency of the price.\n\n:returns: `Currency`"""
    cdef readonly Money commission
    """The commission generated from the fill.\n\n:returns: `Money`"""
    cdef readonly LiquiditySide liquidity_side
    """The liquidity side of the event (MAKER or TAKER).\n\n:returns: `LiquiditySide`"""
    cdef readonly int64_t ts_filled_ns
    """The UNIX timestamp (nanoseconds) when the order was filled.\n\n:returns: `int64`"""
    cdef readonly dict info
    """The additional fill information.\n\n:returns: `dict[str, object]`"""

    @staticmethod
    cdef OrderFilled from_dict_c(dict values)

    @staticmethod
    cdef dict to_dict_c(OrderFilled obj)
    cdef bint is_buy_c(self) except *
    cdef bint is_sell_c(self) except *
