"""
Logit Blog — AI 초안 자동 생성기
매일 새벽 스케줄러가 호출 → OpenAI로 글 초안 생성 → DB 저장 (DRAFT 상태)
"""
import random
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.config import settings
from app.models import Post, Category, Tag, AIGenerationLog, PostStatus
from app.utils import generate_slug, estimate_read_time

logger = logging.getLogger("logit.ai")


# ── 카테고리별 글 주제 풀 ────────────────────────────────────
TOPIC_POOL = {
    "AI 활용": [
        "ChatGPT 프롬프트 엔지니어링 실전 가이드",
        "Claude vs GPT-4o: 실무에서 뭐가 다른가",
        "AI로 블로그 글 쓰기, 제대로 하는 방법",
        "Perplexity AI 실사용 3개월 후기",
        "Notion AI vs ChatGPT: 어느 쪽이 더 유용한가",
        "AI 이미지 생성 도구 비교: Midjourney vs DALL-E vs Stable Diffusion",
        "GPT-4o를 이용한 업무 자동화 5가지 실전 사례",
        "AI 글쓰기 도구, 진짜 원본성을 지키는 방법",
        "로컬 LLM 직접 써보기: Ollama 설치부터 활용까지",
        "AI 코딩 어시스턴트 비교: GitHub Copilot vs Cursor vs Windsurf",
    ],
    "자동화": [
        "Make.com vs n8n: 무료로 쓸 수 있는 자동화 도구 비교",
        "Zapier 무료 플랜으로 할 수 있는 자동화 5가지",
        "Google Sheets + Apps Script로 업무 자동화하기",
        "Python으로 반복 업무 자동화: 실전 스크립트 5개",
        "Notion 자동화 설정 완전 가이드",
        "이메일 자동화로 하루 1시간 아끼는 방법",
        "RSS 피드 자동화로 정보 수집 시스템 만들기",
        "Airtable 자동화로 팀 업무 관리하기",
    ],
    "생산성": [
        "Notion 세컨드 브레인 6개월 사용 후기",
        "포모도로 기법, 실제로 효과 있나? 3개월 실험 결과",
        "GTD(Getting Things Done) 시스템 실전 적용기",
        "아침 루틴이 바꾼 하루: 6개월 기록",
        "딥워크 실천하기: 집중력을 되찾는 구체적인 방법",
        "시간 관리 앱 비교: Todoist vs Things3 vs TickTick",
        "재택근무 생산성 유지하는 현실적인 방법 7가지",
        "주간 리뷰 시스템 만들기: 목표 달성률을 높이는 법",
    ],
    "디지털 도구": [
        "Obsidian으로 지식 관리 시작하는 법: 초보자 가이드",
        "Notion vs Obsidian: 지식 관리 어떤 게 맞나",
        "Figma 무료 플랜으로 할 수 있는 것들",
        "VS Code 필수 확장 프로그램 10개",
        "클라우드 저장소 비교: Google Drive vs Dropbox vs iCloud",
        "Bear vs Craft vs Ulysses: 글쓰기 앱 비교",
        "Arc 브라우저 3개월 사용 후기",
        "Raycast로 맥 생산성 극대화하기",
    ],
    "블로그 운영": [
        "Google Search Console로 블로그 글 순위 올리는 방법",
        "내부 링크 전략으로 체류 시간 늘리기",
        "글 하나에 얼마나 걸려야 할까? SEO 관점에서 본 최적 작성 시간",
        "블로그 카테고리 구조 설계하는 방법",
        "키워드 리서치 무료로 하는 방법",
        "SEO 친화적 제목 쓰는 공식",
        "블로그 방문자 분석: Google Analytics 핵심 지표 읽는 법",
        "콘텐츠 캘린더 만들고 유지하는 방법",
    ],
    "수익화 실험": [
        "AdSense 승인받는 데 걸린 시간과 실제로 효과 있었던 것들",
        "쿠팡 파트너스 실제 수익 공개: 3개월 후기",
        "1인 블로그로 첫 수익 만들기: 현실적인 로드맵",
        "블로그 수익화 전략 비교: AdSense vs 제휴마케팅 vs 디지털 상품",
        "애드센스 RPM 올리는 방법: 광고 배치 최적화",
        "정보 상품 만들기: 전자책 제작부터 판매까지",
    ],
    "노트/정리법": [
        "제텔카스텐 방법론 실전 적용기",
        "Cornell 노트 필기법이 아직도 유효한 이유",
        "디지털 노트 vs 종이 노트: 목적에 따라 선택하는 법",
        "독서 노트 시스템 만들기: 읽은 내용을 실제로 활용하는 법",
        "Obsidian Daily Note 시스템 구축하기",
        "정보 과부하에서 살아남기: 큐레이션 시스템 만드는 법",
    ],
    "비교/리뷰": [
        "맥북 에어 M3 vs 맥북 프로 M3: 개발자/블로거 관점 비교",
        "ChatGPT Plus vs Claude Pro: 월 구독료 낼 가치 있나",
        "유료 노트 앱 비교: Notion vs Craft vs Roam Research",
        "VPN 서비스 비교: 속도와 보안 실측 테스트",
        "스탠딩 데스크 6개월 사용 후기: 허리 통증이 줄었나",
        "무선 키보드 비교: 로지텍 MX Keys vs Apple Magic Keyboard",
    ],
}


