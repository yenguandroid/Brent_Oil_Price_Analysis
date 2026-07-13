"""
change_point.py

Reusable Bayesian change point modeling utilities built on PyMC.

Two model families are provided:
  - fit_mean_changepoint: single change point in the MEAN of a series
    (shared variance before/after). Used for detecting shifts in the
    average price level or average return.
  - fit_mean_and_vol_changepoint: single change point in BOTH the mean
    and the volatility (sigma) of a series. Used for detecting regime
    shifts in volatility (e.g. around acute shocks like COVID-19).

Both return a small, serializable result object rather than raw traces,
so results are easy to tabulate and compare across multiple fitted windows.
"""
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import pymc as pm
import arviz as az


@dataclass
class ChangePointResult:
    trace: object
    tau_index_samples: np.ndarray
    dates: pd.DatetimeIndex
    before_label: str
    after_label: str

    @property
    def tau_map_index(self) -> int:
        """Posterior mode of tau (most probable single index)."""
        values, counts = np.unique(self.tau_index_samples, return_counts=True)
        return int(values[np.argmax(counts)])

    @property
    def tau_date(self) -> pd.Timestamp:
        return self.dates[min(self.tau_map_index, len(self.dates) - 1)]

    @property
    def tau_credible_interval(self) -> tuple:
        lo, hi = np.percentile(self.tau_index_samples, [5.5, 94.5])
        lo_i, hi_i = int(round(lo)), int(round(hi))
        lo_i = min(max(lo_i, 0), len(self.dates) - 1)
        hi_i = min(max(hi_i, 0), len(self.dates) - 1)
        return self.dates[lo_i], self.dates[hi_i]

    def summary(self, var_names=None) -> pd.DataFrame:
        return az.summary(self.trace, var_names=var_names)


def fit_mean_changepoint(
    values: np.ndarray,
    dates: pd.DatetimeIndex,
    draws: int = 1500,
    tune: int = 1000,
    chains: int = 4,
    cores: int = 1,
    target_accept: float = 0.9,
    random_seed: int = 42,
    progressbar: bool = True,
) -> ChangePointResult:
    """
    Fit a single change point model where only the MEAN shifts:
        tau  ~ DiscreteUniform(0, n-1)
        mu1  ~ Normal(mean(values), 2*std(values))
        mu2  ~ Normal(mean(values), 2*std(values))
        sigma ~ HalfNormal(std(values))   [shared before/after]
        mu = switch(tau >= t, mu1, mu2)
        obs ~ Normal(mu, sigma)

    `values` should already be whatever series you want to model
    (raw price levels, or log returns) — the function is agnostic.
    """
    values = np.asarray(values, dtype=float)
    n = len(values)
    idx = np.arange(n)
    data_mean, data_std = values.mean(), values.std()

    with pm.Model() as model:
        tau = pm.DiscreteUniform("tau", lower=0, upper=n - 1)
        mu1 = pm.Normal("mu1", mu=data_mean, sigma=2 * data_std)
        mu2 = pm.Normal("mu2", mu=data_mean, sigma=2 * data_std)
        sigma = pm.HalfNormal("sigma", sigma=data_std)
        mu = pm.math.switch(tau >= idx, mu1, mu2)
        pm.Normal("obs", mu=mu, sigma=sigma, observed=values)
        trace = pm.sample(
            draws=draws, tune=tune, chains=chains, cores=cores,
            target_accept=target_accept, random_seed=random_seed,
            progressbar=progressbar,
        )

    tau_samples = trace.posterior["tau"].values.flatten()
    return ChangePointResult(
        trace=trace, tau_index_samples=tau_samples, dates=dates,
        before_label="mu1", after_label="mu2",
    )


def fit_mean_and_vol_changepoint(
    values: np.ndarray,
    dates: pd.DatetimeIndex,
    draws: int = 1500,
    tune: int = 1000,
    chains: int = 4,
    cores: int = 1,
    target_accept: float = 0.95,
    random_seed: int = 42,
      progressbar: bool = True,
) -> ChangePointResult:
    """
    Fit a single change point model where BOTH the mean and the volatility
    (sigma) shift at tau:
        tau ~ DiscreteUniform(0, n-1)
        mu1, mu2 ~ Normal(mean(values), 2*std(values))
        sigma1, sigma2 ~ HalfNormal(std(values))
        mu = switch(tau >= t, mu1, mu2)
        sigma = switch(tau >= t, sigma1, sigma2)
        obs ~ Normal(mu, sigma)

    Intended for log-return series, to detect volatility regime shifts
    (e.g. a jump from calm to turbulent trading around a shock event).
    """
    values = np.asarray(values, dtype=float)
    n = len(values)
    idx = np.arange(n)
    data_mean, data_std = values.mean(), values.std()

    with pm.Model() as model:
        tau = pm.DiscreteUniform("tau", lower=0, upper=n - 1)
        mu1 = pm.Normal("mu1", mu=data_mean, sigma=2 * data_std)
        mu2 = pm.Normal("mu2", mu=data_mean, sigma=2 * data_std)
        sigma1 = pm.HalfNormal("sigma1", sigma=data_std)
        sigma2 = pm.HalfNormal("sigma2", sigma=data_std)
        mu = pm.math.switch(tau >= idx, mu1, mu2)
        sigma = pm.math.switch(tau >= idx, sigma1, sigma2)
        pm.Normal("obs", mu=mu, sigma=sigma, observed=values)
        trace = pm.sample(
            draws=draws, tune=tune, chains=chains, cores=cores,
            target_accept=target_accept, random_seed=random_seed,
            progressbar=progressbar,
        )

    tau_samples = trace.posterior["tau"].values.flatten()
    return ChangePointResult(
        trace=trace, tau_index_samples=tau_samples, dates=dates,
        before_label="mu1/sigma1", after_label="mu2/sigma2",
    )


def nearest_events(tau_date: pd.Timestamp, events: pd.DataFrame, window_days: int = 400) -> pd.DataFrame:
    """
    Return events from the compiled event log within `window_days` of a
    detected change point date, sorted by proximity (closest first).
    """
    events = events.copy()
    events["days_from_changepoint"] = (events["start_date"] - tau_date).dt.days
    close = events[events["days_from_changepoint"].abs() <= window_days].copy()
    close["abs_days"] = close["days_from_changepoint"].abs()
    return close.sort_values("abs_days").drop(columns="abs_days")


def pct_change(before: float, after: float) -> float:
    """Percentage change from `before` to `after`."""
    return (after - before) / before * 100.0
