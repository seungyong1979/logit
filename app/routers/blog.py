"""
Logit Blog — 공개 블로그 라우터
홈, 글 상세, 카테고리, 검색, RSS, sitemap, robots, ads.txt
"""
from datetime import datetime, timezone
from xml.etree import ElementTree as ET
from fastapi import APIRouter, Depends, Request, HTTPException, Query
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func, or_
from app.database import get_db
from app.models import Post, Category, Tag, PostStatus, SiteSettings
from app.utils import paginate, format_date_ko, format_date_iso, strip_html
from app.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def get_sidebar_data(db: Session) -> dict:
    """사이드바 공통 데이터"""
    try:
        categories = db.query(Category).order_by(Category.order).all()
    except Exception:
        categories = []
    try:
        popular_posts = (
            db.query(Post)
            .options(joinedload(Post.category))
            .filter(Post.status == PostStatus.PUBLISHED)
            .order_by(desc(Post.view_count))
            .limit(5)
            .all()
        )
    except Exception:
        popular_posts = []
    try:
        recent_tags = db.query(Tag).limit(20).all()
    except Exception:
        recent_tags = []
    return {
        "sidebar_categories": categories,
        "popular_posts": popular_posts,
        "recent_tags": recent_tags,
    }


def get_site_settings(db: Session) -> dict:
    """DB의 사이트 설정을 안전하게 로드"""
    defaults = {
        "site_author_name": "Logit 운영자",
        "site_author_bio": "두 아이를 키우고 있는 아빠입니다. 아이를 키우며 교육 문제를 오래 고민했고, 그 과정에서 대안교육을 선택했습니다.",
        "site_author_avatar": "",
        "adsense_client": "",
        "adsense_slot_top": "",
        "adsense_slot_mid": "",
        "adsense_slot_sidebar": "",
        "ga_id": "",
    }
    try:
        rows = db.query(SiteSettings).all()
        for row in rows:
            defaults[row.key] = row.value
    except Exception:
        pass
    return defaults


def common_context(request: Request, db: Session) -> dict:
    """모든 템플릿 공통 컨텍스트"""
    site = get_site_settings(db)
    return {
        "request": request,
        "site_name": settings.APP_NAME,
        "base_url": settings.BASE_URL,
        "adsense_client": site.get("adsense_client") or settings.ADSENSE_CLIENT_ID,
        "adsense_slot_top": site.get("adsense_slot_top") or settings.ADSENSE_SLOT_TOP,
        "adsense_slot_mid": site.get("adsense_slot_mid") or settings.ADSENSE_SLOT_MID,
        "adsense_slot_bottom": settings.ADSENSE_SLOT_BOTTOM,
        "adsense_slot_sidebar": site.get("adsense_slot_sidebar") or settings.ADSENSE_SLOT_SIDEBAR,
        "ga_id": site.get("ga_id") or settings.GA_MEASUREMENT_ID,
        "current_year": datetime.now().year,
        "site_author_name": site.get("site_author_name", "Logit 운영자"),
        "site_author_bio": site.get("site_author_bio", ""),
        "site_author_avatar": site.get("site_author_avatar", ""),
        **get_sidebar_data(db),
    }


# ── 홈 ──────────────────────────────────────────────────────
@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    published = Post.status == PostStatus.PUBLISHED

    latest_posts = (
        db.query(Post)
        .options(joinedload(Post.category))
        .filter(published)
        .order_by(desc(Post.published_at))
        .limit(6)
        .all()
    )
    featured_post = (
        db.query(Post)
        .options(joinedload(Post.category))
        .filter(published, Post.is_featured == True)
        .order_by(desc(Post.published_at))
        .first()
    ) or (latest_posts[0] if latest_posts else None)

    popular_posts = (
        db.query(Post)
        .options(joinedload(Post.category))
        .filter(published)
        .order_by(desc(Post.view_count))
        .limit(4)
        .all()
    )
    categories = db.query(Category).order_by(Category.order).all()
    total_posts = db.query(Post).filter(published).count()

    ctx = common_context(request, db)
    ctx.update({
        "page_title": f"{settings.APP_NAME} | 아이와 함께 배우는 AI 시대의 돈 공부",
        "latest_posts": latest_posts,
        "featured_post": featured_post,
        "popular_posts": popular_posts,
        "categories": categories,
        "total_posts": total_posts,
    })
    return templates.TemplateResponse("blog/home.html", ctx)


