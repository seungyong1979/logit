"""
Logit Blog — 관리자 라우터
로그인, 대시보드, 글 관리(CRUD), AI 초안 생성, 카테고리 관리
"""
from datetime import datetime
from fastapi import APIRouter, Depends, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func
from app.database import get_db
from app.models import Post, Category, Tag, Admin, AIGenerationLog, PostStatus
from app.auth import (
    verify_password, hash_password, create_access_token,
    require_admin, get_current_admin_optional,
)
from app.utils import generate_slug, estimate_read_time, format_date_ko, paginate
from app.config import settings
from app.ai_generator import generate_ai_draft

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")


def admin_context(request: Request, admin: Admin) -> dict:
    return {
        "request": request,
        "admin": admin,
        "site_name": settings.APP_NAME,
        "current_year": datetime.now().year,
    }


# ── 로그인 ───────────────────────────────────────────────────
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, db: Session = Depends(get_db)):
    admin = get_current_admin_optional(request, db)
    if admin:
        return RedirectResponse("/admin/dashboard", status_code=302)
    return templates.TemplateResponse("admin/login.html", {
        "request": request,
        "site_name": settings.APP_NAME,
        "error": None,
    })


@router.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    admin = db.query(Admin).filter(Admin.email == email, Admin.is_active == True).first()
    if not admin or not verify_password(password, admin.hashed_password):
        return templates.TemplateResponse("admin/login.html", {
            "request": request,
            "site_name": settings.APP_NAME,
            "error": "이메일 또는 비밀번호가 올바르지 않습니다.",
        }, status_code=401)

    admin.last_login = datetime.utcnow()
    db.commit()

    token = create_access_token({"sub": admin.email})
    response = RedirectResponse("/admin/dashboard", status_code=302)
    response.set_cookie(
        "admin_token", token,
        httponly=True,
        samesite="lax",
        secure=settings.APP_ENV == "production",
        max_age=60 * 60 * 24 * 7,
    )
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse("/admin/login", status_code=302)
    response.delete_cookie("admin_token")
    return response


# ── 대시보드 ─────────────────────────────────────────────────
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    admin: Admin = Depends(require_admin),
    db: Session = Depends(get_db),
):
    # 통계
    total_posts = db.query(Post).count()
    published_posts = db.query(Post).filter(Post.status == PostStatus.PUBLISHED).count()
    draft_posts = db.query(Post).filter(Post.status == PostStatus.DRAFT).count()
    total_views = db.query(func.sum(Post.view_count)).scalar() or 0

    # 최신 AI 초안 (오늘 생성된 것 포함)
    ai_drafts = (
        db.query(Post)
        .options(joinedload(Post.category))
        .filter(Post.status == PostStatus.DRAFT, Post.is_ai_draft == True)
        .order_by(desc(Post.created_at))
        .limit(5)
        .all()
    )

    # 검수 대기 글
    review_posts = (
        db.query(Post)
        .options(joinedload(Post.category))
        .filter(Post.status == PostStatus.REVIEW)
        .order_by(desc(Post.created_at))
        .limit(5)
        .all()
    )

    # 최근 발행 글
    recent_published = (
        db.query(Post)
        .options(joinedload(Post.category))
        .filter(Post.status == PostStatus.PUBLISHED)
        .order_by(desc(Post.published_at))
        .limit(5)
        .all()
    )

    # 인기 글 TOP 5
    top_posts = (
        db.query(Post)
        .options(joinedload(Post.category))
        .filter(Post.status == PostStatus.PUBLISHED)
        .order_by(desc(Post.view_count))
        .limit(5)
        .all()
    )

    # AI 생성 로그 (최근 7개)
    ai_logs = (
        db.query(AIGenerationLog)
        .order_by(desc(AIGenerationLog.created_at))
        .limit(7)
        .all()
    )

    ctx = admin_context(request, admin)
    ctx.update({
        "total_posts": total_posts,
        "published_posts": published_posts,
        "draft_posts": draft_posts,
        "total_views": total_views,
        "ai_drafts": ai_drafts,
        "review_posts": review_posts,
        "recent_published": recent_published,
        "top_posts": top_posts,
        "ai_logs": ai_logs,
        "format_date_ko": format_date_ko,
    })
    return templates.TemplateResponse("admin/dashboard.html", ctx)


