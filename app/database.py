"""
Logit Blog — 데이터베이스 연결 설정
SQLAlchemy + PostgreSQL (로컬 개발 시 SQLite 자동 폴백)
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# PostgreSQL URL 형식 맞추기 (Render/Supabase는 postgres:// 를 postgresql:// 로 변환)
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# SQLite는 check_same_thread=False 필요
connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_recycle=300,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI Dependency — DB 세션 제공"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """앱 시작 시 테이블 생성"""
    from app import models  # noqa: F401 — 모델 임포트로 테이블 등록
    Base.metadata.create_all(bind=engine)
