from datetime import date
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.services.tournament_service import run_daily_tournament

logger = logging.getLogger(__name__)
settings = get_settings()
scheduler = BackgroundScheduler()


def _job() -> None:
    with SessionLocal() as db:
        try:
            run_daily_tournament(db, run_date=date.today())
        except Exception:
            logger.exception("Daily tournament job failed")


def start_scheduler() -> None:
    if scheduler.running:
        return
    scheduler.add_job(
        _job,
        CronTrigger(hour=settings.tournament_run_hour, minute=settings.tournament_run_minute),
        id="daily-tournament",
        replace_existing=True,
    )
    scheduler.start()


def ensure_today_tournament(db: Session) -> None:
    try:
        run_daily_tournament(db, run_date=date.today())
    except Exception:
        logger.exception("Initial tournament run failed")


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)