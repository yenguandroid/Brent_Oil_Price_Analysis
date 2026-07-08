import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from data_loader import load_brent_prices, load_events, add_log_returns  # noqa: E402
from eda import (  # noqa: E402
    run_adf_test,
    run_kpss_test,
    summarize_stationarity,
    rolling_volatility,
    basic_descriptive_stats,
)


@pytest.fixture(scope="module")
def prices():
    return load_brent_prices()


@pytest.fixture(scope="module")
def prices_with_returns(prices):
    return add_log_returns(prices)


def test_load_brent_prices_shape_and_types(prices):
    assert not prices.empty
    assert "Price" in prices.columns
    assert pd.api.types.is_float_dtype(prices["Price"])
    assert isinstance(prices.index, pd.DatetimeIndex)


def test_load_brent_prices_no_duplicate_dates(prices):
    assert prices.index.duplicated().sum() == 0


def test_load_brent_prices_sorted_ascending(prices):
    assert prices.index.is_monotonic_increasing


def test_add_log_returns_columns(prices_with_returns):
    assert "log_price" in prices_with_returns.columns
    assert "log_return" in prices_with_returns.columns
    # first log return should be NaN (nothing to diff against)
    assert np.isnan(prices_with_returns["log_return"].iloc[0])


def test_load_events_minimum_count():
    events = load_events()
    assert len(events) >= 10
    expected_cols = {"event_id", "start_date", "event_name", "category", "region",
                      "description", "expected_direction"}
    assert expected_cols.issubset(set(events.columns))


def test_load_events_dates_parsed():
    events = load_events()
    assert pd.api.types.is_datetime64_any_dtype(events["start_date"])
    assert events["start_date"].notna().all()


def test_run_adf_test_returns_result(prices_with_returns):
    result = run_adf_test(prices_with_returns["log_return"])
    assert result.test_name == "ADF"
    assert isinstance(result.p_value, float)


def test_run_kpss_test_returns_result(prices_with_returns):
    result = run_kpss_test(prices_with_returns["log_return"])
    assert result.test_name == "KPSS"
    assert isinstance(result.p_value, float)


def test_log_returns_are_more_stationary_than_price(prices_with_returns):
    """Sanity check the core EDA finding: ADF should reject the unit-root
    null far more strongly (more negative statistic) for log returns than
    for the raw price level."""
    adf_price = run_adf_test(prices_with_returns["Price"])
    adf_return = run_adf_test(prices_with_returns["log_return"])
    assert adf_return.statistic < adf_price.statistic


def test_summarize_stationarity_shape(prices_with_returns):
    table = summarize_stationarity(prices_with_returns["Price"], prices_with_returns["log_return"])
    assert len(table) == 2
    assert "ADF conclusion" in table.columns


def test_rolling_volatility_length(prices_with_returns):
    vol = rolling_volatility(prices_with_returns["log_return"], window=30)
    assert len(vol) == len(prices_with_returns)


def test_basic_descriptive_stats_has_skew_kurtosis(prices_with_returns):
    stats = basic_descriptive_stats(prices_with_returns["log_return"])
    assert "skew" in stats.index
    assert "kurtosis" in stats.index
