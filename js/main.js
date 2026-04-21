/**
 * Logit — 메인 JavaScript
 * 검색, 모바일 메뉴, 읽기 진행바, TOC, FAQ 등 UI 인터랙션
 */

'use strict';

/* ============================================================
   DOM 로드 완료 후 실행
============================================================ */
document.addEventListener('DOMContentLoaded', () => {
  initSearchOverlay();
  initMobileMenu();
  initBackToTop();
  initReadingProgress();
  initFAQ();
  initTOC();
  initCategoryBarScroll();
  initSearchPage();
  initExternalLinks();
  initCodeCopy();
  initLazyImages();
});

/* ============================================================
   검색 오버레이
============================================================ */
// 샘플 포스트 데이터 (실제 운영 시 API 또는 JSON으로 대체)
const POSTS_DATA = [
  {
    title: 'ChatGPT로 블로그 글 쓰기: 제대로 하는 방법과 절대 하면 안 되는 것들',
    category: 'AI 활용',
    excerpt: 'AI 글쓰기 도구를 단순 복붙하면 오히려 역효과입니다. 6개월간 직접 운영하며 정리한 AI + 사람 협업 글쓰기 프레임워크를 공개합니다.',
    url: 'post.html',
    tags: ['ChatGPT', 'AI', '글쓰기', '블로그']
  },
  {
    title: 'Make.com vs n8n: 무료로 쓸 수 있는 자동화 도구 실제 비교',
    category: '자동화',
    excerpt: '두 도구를 3개월 이상 직접 써본 후기. 어떤 상황에 뭘 써야 하는지 솔직하게 정리했습니다.',
    url: 'post.html',
    tags: ['Make.com', 'n8n', '자동화']
  },
  {
    title: 'Notion 세컨드 브레인 6개월 사용 후기: 진짜 효과 있나?',
    category: '생산성',
    excerpt: '화려한 템플릿보다 단순한 구조가 더 오래 지속됩니다.',
    url: 'post.html',
    tags: ['Notion', '생산성', '지식관리']
  },
  {
    title: 'AdSense 승인받는 데 걸린 시간과 실제로 효과 있었던 것들',
    category: '수익화 실험',
    excerpt: '광고 붙이기 전 준비해야 할 것들, 승인까지 걸린 시간, 첫 달 수익 공개.',
    url: 'post.html',
    tags: ['AdSense', '블로그수익', '수익화']
  },
  {
    title: 'Obsidian으로 지식 관리 시작하는 법: 초보자 가이드',
    category: '노트/정리법',
    excerpt: '플러그인 없이 시작하는 Obsidian 기초 가이드.',
    url: 'post.html',
    tags: ['Obsidian', '노트', '지식관리']
  },
  {
    title: 'Claude vs GPT-4o: 실제 업무에서 써보니 이게 다르더라',
    category: 'AI 활용',
    excerpt: '두 모델의 실제 사용성 차이를 업무 유형별로 정리했습니다.',
    url: 'post.html',
    tags: ['Claude', 'GPT-4o', 'AI', '비교']
  },
  {
    title: 'Perplexity AI가 Google 검색을 대체할 수 있을까?',
    category: '비교/리뷰',
    excerpt: '3개월 실사용 비교. 검색 패턴에 따라 다릅니다.',
    url: 'post.html',
    tags: ['Perplexity', 'AI검색', 'Google']
  },
  {
    title: 'Google Search Console로 내 블로그 글 순위 올리는 방법',
    category: '블로그 운영',
    excerpt: '데이터를 보는 방법부터 실제 글 개선까지.',
    url: 'post.html',
    tags: ['SEO', 'Search Console', '블로그운영']
  },
  {
    title: 'Zapier 무료 플랜으로 할 수 있는 업무 자동화 5가지',
    category: '자동화',
    excerpt: '유료 전환 없이도 충분히 쓸 만한 자동화 시나리오.',
    url: 'post.html',
    tags: ['Zapier', '자동화', '무료플랜']
  },
  {
    title: '1인 블로그로 첫 수익 만들기: 현실적인 6개월 로드맵',
    category: '수익화 실험',
    excerpt: '0에서 시작해 첫 수익까지의 현실적인 과정을 공유합니다.',
    url: 'post.html',
    tags: ['블로그수익', '수익화', '로드맵']
  }
];

