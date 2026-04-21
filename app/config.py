"""
Logit Blog — 앱 설정
"""
import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "Logit")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")
    DEBUG: bool = os.getenv("APP_ENV", "development") == "development"

    # DB
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./logit.db"  # 로컬 개발용 SQLite 폴백
    )

    # 관리자
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@logit.kr")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin1234!")

    # JWT
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7일

    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    AI_MODEL: str = os.getenv("AI_MODEL", "gpt-4o-mini")
    AI_DRAFT_CATEGORIES: list = os.getenv(
        "AI_DRAFT_CATEGORIES",
        "AI 활용,자동화,생산성,디지털 도구,블로그 운영,수익화 실험,노트/정리법,비교/리뷰"
    ).split(",")

    # 스케줄러
    AI_DRAFT_SCHEDULE_HOUR: int = int(os.getenv("AI_DRAFT_SCHEDULE_HOUR", "6"))
    AI_DRAFT_SCHEDULE_MINUTE: int = int(os.getenv("AI_DRAFT_SCHEDULE_MINUTE", "0"))
    AI_DRAFT_TIMEZONE: str = os.getenv("AI_DRAFT_TIMEZONE", "Asia/Seoul")

    # AdSense
    ADSENSE_CLIENT_ID: str = os.getenv("ADSENSE_CLIENT_ID", "")
    ADSENSE_SLOT_TOP: str = os.getenv("ADSENSE_SLOT_TOP", "")
    ADSENSE_SLOT_MID: str = os.getenv("ADSENSE_SLOT_MID", "")
    ADSENSE_SLOT_BOTTOM: str = os.getenv("ADSENSE_SLOT_BOTTOM", "")
    ADSENSE_SLOT_SIDEBAR: str = os.getenv("ADSENSE_SLOT_SIDEBAR", "")

    # GA
    GA_MEASUREMENT_ID: str = os.getenv("GA_MEASUREMENT_ID", "")


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
