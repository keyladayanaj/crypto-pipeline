import logging
import sys
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED

from src.config import COLLECT_INTERVAL_HRS
from src.collector import fetch_prices, detect_alerts
from src.database import init_db, save_snapshot, save_alerts

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("scheduler")


def run_pipeline():
    """Etapa completa: coleta → detecta alertas → persiste."""
    logger.info("=== Iniciando coleta ===")
    try:
        df = fetch_prices()
        save_snapshot(df)

        alerts = detect_alerts(df)
        if not alerts.empty:
            logger.warning(f"ALERTA: {len(alerts)} moedas com variação extrema:")
            for _, row in alerts.iterrows():
                logger.warning(
                    f"  [{row['alert_type']}] {row['symbol'].upper()} "
                    f"{row['price_change_percentage_24h']:+.2f}% "
                    f"@ ${row['current_price']:,.4f}"
                )
            save_alerts(alerts)
        else:
            logger.info("Nenhum alerta detectado.")

        logger.info("=== Coleta concluída ===\n")
    except Exception as e:
        logger.error(f"Falha na coleta: {e}", exc_info=True)


def on_job_event(event):
    if event.exception:
        logger.error(f"Job falhou: {event.exception}")
    else:
        logger.info("Job executado com sucesso.")


if __name__ == "__main__":
    logger.info("Inicializando banco de dados...")
    init_db()

    logger.info("Executando coleta inicial...")
    run_pipeline()

    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(
        run_pipeline,
        trigger="interval",
        hours=COLLECT_INTERVAL_HRS,
        id="crypto_pipeline",
        name="Coleta de Preços",
        misfire_grace_time=300,
    )
    scheduler.add_listener(on_job_event, EVENT_JOB_ERROR | EVENT_JOB_EXECUTED)

    logger.info(f"Scheduler iniciado — coletando a cada {COLLECT_INTERVAL_HRS}h.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler encerrado.")
