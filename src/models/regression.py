"""Regression estimator factory."""

from sklearn.linear_model import LinearRegression


def create_linear_regression() -> LinearRegression:
    """Create an unfitted linear regression estimator."""
    return LinearRegression()