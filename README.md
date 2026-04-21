# Logit — 실행하는 사람의 기록

> AI 활용, 자동화, 생산성, 디지털 도구를 직접 써보고 정리하는 개인 블로그  
> Google AdSense 수익화를 목표로 하는 독립 운영 콘텐츠 블로그

---

## 🏷️ 브랜드 이름 3안 및 소개 문구

### 1안: **Logit** (추천 ⭐)
- 도메인: `logit.kr`
- 의미: Log(기록) + It(실행) 합성어. "실행을 기록한다"
- 소개 문구: *"실행하는 사람의 기록이 쌓이는 곳"*
- 특징: 간결하고 영문 혼용이 자연스러우며, 기억하기 쉬움

### 2안: **Actlog** (액트로그)
- 도메인: `actlog.kr`
- 의미: Action(실행) + Log(기록)
- 소개 문구: *"쓰고, 실행하고, 기록합니다"*
- 특징: 행동 지향적 이미지, 실험과 기록의 느낌

### 3안: **Clearlog** (클리어로그)
- 도메인: `clearlog.kr`
- 의미: Clear(명확한) + Log(기록) — "명확하게 정리하는 기록"
- 소개 문구: *"복잡한 디지털 세상을 명확하게 정리합니다"*
- 특징: 정리·아카이빙 이미지 강조, 신뢰감 높음

---

## 📁 프로젝트 구조

```
logit/
├── index.html              ← 홈 페이지
├── post.html               ← 글 상세 페이지 (예시 글 포함)
├── category.html           ← 카테고리 목록 페이지
├── about.html              ← About 페이지
├── privacy.html            ← 개인정보처리방침
├── disclosure.html         ← 운영 원칙 & 광고 고지
├── contact.html            ← 문의 페이지
├── search.html             ← 검색 결과 페이지
├── 404.html                ← 404 에러 페이지
├── robots.txt              ← 검색엔진 크롤링 설정
├── sitemap.xml             ← XML 사이트맵
├── ads.txt                 ← AdSense 광고 인증 파일
├── rss.xml                 ← RSS 피드
├── favicon.svg             ← 파비콘 (SVG)
├── CONTENT_TEMPLATE.md     ← AI+사람 글쓰기 템플릿
├── css/
│   └── style.css           ← 메인 스타일시트
└── js/
    └── main.js             ← 메인 JavaScript
```

---

## 🚀 구현된 기능

### 페이지 구성
- ✅ 홈 — 히어로, 최신 글, 인기 글, 에디터 추천, 카테고리, 운영자 소개
- ✅ 글 상세 — 브레드크럼, 목차(TOC), 본문 서식, FAQ, 작성자 카드, 관련 글
- ✅ 카테고리 — 필터, 페이지네이션, 사이드바
- ✅ About — 운영자 소개, 운영 철학, AI 글쓰기 입장 공개
- ✅ 개인정보처리방침 — AdSense 심사 요건 충족
- ✅ 운영원칙/광고고지 — 제휴마케팅, AdSense, 협찬 정책 공시
- ✅ Contact — 문의 폼 (validation 포함)
- ✅ 검색 — 실시간 검색, URL 파라미터 지원
- ✅ 404 — 추천 글 포함

### SEO & 기술
- ✅ JSON-LD 구조화 데이터 (Blog, Article, BreadcrumbList)
- ✅ Open Graph / Twitter Card 메타 태그
- ✅ canonical URL
- ✅ robots.txt
- ✅ sitemap.xml
- ✅ RSS 피드 (rss.xml)
- ✅ ads.txt (AdSense 퍼블리셔 ID 입력란 준비)
- ✅ 읽기 진행 표시바
- ✅ 목차(TOC) IntersectionObserver 기반 활성화
- ✅ 검색 오버레이 (실시간 결과)
- ✅ 반응형 디자인 (모바일 최적화)
- ✅ 맨 위로 버튼
- ✅ 외부 링크 자동 rel="noopener noreferrer"
- ✅ 이미지 지연 로딩 지원
- ✅ 인쇄 스타일

### 광고 슬롯
- ✅ 본문 상단 / 중간 / 하단 광고 슬롯 (`ad-slot-inline`)
- ✅ 사이드바 광고 슬롯 300x250, 300x600
- ✅ 홈 페이지 중간 광고 슬롯
- 모든 슬롯은 현재 빈 상태 — AdSense 코드 삽입만 하면 즉시 활성화

### 콘텐츠 UI
- ✅ 요약 박스 (article-summary)
- ✅ callout 박스 (tip, warning, info, danger)
- ✅ 체크리스트 (checklist)
- ✅ FAQ 아코디언
- ✅ 비교 표 (table)
- ✅ 코드 블록 + 복사 버튼
- ✅ 인용구 (blockquote)
- ✅ 태그 (tag)

---

