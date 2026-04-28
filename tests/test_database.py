import pytest
import pandas as pd
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, call


MOCK_DF = pd.DataFrame([
    {
        "id": "bitcoin", "symbol": "btc", "name": "Bitcoin",
        "current_price": 65000.0, "market_cap": 1_200_000_000_000,
        "total_volume": 30_000_000_000, "price_change_percentage_24h": 3.5,
        "high_24h": 66000.0, "low_24h": 63000.0, "circulating_supply": 19_000_000,
        "collected_at": datetime.now(timezone.utc),
    }
])


def test_save_snapshot_calls_session_add_all():
    with patch("src.database.Session") as MockSession:
        mock_session = MagicMock()
        MockSession.return_value.__enter__.return_value = mock_session

        from src.database import save_snapshot
        count = save_snapshot(MOCK_DF)

        assert count == 1
        mock_session.add_all.assert_called_once()
        mock_session.commit.assert_called_once()


def test_save_alerts_skips_empty_df():
    with patch("src.database.Session") as MockSession:
        from src.database import save_alerts
        save_alerts(pd.DataFrame())
        MockSession.assert_not_called()