# ── 글 상세 ──────────────────────────────────────────────────
@router.get("/post/{slug}", response_class=HTMLResponse)
async def post_detail(slug: str, request: Request, db: Session = Depends(get_db)):
    post = (
        db.query(Post)
        .options(joinedload(Post.category), joinedload(Post.tags))
        .filter(Post.slug == slug, Post.status == PostStatus.PUBLISHED)
        .first()
    )
    if not post:
        raise HTTPException(status_code=404, detail="글을 찾을 수 없습니다.")

    # 조회수 증가
    post.view_count = (post.view_count or 0) + 1
    db.commit()

    # 관련 글
    related_posts = (
        db.query(Post)
        .options(joinedload(Post.category))
        .filter(
            Post.status == PostStatus.PUBLISHED,
            Post.id != post.id,
            Post.category_id == post.category_id,
        )
        .order_by(desc(Post.published_at))
        .limit(3)
        .all()
    )
    if len(related_posts) < 3:
        extra = (
            db.query(Post)
            .options(joinedload(Post.category))
            .filter(
                Post.status == PostStatus.PUBLISHED,
                Post.id != post.id,
                Post.id.notin_([p.id for p in related_posts]),
            )
            .order_by(desc(Post.view_count))
            .limit(3 - len(related_posts))
            .all()
        )
        related_posts.extend(extra)

    ctx = common_context(request, db)
    ctx.update({
        "page_title": f"{post.meta_title or post.title} | {settings.APP_NAME}",
        "meta_description": post.meta_description or post.excerpt,
        "og_image": post.og_image or f"{settings.BASE_URL}/static/images/og-default.png",
        "canonical_url": f"{settings.BASE_URL}/post/{post.slug}",
        "post": post,
        "related_posts": related_posts,
        "format_date_ko": format_date_ko,
        "format_date_iso": format_date_iso,
    })
    return templates.TemplateResponse("blog/post.html", ctx)


# ── 카테고리 ─────────────────────────────────────────────────
@router.get("/category/{slug}", response_class=HTMLResponse)
async def category_posts(
    slug: str,
    request: Request,
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db),
):
    category = db.query(Category).filter(Category.slug == slug).first()
    if not category:
        raise HTTPException(status_code=404, detail="카테고리를 찾을 수 없습니다.")

    query = (
        db.query(Post)
        .options(joinedload(Post.category))
        .filter(Post.status == PostStatus.PUBLISHED, Post.category_id == category.id)
        .order_by(desc(Post.published_at))
    )
    total = query.count()
    per_page = 9
    posts = query.offset((page - 1) * per_page).limit(per_page).all()
    pagination = paginate(total, page, per_page)

    ctx = common_context(request, db)
    ctx.update({
        "page_title": f"{category.name} — 카테고리 | {settings.APP_NAME}",
        "meta_description": category.description,
        "canonical_url": f"{settings.BASE_URL}/category/{slug}",
        "category": category,
        "posts": posts,
        "pagination": pagination,
        "current_page": page,
        "format_date_ko": format_date_ko,
    })
    return templates.TemplateResponse("blog/category.html", ctx)


# ── 카테고리 목록 ─────────────────────────────────────────────
@router.get("/categories", response_class=HTMLResponse)
async def categories_list(request: Request, db: Session = Depends(get_db)):
    categories = db.query(Category).order_by(Category.order).all()
    # 각 카테고리 글 수 집계
    for cat in categories:
        cat._post_count = (
            db.query(func.count(Post.id))
            .filter(Post.category_id == cat.id, Post.status == PostStatus.PUBLISHED)
            .scalar()
        )

    ctx = common_context(request, db)
    ctx.update({
        "page_title": f"카테고리 | {settings.APP_NAME}",
        "categories": categories,
    })
    return templates.TemplateResponse("blog/categories.html", ctx)