## 🔧 배포 가이드 (Render.com)

### 정적 사이트로 배포

1. GitHub에 이 프로젝트 레포 생성 후 push
2. [render.com](https://render.com) 가입 및 로그인
3. "New +" → "Static Site" 선택
4. GitHub 레포 연결
5. 설정:
   - **Build Command**: 없음 (정적 사이트)
   - **Publish Directory**: `.` (루트)
6. Deploy 클릭

### 커스텀 도메인 연결 (Render)
1. Render 대시보드 → 해당 서비스 → "Settings" → "Custom Domains"
2. 도메인 추가 (예: `logit.kr`)
3. DNS 설정: CNAME → `<your-site>.onrender.com`
4. HTTPS는 자동 발급

### 404 페이지 설정 (Render)
Render 대시보드 → Redirects/Rewrites 탭 → 아래 추가:
```
Source: /*
Destination: /404.html
Type: rewrite (404 응답 코드)
```

---

## 📊 Google AdSense 연동 방법

### 1단계: 사이트 소유 확인 (ads.txt)
- `ads.txt` 파일에 퍼블리셔 ID 입력
- `google.com, pub-XXXXXXXXXXXXXXXXX, DIRECT, f08c47fec0942fa0`

### 2단계: AdSense 코드 삽입 (head 영역)
모든 HTML 파일의 `<head>` 내 아래 주석 부분을 활성화:
```html
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXX" crossorigin="anonymous"></script>
```

### 3단계: 광고 슬롯 활성화
광고를 표시할 위치의 `ad-slot-inline` 또는 `ad-slot` div 내부에 AdSense `<ins>` 태그 삽입:
```html
<ins class="adsbygoogle"
     style="display:block"
     data-ad-client="ca-pub-XXXXXXXXXX"
     data-ad-slot="XXXXXXXXXX"
     data-ad-format="auto"
     data-full-width-responsive="true"></ins>
<script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
```

---

## 📊 Google Analytics 연동

`index.html`과 모든 페이지의 `<head>`에 삽입:
```html
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

---

## 📮 Contact 폼 연동 (실제 이메일 발송)

현재 폼은 JavaScript로만 구현되어 있습니다. 실제 이메일 발송을 위해:

### FormSpree (추천 - 무료)
```html
<form action="https://formspree.io/f/XXXXXXXX" method="POST">
```

### EmailJS (클라이언트 사이드)
```javascript
emailjs.send('service_id', 'template_id', formData, 'user_id');
```

---

## 🔮 향후 개발 계획

### 단기 (1~3개월)
- [ ] 실제 글 발행 시작 (주 2~3편 목표)
- [ ] Google Search Console 등록
- [ ] Google Analytics 데이터 수집 시작
- [ ] AdSense 신청

### 중기 (3~6개월)
- [ ] 태그 페이지 구현 (`/tag/[tag-name]`)
- [ ] 뉴스레터 연동 (Mailchimp 또는 ConvertKit)
- [ ] 다크 모드 지원
- [ ] 소셜 공유 기능 완성

### 장기 (6개월+)
- [ ] 검색 기능 서버사이드 구현 (Algolia 또는 자체 API)
- [ ] CMS 연동 고려 (Contentful, Sanity 등)
- [ ] 성능 최적화 (Lighthouse 95+ 목표)
- [ ] 댓글 시스템 추가 (Giscus 등)

---

## 🎯 AdSense 승인 준비 체크리스트

AdSense 신청 전 확인 사항:

- [ ] 콘텐츠 최소 15~20개 이상 발행
- [ ] 각 글이 500자 이상의 실질적 정보 포함
- [ ] About 페이지 명확히 작성
- [ ] Privacy Policy 페이지 존재
- [ ] Contact 페이지 존재
- [ ] ads.txt 파일 루트에 배치
- [ ] 모든 페이지 navigation 정상 작동
- [ ] 저작권 침해 콘텐츠 없음
- [ ] 성인/도박/불법 콘텐츠 없음
- [ ] 사이트 로딩 속도 양호
- [ ] 모바일 반응형 정상 작동
- [ ] 운영 원칙/광고 고지 페이지 존재

---

## 📝 콘텐츠 운영 가이드

`CONTENT_TEMPLATE.md` 파일을 참고하세요.  
AI 초안 생성 → 사람 편집 → 검수 → 발행 프로세스가 포함되어 있습니다.

---

## ⚙️ 기술 스택

- **HTML5** — 시맨틱 마크업, aria 접근성
- **CSS3** — CSS 변수, Grid, Flexbox, 반응형
- **Vanilla JavaScript** — 라이브러리 의존성 없음 (성능 최적화)
- **Google Fonts** — Noto Sans KR
- **배포** — Render.com 정적 사이트

---

*© 2025 Logit. 운영자가 직접 소유·운영하는 독립 블로그입니다.*
