import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import app  # noqa: E402


@pytest.fixture
def client():
    app.testing = True
    with app.test_client() as c:
        yield c


def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ok"


def test_prices_default(client):
    res = client.get("/api/prices")
    assert res.status_code == 200
    body = res.get_json()
    assert body["count"] > 8000
    assert set(body["data"][0].keys()) == {"date", "price"}


def test_prices_date_range_filter(client):
    res = client.get("/api/prices?start=2020-01-01&end=2020-01-31")
    body = res.get_json()
    assert body["count"] > 0
    assert all("2020-01" in row["date"] for row in body["data"])


def test_prices_monthly_resample_reduces_count(client):
    daily = client.get("/api/prices?start=2020-01-01&end=2020-12-31&freq=D").get_json()
    monthly = client.get("/api/prices?start=2020-01-01&end=2020-12-31&freq=M").get_json()
    assert monthly["count"] < daily["count"]
    assert monthly["count"] <= 12


def test_events_default(client):
    res = client.get("/api/events")
    body = res.get_json()
    assert body["count"] >= 10
    required_fields = {
        "event_id", "start_date", "event_name", "category",
        "region", "description", "expected_direction",
    }
    assert required_fields.issubset(body["data"][0].keys())


def test_events_category_filter(client):
    res = client.get("/api/events?category=OPEC Decision")
    body = res.get_json()
    assert body["count"] > 0
    assert all(row["category"] == "OPEC Decision" for row in body["data"])


def test_changepoints(client):
    res = client.get("/api/changepoints")
    assert res.status_code == 200
    body = res.get_json()
    assert "changepoints" in body
    assert "volatility_changepoint" in body
    assert "overall_metrics" in body
    assert len(body["changepoints"]) == 5  # global + 4 event windows

    names = [cp["name"] for cp in body["changepoints"]]
    assert "Global (full 1987-2022 series)" in names

    for cp in body["changepoints"]:
        assert "change_point_date" in cp
        assert "before_mean" in cp
        assert "after_mean" in cp
        assert "pct_change" in cp
        assert "r_hat_tau" in cp


def test_metrics(client):
    res = client.get("/api/metrics")
    assert res.status_code == 200
    body = res.get_json()
    assert "overall_mean_price" in body
    assert "date_range" in body
    assert "n_observations" in body