SYSTEM_PROMPT = """당신은 'Logit'이라는 한국어 개인 블로그의 콘텐츠 작성자입니다.

[블로그 특성]
- AI, 자동화, 생산성 도구를 직접 써보고 정리하는 실용 정보 블로그
- 빠른 정보보다 신뢰할 수 있는 정보를 추구
- 실제 경험, 비교 데이터, 솔직한 의견을 담는 에디토리얼 스타일
- 운영자의 실제 경험과 관점이 녹아있는 글

[글쓰기 원칙]
- 너무 홍보/마케팅 어조 금지
- 과장 표현, 클릭베이트 금지
- 독자에게 실질적으로 도움되는 정보 중심
- 자연스럽고 읽기 쉬운 한국어
- SEO를 고려하되 스팸성 키워드 반복 금지

[출력 형식 — 반드시 아래 구조를 정확히 따를 것]
제목: (글 제목)
한줄요약: (독자가 읽기 전 핵심을 한 문장으로)
추천독자: (어떤 분께 이 글이 유용한지 1-2줄)
예상읽기시간: (X분)
태그: (태그1, 태그2, 태그3, 태그4, 태그5)
메타설명: (검색 결과에 표시될 150자 이내 설명)

---본문시작---

## 핵심 포인트 3가지
- **포인트 1**: 설명
- **포인트 2**: 설명  
- **포인트 3**: 설명

## 들어가며
(300-400자의 도입부. 왜 이 글을 쓰게 됐는지, 독자가 얻어갈 것이 무엇인지)

## (소제목 1)
(본문. 구체적인 경험과 데이터 포함. 각 섹션 400-600자)

## (소제목 2)
(본문)

## (소제목 3 — 필요 시 추가)
(본문)

## 체크리스트
- [ ] 항목 1
- [ ] 항목 2
- [ ] 항목 3

## 자주 묻는 질문 (FAQ)
**Q. 질문 1?**
A. 답변 1

**Q. 질문 2?**
A. 답변 2

## 마치며
(200-300자의 마무리. 핵심 메시지 재강조, 독자 행동 유도)

---본문끝---"""


def parse_ai_response(response_text: str, category_name: str) -> dict:
    """AI 응답 텍스트를 파싱해서 구조화된 데이터로 변환"""
    lines = response_text.strip().split("\n")
    data = {
        "title": "",
        "excerpt": "",
        "recommend_for": "",
        "read_time": 5,
        "tags": [],
        "meta_description": "",
        "content_markdown": "",
    }

    body_lines = []
    in_body = False

    for line in lines:
        if line.strip() == "---본문시작---":
            in_body = True
            continue
        if line.strip() == "---본문끝---":
            in_body = False
            continue

        if in_body:
            body_lines.append(line)
            continue

        if line.startswith("제목:"):
            data["title"] = line.replace("제목:", "").strip()
        elif line.startswith("한줄요약:"):
            data["excerpt"] = line.replace("한줄요약:", "").strip()
        elif line.startswith("추천독자:"):
            data["recommend_for"] = line.replace("추천독자:", "").strip()
        elif line.startswith("예상읽기시간:"):
            try:
                t = line.replace("예상읽기시간:", "").strip().replace("분", "").strip()
                data["read_time"] = int(t)
            except Exception:
                data["read_time"] = 5
        elif line.startswith("태그:"):
            raw = line.replace("태그:", "").strip()
            data["tags"] = [t.strip() for t in raw.split(",") if t.strip()]
        elif line.startswith("메타설명:"):
            data["meta_description"] = line.replace("메타설명:", "").strip()

    data["content_markdown"] = "\n".join(body_lines).strip()
    return data


