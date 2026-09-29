"""Time-series model specification factory."""

from collections.abc import Sequence

from statsmodels.tsa.arima.model import ARIMA


def create_arima_model(
    values: Sequence[float], order: tuple[int, int, int] = (1, 1, 1)
) -> ARIMA:
    """Create an unfitted ARIMA model specification.

    No model fitting or forecasting is performed by this factory.
    """
    return ARIMA(values, order=order)