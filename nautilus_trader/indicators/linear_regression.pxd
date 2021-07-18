from nautilus_trader.indicators.base.indicator cimport Indicator


cdef class LinearRegression(Indicator):
    cdef object _inputs

    cdef readonly int period
    """The window period.\n\n:returns: `int`"""
    cdef readonly double value
    """The current value.\n\n:returns: `double`"""

    cpdef void update_raw(self, double close_price) except *