function initSearchOverlay() {
  const searchToggle = document.getElementById('searchToggle');
  const searchOverlay = document.getElementById('searchOverlay');
  const searchInput = document.getElementById('searchInput');
  const searchResults = document.getElementById('searchResults');

  if (!searchToggle || !searchOverlay) return;

  // 검색 열기
  searchToggle.addEventListener('click', () => {
    searchOverlay.classList.add('active');
    searchToggle.setAttribute('aria-expanded', 'true');
    setTimeout(() => searchInput?.focus(), 100);
    document.body.style.overflow = 'hidden';
  });

  // 오버레이 클릭으로 닫기
  searchOverlay.addEventListener('click', (e) => {
    if (e.target === searchOverlay) closeSearch();
  });

  // ESC로 닫기
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeSearch();
  });

  // 검색어 입력 처리
  searchInput?.addEventListener('input', debounce((e) => {
    const query = e.target.value.trim();
    if (query.length < 2) {
      searchResults.innerHTML = '';
      return;
    }
    renderSearchResults(query, searchResults);
  }, 200));

  // 엔터로 검색 페이지 이동
  searchInput?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      const query = e.target.value.trim();
      if (query) {
        window.location.href = `search.html?q=${encodeURIComponent(query)}`;
      }
    }
  });

  function closeSearch() {
    searchOverlay.classList.remove('active');
    searchToggle.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
    if (searchInput) searchInput.value = '';
    if (searchResults) searchResults.innerHTML = '';
  }
}

function renderSearchResults(query, container) {
  const q = query.toLowerCase();
  const results = POSTS_DATA.filter(post =>
    post.title.toLowerCase().includes(q) ||
    post.excerpt.toLowerCase().includes(q) ||
    post.tags.some(t => t.toLowerCase().includes(q)) ||
    post.category.toLowerCase().includes(q)
  ).slice(0, 5);

  if (results.length === 0) {
    container.innerHTML = `<p style="padding: 1rem; color: var(--color-text-muted); font-size: var(--text-sm); text-align:center;">"${query}"에 대한 검색 결과가 없습니다.</p>`;
    return;
  }

  container.innerHTML = results.map(post => `
    <a href="${post.url}" class="search-result-item">
      <div>
        <div class="result-category">${post.category}</div>
        <div class="result-title">${highlightQuery(post.title, query)}</div>
        <div class="result-excerpt">${post.excerpt.slice(0, 80)}...</div>
      </div>
    </a>
  `).join('');
}

function highlightQuery(text, query) {
  const regex = new RegExp(`(${query})`, 'gi');
  return text.replace(regex, '<mark style="background:var(--color-primary-light);color:var(--color-primary);border-radius:2px;">$1</mark>');
}

/* ============================================================
   모바일 메뉴
============================================================ */
function initMobileMenu() {
  const toggle = document.getElementById('mobileMenuToggle');
  const nav = document.getElementById('mobileNav');

  if (!toggle || !nav) return;

  toggle.addEventListener('click', () => {
    const isOpen = nav.classList.toggle('active');
    toggle.setAttribute('aria-expanded', isOpen.toString());
    nav.setAttribute('aria-hidden', (!isOpen).toString());
    document.body.style.overflow = isOpen ? 'hidden' : '';
  });

  // 메뉴 링크 클릭 시 닫기
  nav.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      nav.classList.remove('active');
      toggle.setAttribute('aria-expanded', 'false');
      nav.setAttribute('aria-hidden', 'true');
      document.body.style.overflow = '';
    });
  });
}

/* ============================================================
   맨 위로 버튼
============================================================ */
function initBackToTop() {
  const btn = document.getElementById('backToTop');
  if (!btn) return;

  const toggleVisibility = () => {
    if (window.scrollY > 400) {
      btn.classList.add('visible');
    } else {
      btn.classList.remove('visible');
    }
  };

  window.addEventListener('scroll', throttle(toggleVisibility, 100), { passive: true });

  btn.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
}

