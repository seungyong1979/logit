"""
Logit Blog — 공통 유틸리티 함수
"""
import re
import math
from datetime import datetime
from typing import Optional, Dict
from slugify import slugify


def generate_slug(text: str, max_length: int = 100) -> str:
    """한글 포함 텍스트를 URL 슬러그로 변환"""
    slug = slugify(text, allow_unicode=False, separator="-")
    if not slug:
        slug = f"post-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    return slug[:max_length]


def estimate_read_time(content: str) -> int:
    """본문 내용으로 예상 읽기 시간 계산 (분)"""
    text = re.sub(r"<[^>]+>", "", content)
    char_count = len(text.replace(" ", ""))
    minutes = math.ceil(char_count / 500)
    return max(1, min(minutes, 60))


def format_date_ko(dt: Optional[datetime]) -> str:
    """datetime → 한국어 날짜 문자열"""
    if not dt:
        return ""
    return dt.strftime("%Y년 %m월 %d일").replace(" 0", " ")


def format_date_iso(dt: Optional[datetime]) -> str:
    """datetime → ISO 8601 문자열"""
    if not dt:
        return ""
    return dt.isoformat()


def truncate(text: str, length: int = 150, suffix: str = "...") -> str:
    """텍스트 자르기"""
    if not text:
        return ""
    if len(text) <= length:
        return text
    return text[:length].rstrip() + suffix


def strip_html(text: str) -> str:
    """HTML 태그 제거"""
    return re.sub(r"<[^>]+>", "", text or "")


def paginate(total: int, page: int, per_page: int = 12) -> Dict:
    """페이지네이션 정보 딕셔너리 반환"""
    total_pages = math.ceil(total / per_page) if total > 0 else 1
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages,
    }