def markdown_to_html(md: str) -> str:
    """
    Markdown → HTML 변환 (외부 라이브러리 없이 기본 변환)
    실제 운영 시 python-markdown 또는 mistune 사용 권장
    """
    import re
    html = md

    # 체크리스트
    html = re.sub(r"- \[ \] (.+)", r'<li class="checklist-item"><span class="check-box"></span>\1</li>', html)
    html = re.sub(r"- \[x\] (.+)", r'<li class="checklist-item checked"><span class="check-box">✓</span>\1</li>', html)

    # FAQ 패턴
    html = re.sub(r"\*\*Q\. (.+?)\*\*", r'<div class="faq-question">\1</div>', html)
    html = re.sub(r"^A\. (.+)$", r'<div class="faq-answer">\1</div>', html, flags=re.MULTILINE)

    # h2, h3
    html = re.sub(r"^## (.+)$", r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r"^### (.+)$", r'<h3>\1</h3>', html, flags=re.MULTILINE)

    # Bold
    html = re.sub(r"\*\*(.+?)\*\*", r'<strong>\1</strong>', html)

    # Bullet list
    lines = html.split("\n")
    result = []
    in_ul = False
    in_checklist = False
    for line in lines:
        if line.startswith("- ") and "checklist-item" not in line:
            if not in_ul:
                result.append("<ul>")
                in_ul = True
            result.append(f"<li>{line[2:]}</li>")
        else:
            if in_ul:
                result.append("</ul>")
                in_ul = False
            result.append(line)
    if in_ul:
        result.append("</ul>")
    html = "\n".join(result)

    # Paragraph (빈 줄로 구분된 텍스트)
    paragraphs = re.split(r"\n\n+", html)
    processed = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        if p.startswith("<h") or p.startswith("<ul") or p.startswith("<li") \
                or p.startswith("<div") or p.startswith("<ol"):
            processed.append(p)
        else:
            processed.append(f"<p>{p}</p>")
    html = "\n".join(processed)

    return html


