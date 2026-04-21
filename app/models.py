"""
Logit Blog — SQLAlchemy 데이터 모델
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean,
    DateTime, ForeignKey, Table, Enum
)
from sqlalchemy.orm import relationship
from app.database import Base
import enum


# ── 글-태그 다대다 연결 테이블 ──────────────────────────────
post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", Integer, ForeignKey("posts.id"), primary_key=True),
    Column("tag_id",  Integer, ForeignKey("tags.id"),  primary_key=True),
)


class PostStatus(str, enum.Enum):
    DRAFT     = "draft"      # AI 초안 (미공개)
    REVIEW    = "review"     # 검수 중
    PUBLISHED = "published"  # 발행됨
    ARCHIVED  = "archived"   # 보관


# ── 카테고리 ────────────────────────────────────────────────
class Category(Base):
    __tablename__ = "categories"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(100), unique=True, nullable=False)
    slug        = Column(String(120), unique=True, nullable=False, index=True)
    description = Column(String(300), default="")
    icon        = Column(String(10), default="📝")   # 이모지
    color       = Column(String(20), default="#2563eb")
    order       = Column(Integer, default=0)
    created_at  = Column(DateTime, default=datetime.utcnow)

    posts = relationship("Post", back_populates="category")

    @property
    def post_count(self):
        return len([p for p in self.posts if p.status == PostStatus.PUBLISHED])


# ── 태그 ────────────────────────────────────────────────────
class Tag(Base):
    __tablename__ = "tags"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(80), unique=True, nullable=False)
    slug       = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    posts = relationship("Post", secondary=post_tags, back_populates="tags")


# ── 글 ──────────────────────────────────────────────────────
class Post(Base):
    __tablename__ = "posts"

    id               = Column(Integer, primary_key=True, index=True)
    title            = Column(String(300), nullable=False)
    slug             = Column(String(350), unique=True, nullable=False, index=True)
    excerpt          = Column(String(500), default="")      # 한줄 요약
    content          = Column(Text, default="")             # 본문 (HTML)
    content_markdown = Column(Text, default="")             # 본문 (Markdown, AI 초안용)

    # SEO
    meta_title       = Column(String(300), default="")
    meta_description = Column(String(500), default="")
    og_image         = Column(String(500), default="")

    # 분류
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    category    = relationship("Category", back_populates="posts")
    tags        = relationship("Tag", secondary=post_tags, back_populates="posts")

    # 상태
    status           = Column(Enum(PostStatus), default=PostStatus.DRAFT, index=True)
    is_featured      = Column(Boolean, default=False)
    is_ai_draft      = Column(Boolean, default=False)   # AI가 생성한 초안 여부
    ai_prompt_used   = Column(Text, default="")         # 사용된 프롬프트 기록

    # 통계
    view_count       = Column(Integer, default=0)
    read_time_min    = Column(Integer, default=5)       # 예상 읽기 시간(분)

    # 날짜
    created_at       = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at     = Column(DateTime, nullable=True, index=True)


# ── 관리자 ──────────────────────────────────────────────────
class Admin(Base):
    __tablename__ = "admins"

    id              = Column(Integer, primary_key=True, index=True)
    email           = Column(String(200), unique=True, nullable=False, index=True)
    hashed_password = Column(String(300), nullable=False)
    name            = Column(String(100), default="운영자")
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime, default=datetime.utcnow)
    last_login      = Column(DateTime, nullable=True)


# ── AI 생성 로그 ────────────────────────────────────────────
class AIGenerationLog(Base):
    __tablename__ = "ai_generation_logs"

    id           = Column(Integer, primary_key=True, index=True)
    post_id      = Column(Integer, ForeignKey("posts.id"), nullable=True)
    category     = Column(String(100), default="")
    prompt       = Column(Text, default="")
    tokens_used  = Column(Integer, default=0)
    model        = Column(String(50), default="")
    status       = Column(String(50), default="success")  # success / failed
    error_msg    = Column(Text, default="")
    created_at   = Column(DateTime, default=datetime.utcnow)
