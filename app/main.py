"""
Logit Blog — FastAPI 메인 진입점
"""
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.gzip import GZipMiddleware

from app.config import settings
from app.database import init_db, SessionLocal
from app.routers import blog, admin
from app.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("logit")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 처리"""
    # 시작
    logger.info("Logit Blog 시작 중...")
    init_db()
    _seed_initial_data()
    start_scheduler()
    logger.info("Logit Blog 준비 완료!")
    yield
    # 종료
    stop_scheduler()
    logger.info("Logit Blog 종료")


def _seed_initial_data():
    """최초 실행 시 기본 데이터 삽입 (카테고리, 관리자)"""
    from app.models import Category, Admin
    from app.auth import hash_password
    db = SessionLocal()
    try:
        # 카테고리 초기 데이터
        if db.query(Category).count() == 0:
            categories = [
                Category(name="AI 활용", slug="ai", icon="🤖", description="ChatGPT, Claude 등 AI 도구 실용 가이드", order=1),
                Category(name="자동화", slug="automation", icon="⚙️", description="Make.com, Zapier, n8n으로 업무 자동화", order=2),
                Category(name="생산성", slug="productivity", icon="⚡", description="시간 관리, 집중력, 업무 효율 향상", order=3),
                Category(name="디지털 도구", slug="tools", icon="🛠️", description="앱·서비스 실사용 리뷰와 비교", order=4),
                Category(name="블로그 운영", slug="blog-ops", icon="📊", description="SEO, 콘텐츠 전략, 수익화", order=5),
                Category(name="수익화 실험", slug="monetize", icon="💰", description="AdSense, 제휴 마케팅 실전 기록", order=6),
                Category(name="노트/정리법", slug="notes", icon="📝", description="지식 관리, 노트 시스템, Obsidian", order=7),
                Category(name="비교/리뷰", slug="review", icon="⚖️", description="도구와 서비스 심층 비교 분석", order=8),
            ]
            db.add_all(categories)
            db.commit()
            logger.info("기본 카테고리 8개 생성 완료")

        # 관리자 계정
        if db.query(Admin).count() == 0:
            admin = Admin(
                email=settings.ADMIN_EMAIL,
                hashed_password=hash_password(settings.ADMIN_PASSWORD),
                name="운영자",
            )
            db.add(admin)
            db.commit()
            logger.info(f"관리자 계정 생성: {settings.ADMIN_EMAIL}")
    except Exception as e:
        logger.error(f"초기 데이터 생성 오류: {e}")
        db.rollback()
    finally:
        db.close()


app = FastAPI(
    title="Logit Blog",
    description="AI + 자동화 + 생산성 블로그",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/admin/api-docs" if settings.DEBUG else None,
    redoc_url=None,
)

# 미들웨어
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 정적 파일
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 라우터 등록
app.include_router(blog.router)
app.include_router(admin.router)


# ── 404 핸들러 ───────────────────────────────────────────────
templates = Jinja2Templates(directory="app/templates")

def _error_context(request: Request, status: int) -> dict:
    """에러 페이지 공통 컨텍스트 (DB 없이)"""
    from app.database import SessionLocal
    from app.models import Post, PostStatus
    from sqlalchemy import desc
    ctx = {
        "request": request,
        "site_name": settings.APP_NAME,
        "base_url": settings.BASE_URL,
        "current_year": datetime.now().year,
        "sidebar_categories": [],
        "popular_posts": [],
        "recent_tags": [],
        "adsense_client": settings.ADSENSE_CLIENT_ID,
        "adsense_slot_top": "", "adsense_slot_mid": "",
        "adsense_slot_bottom": "", "adsense_slot_sidebar": "",
        "ga_id": settings.GA_MEASUREMENT_ID,
        "canonical_url": None, "meta_description": None,
    }
    try:
        db = SessionLocal()
        from app.models import Category
        ctx["sidebar_categories"] = db.query(Category).order_by(Category.order).all()
        ctx["popular_posts"] = (
            db.query(Post)
            .filter(Post.status == PostStatus.PUBLISHED)
            .order_by(desc(Post.view_count))
            .limit(3).all()
        )
        db.close()
    except Exception:
        pass
    return ctx


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    ctx = _error_context(request, 404)
    return templates.TemplateResponse("404.html", ctx, status_code=404)


@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    ctx = _error_context(request, 500)
    ctx["error_title"] = "서버 오류"
    ctx["error_message"] = "일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
    return templates.TemplateResponse("404.html", ctx, status_code=500)