/* ============================================================
   읽기 진행 바
============================================================ */
function initReadingProgress() {
  const progressBar = document.getElementById('readingProgress');
  if (!progressBar) return;

  const articleBody = document.querySelector('.article-body');
  if (!articleBody) return; // 홈/목록 페이지에선 숨김

  const updateProgress = () => {
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    const scrolled = window.scrollY;
    const progress = docHeight > 0 ? (scrolled / docHeight) * 100 : 0;
    progressBar.style.width = `${Math.min(progress, 100)}%`;
  };

  window.addEventListener('scroll', throttle(updateProgress, 50), { passive: true });
}

/* ============================================================
   FAQ 아코디언
============================================================ */
function initFAQ() {
  const faqItems = document.querySelectorAll('.faq-question');

  faqItems.forEach(question => {
    question.addEventListener('click', () => {
      const answer = question.nextElementSibling;
      const isOpen = question.classList.contains('active');

      // 모두 닫기
      document.querySelectorAll('.faq-question').forEach(q => {
        q.classList.remove('active');
        const a = q.nextElementSibling;
        if (a) a.classList.remove('active');
      });

      // 현재 항목 토글
      if (!isOpen) {
        question.classList.add('active');
        if (answer) answer.classList.add('active');
      }
    });
  });
}

/* ============================================================
   목차 (TOC) — 활성 섹션 하이라이트
============================================================ */
function initTOC() {
  const tocLinks = document.querySelectorAll('.toc-list a');
  if (tocLinks.length === 0) return;

  const headings = Array.from(document.querySelectorAll('.article-body h2, .article-body h3'))
    .filter(h => h.id);

  if (headings.length === 0) return;

  const observerOptions = {
    root: null,
    rootMargin: '-15% 0% -70% 0%',
    threshold: 0
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        tocLinks.forEach(link => link.classList.remove('toc-active'));
        const activeLink = document.querySelector(`.toc-list a[href="#${entry.target.id}"]`);
        if (activeLink) activeLink.classList.add('toc-active');
      }
    });
  }, observerOptions);

  headings.forEach(h => observer.observe(h));

  // TOC 링크 클릭 - 부드러운 스크롤
  tocLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const targetId = link.getAttribute('href').slice(1);
      const target = document.getElementById(targetId);
      if (target) {
        const offset = 80;
        const top = target.getBoundingClientRect().top + window.scrollY - offset;
        window.scrollTo({ top, behavior: 'smooth' });
      }
    });
  });
}