# ── 검색 ─────────────────────────────────────────────────────
@router.get("/search", response_class=HTMLResponse)
async def search(
    request: Request,
    q: str = Query("", alias="q"),
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db),
):
    posts = []
    total = 0
    pagination = {}

    if q.strip():
        query = (
            db.query(Post)
            .options(joinedload(Post.category))
            .filter(
                Post.status == PostStatus.PUBLISHED,
                or_(
                    Post.title.ilike(f"%{q}%"),
                    Post.excerpt.ilike(f"%{q}%"),
                    Post.content.ilike(f"%{q}%"),
                )
            )
            .order_by(desc(Post.published_at))
        )
        total = query.count()
        per_page = 9
        posts = query.offset((page - 1) * per_page).limit(per_page).all()
        pagination = paginate(total, page, per_page)

    ctx = common_context(request, db)
    ctx.update({
        "page_title": f"'{q}' 검색 결과 | {settings.APP_NAME}" if q else f"검색 | {settings.APP_NAME}",
        "query": q,
        "posts": posts,
        "total": total,
        "pagination": pagination,
        "current_page": page,
        "format_date_ko": format_date_ko,
    })
    return templates.TemplateResponse("blog/search.html", ctx)


# ── About ────────────────────────────────────────────────────
@router.get("/about", response_class=HTMLResponse)
async def about(request: Request, db: Session = Depends(get_db)):
    ctx = common_context(request, db)
    ctx.update({
        "page_title": f"소개 | {settings.APP_NAME}",
        "meta_description": "두 아이를 키우는 아빠가 대안교육, 어린이 경제교육, 부모의 AI 활용을 기록하는 블로그 Logit을 소개합니다.",
        "canonical_url": f"{settings.BASE_URL}/about",
    })
    return templates.TemplateResponse("blog/about.html", ctx)


# ── 개인정보처리방침 ──────────────────────────────────────────
@router.get("/privacy", response_class=HTMLResponse)
async def privacy(request: Request, db: Session = Depends(get_db)):
    ctx = common_context(request, db)
    ctx.update({
        "page_title": f"개인정보처리방침 | {settings.APP_NAME}",
        "canonical_url": f"{settings.BASE_URL}/privacy",
    })
    return templates.TemplateResponse("blog/privacy.html", ctx)


# ── 광고 고지 ────────────────────────────────────────────────
@router.get("/disclosure", response_class=HTMLResponse)
async def disclosure(request: Request, db: Session = Depends(get_db)):
    ctx = common_context(request, db)
    ctx.update({
        "page_title": f"운영 원칙 & 광고 고지 | {settings.APP_NAME}",
        "canonical_url": f"{settings.BASE_URL}/disclosure",
    })
    return templates.TemplateResponse("blog/disclosure.html", ctx)


# ── 문의 ─────────────────────────────────────────────────────
@router.get("/contact", response_class=HTMLResponse)
async def contact(request: Request, db: Session = Depends(get_db)):
    ctx = common_context(request, db)
    ctx.update({
        "page_title": f"문의하기 | {settings.APP_NAME}",
        "canonical_url": f"{settings.BASE_URL}/contact",
        "contact_sent": False,
    })
    return templates.TemplateResponse("blog/contact.html", ctx)


