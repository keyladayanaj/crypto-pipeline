import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL         = os.getenv("DATABASE_URL", "postgresql://admin:secret@localhost:5432/cryptodb")
COINGECKO_API_URL    = os.getenv("COINGECKO_API_URL", "https://api.coingecko.com/api/v3")
TOP_N_COINS          = int(os.getenv("TOP_N_COINS", "20"))
COLLECT_INTERVAL_HRS = int(os.getenv("COLLECT_INTERVAL_HOURS", "1"))
ALERT_THRESHOLD_PCT  = float(os.getenv("ALERT_THRESHOLD_PCT", "5.0"))
