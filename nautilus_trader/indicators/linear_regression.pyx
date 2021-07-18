from collections import deque
from statistics import mean

import numpy as np
cimport numpy as np

from nautilus_trader.core.correctness cimport Condition
from nautilus_trader.indicators.base.indicator cimport Indicator
from nautilus_trader.model.data.bar cimport Bar


cdef class LinearRegression(Indicator):
    """
    An indicator that calculates a simple linear regression.
    """

    def __init__(self, int period=0):
        """
        Initialize a new instance of the ``LinearRegression`` class.

        Parameters
        ----------
        period : int
            The period for the indicator.

        Raises
        ------
        ValueError
            If period is not greater than zero.

        """
        Condition.positive_int(period, "period")
        super().__init__(params=[period])

        self.period = period
        self._inputs = deque(maxlen=self.period)
        self.value = 0

    cpdef void handle_bar(self, Bar bar) except *:
        """
        Update the indicator with the given bar.

        Parameters
        ----------
        bar : Bar
            The update bar.

        """
        Condition.not_none(bar, "bar")

        self.update_raw(bar.close.as_double())

    cpdef void update_raw(self, double close_price) except *:
        """
        Update the indicator with the given raw values.

        Parameters
        ----------
        close_price : double
            The close price.

        """
        self._inputs.append(close_price)

        # Warmup indicator logic
        if not self.initialized:
            self._set_has_inputs(True)
            if len(self._inputs) >= self.period:
                self._set_initialized(True)
            else:
                return

        x_arr = np.arange(self.period)
        slope = ((mean(x_arr) * mean(self._inputs)) - mean(x_arr * self._inputs)) / ((mean(x_arr) * mean(x_arr)) - mean(x_arr * x_arr))
        intercept = mean(self._inputs) - slope * mean(x_arr)

        regression_line = []
        for x in x_arr:
            regression_line.append((slope * x) + intercept)

        self.value = regression_line[-1]

    cdef void _reset(self) except *:
        self._inputs.clear()
        self.value = 0