# ── RSS 피드 ──────────────────────────────────────────────────
@router.get("/rss.xml")
async def rss_feed(db: Session = Depends(get_db)):
    posts = (
        db.query(Post)
        .options(joinedload(Post.category))
        .filter(Post.status == PostStatus.PUBLISHED)
        .order_by(desc(Post.published_at))
        .limit(20)
        .all()
    )

    rss = ET.Element("rss", version="2.0", attrib={
        "xmlns:atom": "http://www.w3.org/2005/Atom",
        "xmlns:content": "http://purl.org/rss/1.0/modules/content/",
    })
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = settings.APP_NAME
    ET.SubElement(channel, "link").text = settings.BASE_URL
    ET.SubElement(channel, "description").text = "두 아이를 키우는 아빠가 아이 교육, 어린이 경제교육, 부모의 AI 활용을 공부하고 기록하는 블로그입니다."
    ET.SubElement(channel, "language").text = "ko"
    ET.SubElement(channel, "lastBuildDate").text = datetime.now(timezone.utc).strftime(
        "%a, %d %b %Y %H:%M:%S +0000"
    )
    atom_link = ET.SubElement(channel, "atom:link")
    atom_link.set("href", f"{settings.BASE_URL}/rss.xml")
    atom_link.set("rel", "self")
    atom_link.set("type", "application/rss+xml")

    for post in posts:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = post.title
        ET.SubElement(item, "link").text = f"{settings.BASE_URL}/post/{post.slug}"
        ET.SubElement(item, "guid", isPermaLink="true").text = f"{settings.BASE_URL}/post/{post.slug}"
        ET.SubElement(item, "description").text = post.excerpt
        if post.published_at:
            ET.SubElement(item, "pubDate").text = post.published_at.strftime(
                "%a, %d %b %Y %H:%M:%S +0900"
            )
        if post.category:
            ET.SubElement(item, "category").text = post.category.name

    xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(rss, encoding="unicode")
    return Response(content=xml_str, media_type="application/rss+xml; charset=utf-8")


# ── sitemap.xml ───────────────────────────────────────────────
@router.get("/sitemap.xml")
async def sitemap(db: Session = Depends(get_db)):
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")

    def add_url(loc, lastmod=None, changefreq="weekly", priority="0.8"):
        url = ET.SubElement(urlset, "url")
        ET.SubElement(url, "loc").text = loc
        if lastmod:
            ET.SubElement(url, "lastmod").text = lastmod if isinstance(lastmod, str) else lastmod.strftime("%Y-%m-%d")
        ET.SubElement(url, "changefreq").text = changefreq
        ET.SubElement(url, "priority").text = priority

    today = datetime.now().strftime("%Y-%m-%d")
    add_url(settings.BASE_URL + "/", today, "daily", "1.0")
    add_url(settings.BASE_URL + "/about", today, "monthly", "0.7")
    add_url(settings.BASE_URL + "/categories", today, "weekly", "0.8")
    add_url(settings.BASE_URL + "/contact", today, "monthly", "0.5")
    add_url(settings.BASE_URL + "/privacy", today, "monthly", "0.3")
    add_url(settings.BASE_URL + "/disclosure", today, "monthly", "0.3")

    categories = db.query(Category).all()
    for cat in categories:
        add_url(f"{settings.BASE_URL}/category/{cat.slug}", today, "daily", "0.9")

    posts = (
        db.query(Post)
        .filter(Post.status == PostStatus.PUBLISHED)
        .order_by(desc(Post.published_at))
        .all()
    )
    for post in posts:
        lastmod = post.updated_at or post.published_at or datetime.now()
        add_url(f"{settings.BASE_URL}/post/{post.slug}", lastmod, "weekly", "0.8")

    xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(urlset, encoding="unicode")
    return Response(content=xml_str, media_type="application/xml; charset=utf-8")


# ── robots.txt ───────────────────────────────────────────────
@router.get("/robots.txt")
async def robots_txt():
    content = f"""User-agent: *
Allow: /
Disallow: /admin/
Disallow: /search?q=

Sitemap: {settings.BASE_URL}/sitemap.xml
"""
    return Response(content=content, media_type="text/plain")


# ── ads.txt ──────────────────────────────────────────────────
@router.get("/ads.txt")
async def ads_txt():
    client = settings.ADSENSE_CLIENT_ID or "pub-XXXXXXXXXXXXXXXXX"
    content = f"google.com, {client}, DIRECT, f08c47fec0942fa0\n"
    return Response(content=content, media_type="text/plain")
