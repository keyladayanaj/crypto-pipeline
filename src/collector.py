import logging
import requests
import pandas as pd
from datetime import datetime, timezone
from src.config import COINGECKO_API_URL, TOP_N_COINS, ALERT_THRESHOLD_PCT

logger = logging.getLogger(__name__)

COLUMNS = [
    "id", "symbol", "name",
    "current_price", "market_cap", "total_volume",
    "price_change_percentage_24h",
    "high_24h", "low_24h",
    "circulating_supply",
]


def fetch_prices(top_n: int = TOP_N_COINS) -> pd.DataFrame:
    """Busca os top N coins por market cap na CoinGecko."""
    url = f"{COINGECKO_API_URL}/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": top_n,
        "page": 1,
        "sparkline": False,
        "price_change_percentage": "24h",
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao chamar CoinGecko: {e}")
        raise

    data = response.json()
    df = pd.DataFrame(data)[COLUMNS].copy()
    df["collected_at"] = datetime.now(timezone.utc)

    logger.info(f"Coletados {len(df)} coins.")
    return df


def detect_alerts(df: pd.DataFrame, threshold: float = ALERT_THRESHOLD_PCT) -> pd.DataFrame:
    """Retorna coins com variação 24h acima do threshold (positivo ou negativo)."""
    alerts = df[df["price_change_percentage_24h"].abs() >= threshold].copy()
    alerts["alert_type"] = alerts["price_change_percentage_24h"].apply(
        lambda x: "ALTA" if x > 0 else "QUEDA"
    )
    return alerts


def save_to_csv(df: pd.DataFrame, path: str = "data/raw") -> str:
    """Salva snapshot em CSV — útil para debug antes de usar o banco."""
    import os
    os.makedirs(path, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H")
    filepath = f"{path}/{ts}.csv"
    df.to_csv(filepath, index=False)
    logger.info(f"CSV salvo em {filepath}")
    return filepath
