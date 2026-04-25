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
    """최초 실행 시 기본 데이터 삽입 (카테고리, 관리자, 사이트 설정)"""
    from app.models import Category, Admin
    from app.auth import hash_password
    db = SessionLocal()
    try:
        # ── 카테고리: 새 슬러그로 upsert ──────────────────────
        new_categories = [
            dict(name="아이의 돈 공부", slug="kids-money", icon="💰",
                 description="용돈, 소비, 저축, 선택과 책임을 아이의 눈높이로 풀어갑니다.", order=1),
            dict(name="부모의 교육 고민", slug="education", icon="📚",
                 description="대안교육을 선택한 부모의 시선으로 아이의 배움과 성장을 기록합니다.", order=2),
            dict(name="부모를 위한 AI 활용", slug="ai-parenting", icon="🤖",
                 description="ChatGPT와 AI 도구를 육아와 교육 자료, 가족 기록에 활용하는 방법을 정리합니다.", order=3),
            dict(name="책과 도구 리뷰", slug="book-review", icon="📖",
                 description="아이와 부모가 함께 읽기 좋은 책, 교육에 도움이 되는 도구를 소개합니다.", order=4),
        ]
        for cat_data in new_categories:
            existing = db.query(Category).filter(Category.slug == cat_data["slug"]).first()
            if existing:
                # 이름/아이콘/설명 최신화
                existing.name = cat_data["name"]
                existing.icon = cat_data["icon"]
                existing.description = cat_data["description"]
                existing.order = cat_data["order"]
            else:
                db.add(Category(**cat_data))
        db.commit()
        logger.info("카테고리 초기화/업데이트 완료")

        # ── 사이트 기본 설정 ──────────────────────────────────
        from app.models import SiteSettings
        defaults = {
            "site_author_name": "Logit 운영자",
            "site_author_bio": "두 아이를 키우고 있는 아빠입니다. 아이를 키우며 교육 문제를 오래 고민했고, 그 과정에서 대안교육을 선택했습니다. 이 블로그는 그런 고민의 연장선에서 아이들이 돈과 기술, 배움을 건강하게 이해하도록 돕기 위해 시작했습니다.",
            "site_author_avatar": "",
            "blog_title": "Logit",
            "blog_description": "7세와 10세 아이를 키우며 교육, 돈 공부, AI 활용을 함께 고민합니다.",
            "adsense_client": "",
            "adsense_slot_top": "",
            "adsense_slot_mid": "",
            "adsense_slot_sidebar": "",
            "ga_id": "",
        }
        for key, value in defaults.items():
            if not db.query(SiteSettings).filter(SiteSettings.key == key).first():
                db.add(SiteSettings(key=key, value=value))
        db.commit()
        logger.info("사이트 기본 설정 초기화 완료")

        # ── 관리자 계정 ───────────────────────────────────────
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
    description="두 아이를 키우는 아빠가 아이 교육, 어린이 경제교육, 부모의 AI 활용을 기록하는 블로그",
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
