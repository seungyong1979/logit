"""
Logit Blog — AI 이미지 생성 + Cloudinary 업로드
DALL-E 3로 블로그 대표 이미지 생성 후 Cloudinary에 저장
"""
import logging
import httpx
import hashlib
from datetime import datetime
from typing import Optional
from app.config import settings

logger = logging.getLogger("logit.image")


# ── 이미지 프롬프트 생성 ─────────────────────────────────────
def build_image_prompt(title: str, category_name: str) -> str:
    """글 제목과 카테고리로 DALL-E 이미지 프롬프트 생성"""

    category_style = {
        "AI 활용": "futuristic digital brain with glowing neural networks, blue and purple tones",
        "자동화": "interconnected gears and workflow arrows, clean minimal design, teal colors",
        "생산성": "clean desk with organized tools, warm lighting, productive atmosphere",
        "디지털 도구": "modern app interface on screen, flat design icons, vibrant colors",
        "블로그 운영": "content creation workspace, laptop with analytics charts, green growth theme",
        "수익화 실험": "upward trending graph with coins, gold and green colors, success theme",
        "노트/정리법": "organized notebook and digital notes side by side, minimal clean style",
        "비교/리뷰": "two items being compared on a balanced scale, clean white background",
    }

    style = category_style.get(category_name, "modern digital technology, clean minimal design")

    prompt = (
        f"A professional blog header image for an article titled '{title}'. "
        f"Visual style: {style}. "
        f"Wide landscape format, no text overlay, photorealistic or high-quality illustration, "
        f"suitable for a Korean tech blog. "
        f"Clean composition, high contrast, visually engaging. "
        f"Do not include any text or letters in the image."
    )
    return prompt


# ── Cloudinary 업로드 ────────────────────────────────────────
async def upload_to_cloudinary(image_url: str, post_slug: str) -> Optional[str]:
    """
    DALL-E가 생성한 임시 URL 이미지를 Cloudinary에 영구 저장
    반환값: Cloudinary CDN URL 또는 None
    """
    if not all([
        settings.CLOUDINARY_CLOUD_NAME,
        settings.CLOUDINARY_API_KEY,
        settings.CLOUDINARY_API_SECRET,
    ]):
        logger.warning("[Image] Cloudinary 설정이 없습니다. DALL-E URL을 그대로 사용합니다.")
        return image_url  # Cloudinary 없으면 DALL-E URL 임시 사용

    import base64
    import hmac
    import time

    cloud_name = settings.CLOUDINARY_CLOUD_NAME
    api_key = settings.CLOUDINARY_API_KEY
    api_secret = settings.CLOUDINARY_API_SECRET

    timestamp = int(time.time())
    public_id = f"logit/posts/{post_slug}"

    # 서명 생성
    sign_str = f"public_id={public_id}&timestamp={timestamp}{api_secret}"
    signature = hashlib.sha1(sign_str.encode()).hexdigest()

    upload_url = f"https://api.cloudinary.com/v1_1/{cloud_name}/image/upload"

    data = {
        "file": image_url,
        "public_id": public_id,
        "timestamp": str(timestamp),
        "api_key": api_key,
        "signature": signature,
        "folder": "logit/posts",
        "transformation": "c_fill,w_1200,h_630,q_auto,f_webp",
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(upload_url, data=data)
            resp.raise_for_status()
            result = resp.json()
            cdn_url = result.get("secure_url", "")
            logger.info(f"[Image] Cloudinary 업로드 완료: {cdn_url}")
            return cdn_url
    except Exception as e:
        logger.error(f"[Image] Cloudinary 업로드 실패: {e}")
        return image_url  # 실패 시 DALL-E URL 반환


# ── 메인 함수: 이미지 생성 + 업로드 ─────────────────────────
async def generate_post_image(title: str, category_name: str, post_slug: str) -> Optional[str]:
    """
    DALL-E 3로 블로그 대표 이미지 생성 후 Cloudinary 저장
    반환값: 최종 이미지 URL 또는 None
    """
    if not settings.OPENAI_API_KEY:
        logger.warning("[Image] OPENAI_API_KEY가 없어 이미지 생성을 건너뜁니다.")
        return None

    if not settings.AI_IMAGE_ENABLED:
        logger.info("[Image] AI 이미지 생성이 비활성화되어 있습니다.")
        return None

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        prompt = build_image_prompt(title, category_name)
        logger.info(f"[Image] DALL-E 이미지 생성 시작: '{title}'")

        response = await client.images.generate(
            model=settings.AI_IMAGE_MODEL,  # dall-e-3
            prompt=prompt,
            size=settings.AI_IMAGE_SIZE,    # 1792x1024
            quality="standard",
            n=1,
        )

        dalle_url = response.data[0].url
        logger.info(f"[Image] DALL-E 생성 완료, Cloudinary 업로드 중...")

        # Cloudinary에 영구 저장
        final_url = await upload_to_cloudinary(dalle_url, post_slug)
        return final_url

    except Exception as e:
        logger.error(f"[Image] 이미지 생성 실패: {e}")
        return None