# ── 글 목록 ──────────────────────────────────────────────────
@router.get("/posts", response_class=HTMLResponse)
async def post_list(
    request: Request,
    page: int = Query(1, ge=1),
    status: str = Query("all"),
    category: int = Query(0),
    q: str = Query(""),
    admin: Admin = Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(Post).options(joinedload(Post.category))

    if status != "all":
        try:
            query = query.filter(Post.status == PostStatus(status))
        except ValueError:
            pass
    if category:
        query = query.filter(Post.category_id == category)
    if q:
        query = query.filter(Post.title.ilike(f"%{q}%"))

    query = query.order_by(desc(Post.created_at))
    total = query.count()
    per_page = 20
    posts = query.offset((page - 1) * per_page).limit(per_page).all()
    pagination = paginate(total, page, per_page)

    categories = db.query(Category).order_by(Category.order).all()

    ctx = admin_context(request, admin)
    ctx.update({
        "posts": posts,
        "pagination": pagination,
        "current_page": page,
        "status_filter": status,
        "category_filter": category,
        "search_query": q,
        "categories": categories,
        "format_date_ko": format_date_ko,
        "PostStatus": PostStatus,
    })
    return templates.TemplateResponse("admin/post_list.html", ctx)


# ── 새 글 작성 ────────────────────────────────────────────────
@router.get("/posts/new", response_class=HTMLResponse)
async def post_new(
    request: Request,
    admin: Admin = Depends(require_admin),
    db: Session = Depends(get_db),
):
    categories = db.query(Category).order_by(Category.order).all()
    ctx = admin_context(request, admin)
    ctx.update({
        "post": None,
        "categories": categories,
        "mode": "new",
    })
    return templates.TemplateResponse("admin/post_edit.html", ctx)


@router.post("/posts/new")
async def post_new_submit(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    excerpt: str = Form(""),
    category_id: int = Form(0),
    tags_input: str = Form(""),
    meta_title: str = Form(""),
    meta_description: str = Form(""),
    og_image: str = Form(""),
    status: str = Form("draft"),
    is_featured: bool = Form(False),
    admin: Admin = Depends(require_admin),
    db: Session = Depends(get_db),
):
    slug = generate_slug(title)
    # 슬러그 중복 처리
    existing = db.query(Post).filter(Post.slug == slug).first()
    if existing:
        slug = f"{slug}-{int(datetime.now().timestamp())}"

    post = Post(
        title=title,
        slug=slug,
        content=content,
        excerpt=excerpt or content[:200],
        category_id=category_id or None,
        meta_title=meta_title or title,
        meta_description=meta_description or excerpt or content[:160],
        og_image=og_image,
        is_featured=is_featured,
        status=PostStatus(status),
        read_time_min=estimate_read_time(content),
    )
    if status == PostStatus.PUBLISHED.value:
        post.published_at = datetime.utcnow()

    # 태그 처리
    if tags_input.strip():
        for tag_name in [t.strip() for t in tags_input.split(",") if t.strip()]:
            tag_slug = generate_slug(tag_name)
            tag = db.query(Tag).filter(Tag.slug == tag_slug).first()
            if not tag:
                tag = Tag(name=tag_name, slug=tag_slug)
                db.add(tag)
            post.tags.append(tag)

    db.add(post)
    db.commit()
    return RedirectResponse(f"/admin/posts/{post.id}/edit", status_code=302)


# ── 글 수정 ───────────────────────────────────────────────────
@router.get("/posts/{post_id}/edit", response_class=HTMLResponse)
async def post_edit(
    post_id: int,
    request: Request,
    admin: Admin = Depends(require_admin),
    db: Session = Depends(get_db),
):
    post = (
        db.query(Post)
        .options(joinedload(Post.category), joinedload(Post.tags))
        .filter(Post.id == post_id)
        .first()
    )
    if not post:
        raise HTTPException(status_code=404)

    categories = db.query(Category).order_by(Category.order).all()
    ctx = admin_context(request, admin)
    ctx.update({
        "post": post,
        "categories": categories,
        "mode": "edit",
        "tags_input": ", ".join([t.name for t in post.tags]),
        "PostStatus": PostStatus,
    })
    return templates.TemplateResponse("admin/post_edit.html", ctx)


@router.post("/posts/{post_id}/edit")
async def post_edit_submit(
    post_id: int,
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    excerpt: str = Form(""),
    category_id: int = Form(0),
    tags_input: str = Form(""),
    meta_title: str = Form(""),
    meta_description: str = Form(""),
    og_image: str = Form(""),
    status: str = Form("draft"),
    is_featured: bool = Form(False),
    admin: Admin = Depends(require_admin),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404)

    was_published = post.status == PostStatus.PUBLISHED
    new_status = PostStatus(status)

    post.title = title
    post.content = content
    post.excerpt = excerpt or content[:200]
    post.category_id = category_id or None
    post.meta_title = meta_title or title
    post.meta_description = meta_description or excerpt or content[:160]
    post.og_image = og_image
    post.is_featured = is_featured
    post.status = new_status
    post.updated_at = datetime.utcnow()
    post.read_time_min = estimate_read_time(content)

    # 첫 발행 시 published_at 설정
    if new_status == PostStatus.PUBLISHED and not was_published:
        post.published_at = datetime.utcnow()

    # 태그 갱신
    post.tags.clear()
    if tags_input.strip():
        for tag_name in [t.strip() for t in tags_input.split(",") if t.strip()]:
            tag_slug = generate_slug(tag_name)
            tag = db.query(Tag).filter(Tag.slug == tag_slug).first()
            if not tag:
                tag = Tag(name=tag_name, slug=tag_slug)
                db.add(tag)
            post.tags.append(tag)

    db.commit()
    return RedirectResponse(f"/admin/posts/{post_id}/edit?saved=1", status_code=302)


# ── 글 삭제 ───────────────────────────────────────────────────
@router.post("/posts/{post_id}/delete")
async def post_delete(
    post_id: int,
    admin: Admin = Depends(require_admin),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if post:
        db.delete(post)
        db.commit()
    return RedirectResponse("/admin/posts", status_code=302)


# ── 글 발행/취소 (빠른 액션) ──────────────────────────────────
@router.post("/posts/{post_id}/publish")
async def post_publish(
    post_id: int,
    admin: Admin = Depends(require_admin),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404)
    if post.status != PostStatus.PUBLISHED:
        post.status = PostStatus.PUBLISHED
        if not post.published_at:
            post.published_at = datetime.utcnow()
        db.commit()
    return RedirectResponse(f"/admin/posts/{post_id}/edit", status_code=302)


@router.post("/posts/{post_id}/unpublish")
async def post_unpublish(
    post_id: int,
    admin: Admin = Depends(require_admin),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404)
    post.status = PostStatus.DRAFT
    db.commit()
    return RedirectResponse(f"/admin/posts/{post_id}/edit", status_code=302)


# ── AI 초안 즉시 생성 (수동 트리거) ─────────────────────────
@router.post("/ai/generate")
async def ai_generate(
    request: Request,
    category_slug: str = Form(""),
    admin: Admin = Depends(require_admin),
    db: Session = Depends(get_db),
):
    import asyncio
    from app.database import SessionLocal

    category = None
    if category_slug:
        category = db.query(Category).filter(Category.slug == category_slug).first()

    # 백그라운드에서 실행 (타임아웃 방지)
    async def run_in_background(cat):
        bg_db = SessionLocal()
        try:
            await generate_ai_draft(bg_db, category=cat)
        except Exception as e:
            import logging
            logging.getLogger("logit.ai").error(f"[AI] 백그라운드 생성 실패: {e}")
        finally:
            bg_db.close()

    asyncio.create_task(run_in_background(category))

    # 즉시 대시보드로 이동 (생성은 백그라운드에서 계속)
    return RedirectResponse("/admin/dashboard?ai=generating", status_code=302)


# ── AI 생성 로그 ─────────────────────────────────────────────
@router.get("/ai/logs", response_class=HTMLResponse)
async def ai_logs(
    request: Request,
    admin: Admin = Depends(require_admin),
    db: Session = Depends(get_db),
):
    logs = (
        db.query(AIGenerationLog)
        .order_by(desc(AIGenerationLog.created_at))
        .limit(50)
        .all()
    )
    ctx = admin_context(request, admin)
    ctx.update({"logs": logs, "format_date_ko": format_date_ko})
    return templates.TemplateResponse("admin/ai_logs.html", ctx)


# ── 카테고리 관리 ─────────────────────────────────────────────
@router.get("/categories", response_class=HTMLResponse)
async def admin_categories(
    request: Request,
    admin: Admin = Depends(require_admin),
    db: Session = Depends(get_db),
):
    categories = db.query(Category).order_by(Category.order).all()
    for cat in categories:
        cat._post_count = (
            db.query(func.count(Post.id))
            .filter(Post.category_id == cat.id)
            .scalar()
        )
    ctx = admin_context(request, admin)
    ctx.update({"categories": categories})
    return templates.TemplateResponse("admin/categories.html", ctx)


@router.post("/categories/new")
async def category_new(
    name: str = Form(...),
    slug: str = Form(""),
    description: str = Form(""),
    icon: str = Form("📝"),
    order: int = Form(0),
    admin: Admin = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if not slug:
        slug = generate_slug(name)
    category = Category(
        name=name, slug=slug, description=description,
        icon=icon, order=order,
    )
    db.add(category)
    db.commit()
    return RedirectResponse("/admin/categories", status_code=302)


@router.post("/categories/{cat_id}/delete")
async def category_delete(
    cat_id: int,
    admin: Admin = Depends(require_admin),
    db: Session = Depends(get_db),
):
    cat = db.query(Category).filter(Category.id == cat_id).first()
    if cat:
        db.delete(cat)
        db.commit()
    return RedirectResponse("/admin/categories", status_code=302)


# ── 설정 ──────────────────────────────────────────────────────
@router.get("/settings", response_class=HTMLResponse)
async def admin_settings(
    request: Request,
    admin: Admin = Depends(require_admin),
    db: Session = Depends(get_db),
):
    ctx = admin_context(request, admin)
    ctx.update({"settings": settings})
    return templates.TemplateResponse("admin/settings.html", ctx)
