"""
Logit Blog — APScheduler 기반 백그라운드 스케줄러
매일 설정된 시간에 AI 초안 자동 생성
"""
import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.config import settings
from app.database import SessionLocal
from app.ai_generator import generate_ai_draft

logger = logging.getLogger("logit.scheduler")

scheduler = AsyncIOScheduler(timezone=settings.AI_DRAFT_TIMEZONE)


async def daily_ai_draft_job():
    """매일 자동 실행되는 AI 초안 생성 작업"""
    logger.info("[Scheduler] AI 일일 초안 생성 시작...")
    db = SessionLocal()
    try:
        post = await generate_ai_draft(db)
        if post:
            logger.info(f"[Scheduler] 완료 — 초안 제목: '{post.title}'")
        else:
            logger.warning("[Scheduler] 초안 생성 실패")
    except Exception as e:
        logger.error(f"[Scheduler] 오류 발생: {e}")
    finally:
        db.close()


def start_scheduler():
    """앱 시작 시 스케줄러 등록 및 시작"""
    scheduler.add_job(
        daily_ai_draft_job,
        trigger=CronTrigger(
            hour=settings.AI_DRAFT_SCHEDULE_HOUR,
            minute=settings.AI_DRAFT_SCHEDULE_MINUTE,
            timezone=settings.AI_DRAFT_TIMEZONE,
        ),
        id="daily_ai_draft",
        name="매일 AI 초안 자동 생성",
        replace_existing=True,
        misfire_grace_time=3600,  # 1시간 내 실행 놓쳐도 한 번 실행
    )
    scheduler.start()
    logger.info(
        f"[Scheduler] 시작 — 매일 {settings.AI_DRAFT_SCHEDULE_HOUR:02d}:"
        f"{settings.AI_DRAFT_SCHEDULE_MINUTE:02d} KST에 AI 초안 생성"
    )


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("[Scheduler] 종료")
