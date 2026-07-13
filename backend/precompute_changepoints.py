"""
precompute_changepoints.py

Runs the exact same Bayesian change point models used in
notebooks/task2_change_point_modeling.ipynb and serializes the results
(dates, before/after values, % change, convergence diagnostics) to
backend/data/changepoints.json.

This is a deliberate design choice: PyMC/MCMC sampling takes tens of
seconds to a couple of minutes, which is unacceptable for a live web
request. Run this script once (or whenever the underlying analysis
changes) and let Flask simply serve the resulting static JSON.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from data_loader import load_brent_prices, load_events, add_log_returns  # noqa: E402
from change_point import (  # noqa: E402
    fit_mean_changepoint,
    fit_mean_and_vol_changepoint,
    nearest_events,
    pct_change,
)

RNG_SEED = 42
OUT_PATH = Path(__file__).resolve().parent / "data" / "changepoints.json"


def summarize_mean_result(name, result, events, window_days=800):
    mu1 = result.trace.posterior["mu1"].values.flatten()
    mu2 = result.trace.posterior["mu2"].values.flatten()
    rhat = float(result.summary(var_names=["tau"])["r_hat"].values[0])
    ci_lo, ci_hi = result.tau_credible_interval
    nearby = nearest_events(result.tau_date, events, window_days=window_days)

    return {
        "name": name,
        "change_point_date": result.tau_date.date().isoformat(),
        "credible_interval": [ci_lo.date().isoformat(), ci_hi.date().isoformat()],
        "before_mean": round(float(mu1.mean()), 2),
        "after_mean": round(float(mu2.mean()), 2),
        "pct_change": round(pct_change(mu1.mean(), mu2.mean()), 1),
        "r_hat_tau": round(rhat, 4),
        "nearby_events": [
            {
                "event_name": row["event_name"],
                "start_date": row["start_date"].date().isoformat(),
                "category": row["category"],
                "days_from_changepoint": int(row["days_from_changepoint"]),
            }
            for _, row in nearby.iterrows()
        ],
    }


def main():
    print("Loading data...")
    prices = load_brent_prices()
    prices = add_log_returns(prices)
    events = load_events()

    results = {"generated_from_rows": len(prices), "changepoints": []}

    print("Fitting global change point model (full series)...")
    global_result = fit_mean_changepoint(
        prices["Price"].values, prices.index,
        draws=1500, tune=1000, chains=4, cores=1,
        target_accept=0.9, random_seed=RNG_SEED, progressbar=False,
    )
    results["changepoints"].append(
        summarize_mean_result("Global (full 1987-2022 series)", global_result, events, window_days=800)
    )

    event_windows = {
        "2008 Global Financial Crisis": ("2008-06-01", "2008-12-31"),
        "2014 OPEC decision not to cut": ("2014-09-01", "2014-12-31"),
        "2020 COVID-19 / oil price war": ("2020-01-01", "2020-06-30"),
        "2022 Russia's invasion of Ukraine": ("2021-11-01", "2022-05-31"),
    }

    for name, (start, end) in event_windows.items():
        print(f"Fitting window model: {name} ...")
        w = prices.loc[start:end]
        res = fit_mean_changepoint(
            w["Price"].values, w.index,
            draws=3000, tune=3000, chains=4, cores=1,
            target_accept=0.97, random_seed=RNG_SEED, progressbar=False,
        )
        entry = summarize_mean_result(name, res, events, window_days=60)
        entry["window"] = [start, end]
        results["changepoints"].append(entry)

    print("Fitting volatility change point model (2019-10 to 2020-12, log returns)...")
    vol_window = prices.loc["2019-10-01":"2020-12-31"].dropna(subset=["log_return"])
    vol_result = fit_mean_and_vol_changepoint(
        vol_window["log_return"].values, vol_window.index,
        draws=4000, tune=4000, chains=4, cores=1,
        target_accept=0.97, random_seed=RNG_SEED, progressbar=False,
    )
    sigma1 = vol_result.trace.posterior["sigma1"].values.flatten()
    sigma2 = vol_result.trace.posterior["sigma2"].values.flatten()
    rhat_vol = float(vol_result.summary(var_names=["tau"])["r_hat"].values[0])
    ci_lo, ci_hi = vol_result.tau_credible_interval
    results["volatility_changepoint"] = {
        "name": "Volatility regime shift (log returns, 2019-10 to 2020-12)",
        "change_point_date": vol_result.tau_date.date().isoformat(),
        "credible_interval": [ci_lo.date().isoformat(), ci_hi.date().isoformat()],
        "sigma_before": round(float(sigma1.mean()), 5),
        "sigma_after": round(float(sigma2.mean()), 5),
        "pct_change": round(pct_change(sigma1.mean(), sigma2.mean()), 1),
        "r_hat_tau": round(rhat_vol, 4),
    }

    # Overall descriptive metrics used by the /api/metrics endpoint
    results["overall_metrics"] = {
        "date_range": [prices.index.min().date().isoformat(), prices.index.max().date().isoformat()],
        "n_observations": int(len(prices)),
        "overall_mean_price": round(float(prices["Price"].mean()), 2),
        "overall_price_volatility_30d_avg": round(
            float(prices["log_return"].rolling(30).std().mean()), 5
        ),
        "min_price": round(float(prices["Price"].min()), 2),
        "min_price_date": prices["Price"].idxmin().date().isoformat(),
        "max_price": round(float(prices["Price"].max()), 2),
        "max_price_date": prices["Price"].idxmax().date().isoformat(),
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nWrote {OUT_PATH}")


if __name__ == "__main__":
    main()
