"""
app.py — Flask backend for the Brent Oil Change Point Analysis dashboard.

Serves three kinds of data to the React frontend:
  1. Historical price data       -> GET /api/prices
  2. Change point model results  -> GET /api/changepoints
  3. Event correlation data      -> GET /api/events
Plus a small summary endpoint    -> GET /api/metrics
and a health check               -> GET /api/health

Design note: change point results come from PyMC/MCMC sampling, which
takes tens of seconds to a couple of minutes. That's unacceptable for a
live HTTP request, so `precompute_changepoints.py` is run once (offline)
to produce data/changepoints.json, and this Flask app simply reads and
serves that static file. Price and event data are small enough to load
and filter live from CSV on every request.
"""
from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

app = Flask(__name__)
CORS(app)  # allow the React dev server (different origin/port) to call these APIs


def _load_prices() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "BrentOilPrices.csv")
    df["Date"] = pd.to_datetime(df["Date"])
    return df.sort_values("Date")


def _load_events() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "brent_oil_key_events.csv")
    df["start_date"] = pd.to_datetime(df["start_date"])
    return df.sort_values("start_date")


@app.get("/api/health")
def health():
    """Simple liveness check."""
    return jsonify({"status": "ok"})


@app.get("/api/prices")
def get_prices():
    """
    Historical Brent price data.

    Query params (all optional):
      start     ISO date (YYYY-MM-DD) — filter to prices on/after this date
      end       ISO date (YYYY-MM-DD) — filter to prices on/before this date
      freq      'D' (default, daily/raw), 'W' (weekly mean), or 'M' (monthly mean)
                 — use W or M to reduce payload size for wide date ranges

    Response: { "count": <int>, "data": [ { "date": "YYYY-MM-DD", "price": <float> }, ... ] }
    """
    df = _load_prices()

    start = request.args.get("start")
    end = request.args.get("end")
    if start:
        df = df[df["Date"] >= pd.to_datetime(start)]
    if end:
        df = df[df["Date"] <= pd.to_datetime(end)]

    freq = request.args.get("freq", "D").upper()
    if freq in ("W", "M"):
        pandas_freq = {"W": "W", "M": "ME"}[freq]
        df = (
            df.set_index("Date")["Price"]
            .resample(pandas_freq)
            .mean()
            .dropna()
            .reset_index()
        )

    records = [
        {"date": row["Date"].strftime("%Y-%m-%d"), "price": round(float(row["Price"]), 2)}
        for _, row in df.iterrows()
    ]
    return jsonify({"count": len(records), "data": records})


@app.get("/api/events")
def get_events():
    """
    Compiled major oil-market events (geopolitical, OPEC, economic, sanctions).

    Query params (all optional):
      category  comma-separated list of categories to include
                 (e.g. "OPEC Decision,Economic Shock")
      start     ISO date — only events on/after this date
      end       ISO date — only events on/before this date

    Response: { "count": <int>, "data": [ {event fields...}, ... ] }
    """
    df = _load_events()

    category = request.args.get("category")
    if category:
        wanted = {c.strip() for c in category.split(",")}
        df = df[df["category"].isin(wanted)]

    start = request.args.get("start")
    end = request.args.get("end")
    if start:
        df = df[df["start_date"] >= pd.to_datetime(start)]
    if end:
        df = df[df["start_date"] <= pd.to_datetime(end)]

    records = [
        {
            "event_id": int(row["event_id"]),
            "start_date": row["start_date"].strftime("%Y-%m-%d"),
            "event_name": row["event_name"],
            "category": row["category"],
            "region": row["region"],
            "description": row["description"],
            "expected_direction": row["expected_direction"],
        }
        for _, row in df.iterrows()
    ]
    return jsonify({"count": len(records), "data": records})


@app.get("/api/changepoints")
def get_changepoints():
    """
    Precomputed Bayesian change point model results (see
    backend/precompute_changepoints.py and notebooks/task2_change_point_modeling.ipynb
    for how these were derived).

    Response includes:
      - changepoints: list of { name, change_point_date, credible_interval,
        before_mean, after_mean, pct_change, r_hat_tau, nearby_events, window? }
        — one entry for the global full-series model, plus one per event-focused window
      - volatility_changepoint: the mean+volatility shift model result
      - overall_metrics: summary descriptive statistics
    """
    import json
    with open(DATA_DIR / "changepoints.json") as f:
        return jsonify(json.load(f))


@app.get("/api/metrics")
def get_metrics():
    """
    Summary indicators for dashboard KPI cards: overall mean price, volatility,
    min/max price and their dates, date range and row count of the underlying data.
    """
    import json
    with open(DATA_DIR / "changepoints.json") as f:
        data = json.load(f)
    return jsonify(data.get("overall_metrics", {}))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