/* ============================================================
   검색 결과 페이지 — URL 쿼리 파라미터 처리
   (search.html에 인라인 스크립트가 없는 경우 폴백)
============================================================ */
function initSearchPage() {
  const searchPageInput = document.getElementById('searchPageInput');
  // search.html은 자체 인라인 스크립트로 처리하므로 skip
  if (!searchPageInput) return;
  // 인라인 스크립트가 없는 경우에만 진행
  if (window.__searchInlineInit) return;

  const params = new URLSearchParams(window.location.search);
  const q = params.get('q') || '';

  if (q) {
    searchPageInput.value = q;
    if (searchPageQuery) searchPageQuery.textContent = `"${q}"`;
    const results = POSTS_DATA.filter(post =>
      post.title.toLowerCase().includes(q.toLowerCase()) ||
      post.excerpt.toLowerCase().includes(q.toLowerCase()) ||
      post.tags.some(t => t.toLowerCase().includes(q.toLowerCase())) ||
      post.category.toLowerCase().includes(q.toLowerCase())
    );
    if (searchPageCount) searchPageCount.textContent = results.length;
    if (searchPageResults) {
      if (results.length === 0) {
        searchPageResults.innerHTML = `
          <div style="text-align:center; padding:3rem 1rem; color:var(--color-text-muted);">
            <div style="font-size:2.5rem; margin-bottom:1rem;">🔍</div>
            <p style="font-size:var(--text-lg); font-weight:600; margin-bottom:0.5rem;">"${q}"에 대한 검색 결과가 없습니다</p>
            <p style="font-size:var(--text-sm);">다른 키워드로 검색해보세요.</p>
          </div>`;
      } else {
        searchPageResults.innerHTML = results.map(post => `
          <a href="${post.url}" class="post-card" style="display:block; padding:1.5rem; border:1px solid var(--color-border); border-radius:var(--radius-lg); margin-bottom:1rem; transition:box-shadow 0.2s; background:var(--color-bg);">
            <div style="font-size:var(--text-xs); color:var(--color-primary); font-weight:600; margin-bottom:0.4rem;">${post.category}</div>
            <h3 style="font-size:var(--text-lg); font-weight:700; margin-bottom:0.5rem; color:var(--color-text);">${highlightQuery(post.title, q)}</h3>
            <p style="font-size:var(--text-sm); color:var(--color-text-secondary); line-height:1.6;">${post.excerpt}</p>
            <div style="margin-top:0.75rem; display:flex; gap:0.4rem; flex-wrap:wrap;">
              ${post.tags.map(t => `<span style="font-size:11px; padding:2px 8px; background:var(--color-bg-gray); border-radius:99px; color:var(--color-text-secondary);">#${t}</span>`).join('')}
            </div>
          </a>`).join('');
      }
    }
  }

  // 검색창 입력 후 엔터
  searchPageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      const val = searchPageInput.value.trim();
      if (val) window.location.href = `search.html?q=${encodeURIComponent(val)}`;
    }
  });
}

/* ============================================================
   카테고리 바 수평 스크롤 화살표 힌트
============================================================ */
function initCategoryBarScroll() {
  const bar = document.querySelector('.category-bar');
  if (!bar) return;

  // 현재 URL의 카테고리 파라미터로 active 처리
  const params = new URLSearchParams(window.location.search);
  const currentCat = params.get('cat');

  if (currentCat) {
    bar.querySelectorAll('a').forEach(link => {
      const href = link.getAttribute('href');
      if (href && href.includes(`cat=${currentCat}`)) {
        link.classList.add('active');
      } else if (link.classList.contains('active') && !href?.includes('cat=')) {
        link.classList.remove('active');
      }
    });
  }
}

/* ============================================================
   유틸리티 함수
============================================================ */
function debounce(fn, delay) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

function throttle(fn, limit) {
  let inThrottle;
  return (...args) => {
    if (!inThrottle) {
      fn.apply(this, args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

/* ============================================================
   클립보드 복사 (코드 블록) — DOMContentLoaded 내에서 호출
============================================================ */
function initCodeCopy() {
  document.querySelectorAll('pre code').forEach(block => {
    const pre = block.parentElement;
    if (!pre) return;
    const btn = document.createElement('button');
    btn.textContent = '복사';
    btn.setAttribute('aria-label', '코드 복사');
    btn.style.cssText = `
      position: absolute; top: 0.75rem; right: 0.75rem;
      padding: 4px 10px; font-size: 11px; font-weight: 600;
      background: rgba(255,255,255,0.1); color: #e2e8f0;
      border: 1px solid rgba(255,255,255,0.2); border-radius: 4px;
      cursor: pointer; transition: background 0.15s; z-index:1;
    `;
    btn.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(block.textContent);
        btn.textContent = '✓ 복사됨';
        btn.style.background = 'rgba(5,150,105,0.3)';
        setTimeout(() => {
          btn.textContent = '복사';
          btn.style.background = 'rgba(255,255,255,0.1)';
        }, 1500);
      } catch {
        btn.textContent = '실패';
        setTimeout(() => (btn.textContent = '복사'), 1500);
      }
    });
    pre.style.position = 'relative';
    pre.appendChild(btn);
  });
}

/* ============================================================
   외부 링크에 rel="noopener noreferrer" 자동 추가
============================================================ */
function initExternalLinks() {
  document.querySelectorAll('a[href^="http"]').forEach(link => {
    try {
      const url = new URL(link.href);
      if (url.hostname !== window.location.hostname) {
        link.setAttribute('rel', 'noopener noreferrer');
        if (!link.hasAttribute('target')) {
          link.setAttribute('target', '_blank');
        }
      }
    } catch {
      // invalid URL — skip
    }
  });
}

/* ============================================================
   이미지 지연 로딩 (네이티브 lazy loading 지원 없는 경우 폴백)
============================================================ */
function initLazyImages() {
  if ('IntersectionObserver' in window) {
    const imgObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target;
          if (img.dataset.src) {
            img.src = img.dataset.src;
            img.removeAttribute('data-src');
            imgObserver.unobserve(img);
          }
        }
      });
    }, { rootMargin: '200px 0px' });

    document.querySelectorAll('img[data-src]').forEach(img => imgObserver.observe(img));
  }
}
