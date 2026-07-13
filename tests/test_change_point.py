import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from change_point import (  # noqa: E402
    fit_mean_changepoint,
    fit_mean_and_vol_changepoint,
    nearest_events,
    pct_change,
)


@pytest.fixture(scope="module")
def synthetic_series():
    """
    A short synthetic series with an obvious, engineered mean shift at
    index 40 out of 80, so a change point model should recover it easily
    and quickly (small n keeps this test fast for CI).
    """
    rng = np.random.default_rng(0)
    before = rng.normal(loc=10, scale=1, size=40)
    after = rng.normal(loc=20, scale=1, size=40)
    values = np.concatenate([before, after])
    dates = pd.date_range("2020-01-01", periods=80, freq="D")
    return values, dates


def test_fit_mean_changepoint_recovers_known_break(synthetic_series):
    values, dates = synthetic_series
    result = fit_mean_changepoint(
        values, dates, draws=300, tune=300, chains=2, cores=1, random_seed=0
    )
    # true break is at index 40; allow a small tolerance
    assert abs(result.tau_map_index - 40) <= 5

    mu1 = result.trace.posterior["mu1"].values.flatten().mean()
    mu2 = result.trace.posterior["mu2"].values.flatten().mean()
    assert mu1 < mu2
    assert 8 < mu1 < 12
    assert 18 < mu2 < 22


def test_tau_credible_interval_is_ordered(synthetic_series):
    values, dates = synthetic_series
    result = fit_mean_changepoint(
        values, dates, draws=300, tune=300, chains=2, cores=1, random_seed=0
    )
    lo, hi = result.tau_credible_interval
    assert lo <= result.tau_date <= hi


def test_fit_mean_and_vol_changepoint_recovers_vol_shift():
    rng = np.random.default_rng(1)
    calm = rng.normal(loc=0, scale=0.01, size=40)
    volatile = rng.normal(loc=0, scale=0.10, size=40)
    values = np.concatenate([calm, volatile])
    dates = pd.date_range("2020-01-01", periods=80, freq="D")

    result = fit_mean_and_vol_changepoint(
        values, dates, draws=300, tune=300, chains=2, cores=1, random_seed=1
    )
    sigma1 = result.trace.posterior["sigma1"].values.flatten().mean()
    sigma2 = result.trace.posterior["sigma2"].values.flatten().mean()
    assert sigma1 < sigma2


def test_nearest_events_filters_by_window():
    events = pd.DataFrame({
        "start_date": pd.to_datetime(["2020-01-01", "2020-06-01", "2021-01-01"]),
        "event_name": ["near", "far", "very_far"],
    })
    tau_date = pd.Timestamp("2020-01-10")
    close = nearest_events(tau_date, events, window_days=30)
    assert list(close["event_name"]) == ["near"]


def test_pct_change_basic():
    assert pct_change(100, 150) == pytest.approx(50.0)
    assert pct_change(100, 50) == pytest.approx(-50.0)
