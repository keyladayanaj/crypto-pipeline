import logging
import pandas as pd
from datetime import datetime, timezone
from sqlalchemy import create_engine, String, Float, DateTime, Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from src.config import DATABASE_URL

logger = logging.getLogger(__name__)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)


class Base(DeclarativeBase):
    pass


class PriceSnapshot(Base):
    """Cada linha = 1 coin em 1 momento de coleta."""
    __tablename__ = "price_snapshots"

    id:               Mapped[int]   = mapped_column(Integer, primary_key=True, autoincrement=True)
    coin_id:          Mapped[str]   = mapped_column(String(50), index=True)
    symbol:           Mapped[str]   = mapped_column(String(20))
    name:             Mapped[str]   = mapped_column(String(100))
    price_usd:        Mapped[float] = mapped_column(Float)
    market_cap:       Mapped[float] = mapped_column(Float, nullable=True)
    total_volume:     Mapped[float] = mapped_column(Float, nullable=True)
    change_24h_pct:   Mapped[float] = mapped_column(Float, nullable=True)
    high_24h:         Mapped[float] = mapped_column(Float, nullable=True)
    low_24h:          Mapped[float] = mapped_column(Float, nullable=True)
    circulating_supply: Mapped[float] = mapped_column(Float, nullable=True)
    collected_at:     Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class Alert(Base):
    """Registra variações bruscas detectadas."""
    __tablename__ = "alerts"

    id:          Mapped[int]   = mapped_column(Integer, primary_key=True, autoincrement=True)
    coin_id:     Mapped[str]   = mapped_column(String(50))
    symbol:      Mapped[str]   = mapped_column(String(20))
    alert_type:  Mapped[str]   = mapped_column(String(10))   # "ALTA" ou "QUEDA"
    change_pct:  Mapped[float] = mapped_column(Float)
    price_usd:   Mapped[float] = mapped_column(Float)
    created_at:  Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                  default=lambda: datetime.now(timezone.utc))
    notes:       Mapped[str]   = mapped_column(Text, nullable=True)


def init_db():
    """Cria todas as tabelas se não existirem."""
    Base.metadata.create_all(engine)
    logger.info("Banco inicializado.")


def save_snapshot(df: pd.DataFrame) -> int:
    """Insere todos os registros do DataFrame na tabela price_snapshots."""
    records = [
        PriceSnapshot(
            coin_id=row["id"],
            symbol=row["symbol"],
            name=row["name"],
            price_usd=row["current_price"],
            market_cap=row.get("market_cap"),
            total_volume=row.get("total_volume"),
            change_24h_pct=row.get("price_change_percentage_24h"),
            high_24h=row.get("high_24h"),
            low_24h=row.get("low_24h"),
            circulating_supply=row.get("circulating_supply"),
            collected_at=row["collected_at"],
        )
        for _, row in df.iterrows()
    ]
    with Session(engine) as session:
        session.add_all(records)
        session.commit()
    logger.info(f"{len(records)} registros inseridos.")
    return len(records)


def save_alerts(alerts_df: pd.DataFrame):
    """Persiste alertas de variação brusca."""
    if alerts_df.empty:
        return
    records = [
        Alert(
            coin_id=row["id"],
            symbol=row["symbol"],
            alert_type=row["alert_type"],
            change_pct=row["price_change_percentage_24h"],
            price_usd=row["current_price"],
        )
        for _, row in alerts_df.iterrows()
    ]
    with Session(engine) as session:
        session.add_all(records)
        session.commit()
    logger.info(f"{len(records)} alertas salvos.")
