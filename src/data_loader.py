"""
data_loader.py

Utilities for loading and lightly validating the Brent oil price series
and the compiled event dataset used throughout this project.
"""
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def load_brent_prices(path: str | Path = RAW_DATA_DIR / "BrentOilPrices.csv") -> pd.DataFrame:
    """
    Load the daily Brent crude oil price series.

    Expects a CSV with columns: Date, Price
    Returns a DataFrame indexed by Date (datetime), sorted ascending,
    with a Price column of type float.
    """
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"]).sort_values("Date")
    df = df.set_index("Date")
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
    df = df[~df.index.duplicated(keep="first")]
    return df


def load_events(path: str | Path = RAW_DATA_DIR / "brent_oil_key_events.csv") -> pd.DataFrame:
    """
    Load the structured dataset of major oil-market events.

    Expects columns: event_id, start_date, event_name, category, region,
    description, expected_direction.
    """
    df = pd.read_csv(path)
    df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")
    return df.sort_values("start_date").reset_index(drop=True)


def add_log_returns(df: pd.DataFrame, price_col: str = "Price") -> pd.DataFrame:
    """
    Add log price and log return columns to a price DataFrame.
    """
    out = df.copy()
    out["log_price"] = np.log(out[price_col])
    out["log_return"] = out["log_price"].diff()
    return out