async def generate_ai_draft(db: Session, category=None, category_slug: Optional[str] = None) -> Optional[Post]:
    """
    OpenAI API를 호출해 글 초안을 생성하고 DB에 저장
    category_slug가 None이면 랜덤 카테고리 선택
    """
    if not settings.OPENAI_API_KEY:
        logger.warning("[AI] OPENAI_API_KEY가 설정되지 않았습니다. 더미 초안을 생성합니다.")
        return await generate_dummy_draft(db)

    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    # 카테고리 선택
    if category is None:
        if category_slug:
            category = db.query(Category).filter(Category.slug == category_slug).first()
        else:
            categories = db.query(Category).all()
            if not categories:
                logger.error("[AI] 카테고리가 없습니다.")
                return None
            category = random.choice(categories)
    elif isinstance(category, str):
        category = db.query(Category).filter(Category.slug == category).first()



    category_name = category.name if category else random.choice(settings.AI_DRAFT_CATEGORIES)

    # 주제 선택
    topics = TOPIC_POOL.get(category_name, [])
    if topics:
        # DB에 이미 있는 주제 제외
        existing_titles = [p.title for p in db.query(Post.title).all()]
        available = [t for t in topics if t not in existing_titles]
        topic = random.choice(available) if available else random.choice(topics)
    else:
        topic = f"{category_name} 실전 가이드"

    user_prompt = f"""카테고리: {category_name}
주제: {topic}

위 주제로 블로그 글 초안을 작성해주세요.
글자 수는 2000-3000자 내외로, 실제 경험과 구체적인 정보가 담긴 글로 작성해주세요."""

    log = AIGenerationLog(
        category=category_name,
        prompt=user_prompt,
        model=settings.AI_MODEL,
        status="processing",
    )
    db.add(log)
    db.commit()

    try:
        response = await client.chat.completions.create(
            model=settings.AI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.8,
            max_tokens=4000,
        )

        raw_text = response.choices[0].message.content
        tokens_used = response.usage.total_tokens

        parsed = parse_ai_response(raw_text, category_name)

        if not parsed["title"]:
            parsed["title"] = topic

        # HTML 변환
        content_html = markdown_to_html(parsed["content_markdown"])

        # 슬러그 생성
        slug = generate_slug(parsed["title"])

        # 태그 생성/조회
        tags = []
        for tag_name in parsed["tags"][:5]:
            tag_slug = generate_slug(tag_name)
            tag = db.query(Tag).filter(Tag.slug == tag_slug).first()
            if not tag:
                tag = Tag(name=tag_name, slug=tag_slug)
                db.add(tag)
            tags.append(tag)
        db.flush()

        # 글 저장
        post = Post(
            title=parsed["title"],
            slug=slug,
            excerpt=parsed["excerpt"] or parsed["title"],
            content=content_html,
            content_markdown=parsed["content_markdown"],
            meta_title=parsed["title"],
            meta_description=parsed["meta_description"] or parsed["excerpt"],
            category_id=category.id if category else None,
            status=PostStatus.DRAFT,
            is_ai_draft=True,
            ai_prompt_used=user_prompt,
            read_time_min=parsed["read_time"],
            tags=tags,
        )
        db.add(post)

        # 로그 업데이트
        log.status = "success"
        log.tokens_used = tokens_used
        db.flush()
        log.post_id = post.id

        db.commit()
        db.refresh(post)

        logger.info(f"[AI] 글 초안 생성 완료: '{post.title}' (토큰: {tokens_used})")
        return post

    except Exception as e:
        log.status = "failed"
        log.error_msg = str(e)
        db.commit()
        logger.error(f"[AI] 글 생성 실패: {e}")
        return None


async def generate_dummy_draft(db: Session) -> Optional[Post]:
    """OpenAI API 키가 없을 때 더미 초안 생성 (테스트용)"""
    category = db.query(Category).first()
    if not category:
        return None

    title = f"[AI 초안 예시] {category.name} 실전 가이드 — {datetime.now().strftime('%m월 %d일')}"
    slug = generate_slug(title)

    content_md = """## 핵심 포인트 3가지
- **포인트 1**: 이 글은 AI가 자동 생성한 더미 초안입니다
- **포인트 2**: OpenAI API 키를 설정하면 실제 글이 생성됩니다
- **포인트 3**: 관리자 페이지에서 수정 후 발행하세요

## 들어가며
이 글은 OpenAI API 키 없이 생성된 테스트 초안입니다.
실제 운영 시 `.env` 파일에 `OPENAI_API_KEY`를 설정해주세요.

## 본문 예시

여기에 실제 내용이 들어갑니다. AI가 생성한 초안을 운영자가 검수하고 수정한 뒤 발행합니다.

관리자 페이지에서 이 글을 열어 내용을 수정하고 발행 버튼을 클릭하세요.

## 마치며
`.env` 파일에 `OPENAI_API_KEY=sk-...`를 입력하면 매일 아침 실제 AI 초안이 생성됩니다."""

    post = Post(
        title=title,
        slug=slug,
        excerpt="AI가 자동 생성한 테스트 초안입니다. 수정 후 발행하세요.",
        content=markdown_to_html(content_md),
        content_markdown=content_md,
        meta_title=title,
        meta_description="AI가 자동 생성한 테스트 초안입니다.",
        category_id=category.id,
        status=PostStatus.DRAFT,
        is_ai_draft=True,
        ai_prompt_used="(더미 초안 — API 키 없음)",
        read_time_min=3,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    logger.info(f"[AI] 더미 초안 생성: '{post.title}'")
    return post
