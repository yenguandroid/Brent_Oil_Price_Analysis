"""
eda.py

Reusable analysis functions for Task 1 exploratory data analysis:
trend inspection, stationarity testing, and volatility diagnostics
for the Brent oil price series.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller, kpss


@dataclass
class StationarityResult:
    test_name: str
    statistic: float
    p_value: float
    is_stationary: bool
    critical_values: dict


def run_adf_test(series: pd.Series, significance: float = 0.05) -> StationarityResult:
    """
    Augmented Dickey-Fuller test.
    Null hypothesis: the series has a unit root (is non-stationary).
    """
    series = series.dropna()
    stat, p_value, _, _, crit_vals, _ = adfuller(series, autolag="AIC")
    return StationarityResult(
        test_name="ADF",
        statistic=stat,
        p_value=p_value,
        is_stationary=p_value < significance,
        critical_values=crit_vals,
    )


def run_kpss_test(series: pd.Series, significance: float = 0.05, regression: str = "c") -> StationarityResult:
    """
    KPSS test.
    Null hypothesis: the series IS stationary (opposite of ADF).
    """
    series = series.dropna()
    stat, p_value, _, crit_vals = kpss(series, regression=regression, nlags="auto")
    return StationarityResult(
        test_name="KPSS",
        statistic=stat,
        p_value=p_value,
        is_stationary=p_value > significance,
        critical_values=crit_vals,
    )


def summarize_stationarity(price: pd.Series, log_return: pd.Series) -> pd.DataFrame:
    """
    Run ADF and KPSS on both the raw price level and the log-return series
    and return a tidy comparison table.
    """
    rows = []
    for label, series in [("Price level", price), ("Log return", log_return)]:
        adf = run_adf_test(series)
        kp = run_kpss_test(series)
        rows.append({
            "series": label,
            "ADF statistic": round(adf.statistic, 4),
            "ADF p-value": round(adf.p_value, 4),
            "ADF conclusion": "Stationary" if adf.is_stationary else "Non-stationary",
            "KPSS statistic": round(kp.statistic, 4),
            "KPSS p-value": round(kp.p_value, 4),
            "KPSS conclusion": "Stationary" if kp.is_stationary else "Non-stationary",
        })
    return pd.DataFrame(rows)


def rolling_volatility(log_return: pd.Series, window: int = 30) -> pd.Series:
    """
    Rolling standard deviation of log returns, annualized-agnostic
    (raw daily volatility), used to visualize volatility clustering.
    """
    return log_return.rolling(window=window).std()


def basic_descriptive_stats(series: pd.Series) -> pd.Series:
    """
    Standard descriptive statistics plus skewness and kurtosis,
    useful for spotting fat tails typical of financial return series.
    """
    s = series.dropna()
    stats = s.describe()
    stats["skew"] = s.skew()
    stats["kurtosis"] = s.kurtosis()
    return stats


def year_over_year_trend(price: pd.Series) -> pd.Series:
    """
    Annual mean price, a simple lens on long-run trend/regimes.
    """
    return price.resample("YE").mean()
