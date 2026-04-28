import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from src.collector import fetch_prices, detect_alerts, save_to_csv


MOCK_API_RESPONSE = [
    {
        "id": "bitcoin", "symbol": "btc", "name": "Bitcoin",
        "current_price": 65000.0, "market_cap": 1_200_000_000_000,
        "total_volume": 30_000_000_000, "price_change_percentage_24h": 3.5,
        "high_24h": 66000.0, "low_24h": 63000.0, "circulating_supply": 19_000_000,
    },
    {
        "id": "ethereum", "symbol": "eth", "name": "Ethereum",
        "current_price": 3500.0, "market_cap": 420_000_000_000,
        "total_volume": 18_000_000_000, "price_change_percentage_24h": -6.2,
        "high_24h": 3700.0, "low_24h": 3400.0, "circulating_supply": 120_000_000,
    },
    {
        "id": "solana", "symbol": "sol", "name": "Solana",
        "current_price": 180.0, "market_cap": 80_000_000_000,
        "total_volume": 4_000_000_000, "price_change_percentage_24h": 1.2,
        "high_24h": 185.0, "low_24h": 175.0, "circulating_supply": 440_000_000,
    },
]


@patch("src.collector.requests.get")
def test_fetch_prices_returns_dataframe(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_API_RESPONSE
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    df = fetch_prices(top_n=3)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3
    assert "current_price" in df.columns
    assert "collected_at" in df.columns


@patch("src.collector.requests.get")
def test_fetch_prices_has_timestamp(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_API_RESPONSE
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    df = fetch_prices(top_n=3)

    assert pd.api.types.is_datetime64_any_dtype(df["collected_at"]) or \
           isinstance(df["collected_at"].iloc[0], datetime)


@patch("src.collector.requests.get")
def test_fetch_prices_raises_on_api_error(mock_get):
    import requests
    mock_get.side_effect = requests.exceptions.ConnectionError("sem internet")

    with pytest.raises(requests.exceptions.ConnectionError):
        fetch_prices()


def test_detect_alerts_finds_extreme_changes():
    df = pd.DataFrame(MOCK_API_RESPONSE)
    df["collected_at"] = datetime.now(timezone.utc)

    alerts = detect_alerts(df, threshold=5.0)

    assert len(alerts) == 1
    assert alerts.iloc[0]["id"] == "ethereum"
    assert alerts.iloc[0]["alert_type"] == "QUEDA"


def test_detect_alerts_empty_when_no_extremes():
    df = pd.DataFrame(MOCK_API_RESPONSE)
    df["collected_at"] = datetime.now(timezone.utc)

    alerts = detect_alerts(df, threshold=99.0)

    assert alerts.empty


def test_detect_alerts_marks_positive_as_alta():
    data = [{**MOCK_API_RESPONSE[0], "price_change_percentage_24h": 8.0}]
    df = pd.DataFrame(data)
    df["collected_at"] = datetime.now(timezone.utc)

    alerts = detect_alerts(df, threshold=5.0)

    assert alerts.iloc[0]["alert_type"] == "ALTA"


def test_save_to_csv(tmp_path):
    df = pd.DataFrame(MOCK_API_RESPONSE)
    df["collected_at"] = datetime.now(timezone.utc)

    path = save_to_csv(df, path=str(tmp_path))

    assert path.endswith(".csv")
    loaded = pd.read_csv(path)
    assert len(loaded) == 3
    assert "current_price" in loaded.columns
