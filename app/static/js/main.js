/**
 * Logit Blog — 공통 JavaScript
 * 검색 오버레이, 모바일 메뉴, TOC 하이라이트, 읽기 진행바, Back to top, 관리자 사이드바
 */

'use strict';

document.addEventListener('DOMContentLoaded', () => {
  initReadingProgress();
  initSearchOverlay();
  initMobileMenu();
  initBackToTop();
  initTOC();
  initExternalLinks();
  initLazyImages();
  initAdminSidebar();
  initCopyButtons();
});


/* ── 읽기 진행 바 ────────────────────────────────────────────── */
function initReadingProgress() {
  const bar = document.getElementById('reading-progress');
  if (!bar) return;
  let ticking = false;
  window.addEventListener('scroll', () => {
    if (!ticking) {
      requestAnimationFrame(() => {
        const docH = document.documentElement.scrollHeight - window.innerHeight;
        const progress = docH > 0 ? (window.scrollY / docH) * 100 : 0;
        bar.style.width = Math.min(100, progress) + '%';
        ticking = false;
      });
      ticking = true;
    }
  }, { passive: true });
}


/* ── Back to top ────────────────────────────────────────────── */
function initBackToTop() {
  const btn = document.getElementById('back-to-top');
  if (!btn) return;
  window.addEventListener('scroll', () => {
    btn.classList.toggle('visible', window.scrollY > 400);
  }, { passive: true });
  btn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
}


/* ── 검색 오버레이 ───────────────────────────────────────────── */
function initSearchOverlay() {
  const overlay = document.getElementById('search-overlay');
  const toggle  = document.getElementById('search-toggle');
  const close   = document.getElementById('search-close');
  const input   = document.getElementById('search-overlay-input');
  const results = document.getElementById('search-overlay-results');
  if (!overlay || !toggle) return;

  function openSearch() {
    overlay.classList.add('open');
    overlay.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
    setTimeout(() => input && input.focus(), 50);
  }
  function closeSearch() {
    overlay.classList.remove('open');
    overlay.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
  }

  toggle.addEventListener('click', openSearch);
  close && close.addEventListener('click', closeSearch);
  overlay.addEventListener('click', (e) => { if (e.target === overlay) closeSearch(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeSearch(); });

  // 라이브 검색 (API 미지원 시 빈 결과 표시)
  let debounceTimer;
  input && input.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    const q = input.value.trim();
    if (!q || q.length < 2) { results && (results.innerHTML = ''); return; }
    debounceTimer = setTimeout(() => fetchSearchResults(q, results), 300);
  });

  // Enter 키 → 검색 페이지
  input && input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const q = input.value.trim();
      if (q) window.location.href = '/search?q=' + encodeURIComponent(q);
    }
  });
}

async function fetchSearchResults(query, container) {
  if (!container) return;
  try {
    const res = await fetch(`/search?q=${encodeURIComponent(query)}`, {
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    });
    // 서버 검색 결과 페이지로 이동 유도
    container.innerHTML = `
      <div style="padding:.75rem 0;text-align:center;font-size:.875rem;color:#6b7280;">
        <a href="/search?q=${encodeURIComponent(query)}" style="color:#2563eb;font-weight:600;">
          "${query}" 검색 결과 전체 보기 →
        </a>
      </div>`;
  } catch {}
}


/* ── 모바일 메뉴 ─────────────────────────────────────────────── */
function initMobileMenu() {
  const toggle  = document.getElementById('mobile-menu-toggle');
  const nav     = document.getElementById('mobile-nav');
  const closeBtn = document.getElementById('mobile-nav-close');
  const overlay = document.getElementById('mobile-overlay');
  if (!toggle || !nav) return;

  function openMenu() {
    nav.classList.add('open');
    overlay && overlay.classList.add('open');
    toggle.setAttribute('aria-expanded', 'true');
    document.body.style.overflow = 'hidden';
  }
  function closeMenu() {
    nav.classList.remove('open');
    overlay && overlay.classList.remove('open');
    toggle.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
  }

  toggle.addEventListener('click', openMenu);
  closeBtn && closeBtn.addEventListener('click', closeMenu);
  overlay && overlay.addEventListener('click', closeMenu);
}


/* ── TOC 자동 생성 & 하이라이트 ─────────────────────────────── */
function initTOC() {
  const tocNav = document.getElementById('toc-nav');
  const content = document.getElementById('post-content');
  if (!tocNav || !content) return;

  const headings = content.querySelectorAll('h2, h3');
  if (headings.length === 0) {
    const tocBox = document.getElementById('toc-box');
    if (tocBox) tocBox.style.display = 'none';
    return;
  }

  const links = [];
  headings.forEach((h, i) => {
    if (!h.id) h.id = `heading-${i}`;
    const a = document.createElement('a');
    a.href = `#${h.id}`;
    a.textContent = h.textContent;
    a.style.paddingLeft = h.tagName === 'H3' ? '1.25rem' : '.5rem';
    tocNav.appendChild(a);
    links.push(a);
  });

  // IntersectionObserver로 하이라이트
  if (!window.IntersectionObserver) return;
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          links.forEach((l) => l.classList.remove('toc-active'));
          const activeLink = tocNav.querySelector(`a[href="#${entry.target.id}"]`);
          if (activeLink) activeLink.classList.add('toc-active');
        }
      });
    },
    { rootMargin: '-15% 0% -70% 0%' }
  );
  headings.forEach((h) => observer.observe(h));
}


/* ── 외부 링크 처리 ──────────────────────────────────────────── */
function initExternalLinks() {
  const baseHost = window.location.hostname;
  document.querySelectorAll('a[href]').forEach((a) => {
    try {
      const url = new URL(a.href, window.location.href);
      if (url.hostname && url.hostname !== baseHost && !a.hasAttribute('target')) {
        a.setAttribute('target', '_blank');
        a.setAttribute('rel', 'noopener noreferrer');
      }
    } catch {}
  });
}


/* ── 이미지 레이지 로딩 ──────────────────────────────────────── */
function initLazyImages() {
  if (!window.IntersectionObserver) return;
  const images = document.querySelectorAll('img[data-src]');
  if (!images.length) return;
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const img = entry.target;
        img.src = img.dataset.src;
        img.removeAttribute('data-src');
        observer.unobserve(img);
      }
    });
  }, { rootMargin: '200px' });
  images.forEach((img) => observer.observe(img));
}


/* ── 코드 블록 복사 버튼 ─────────────────────────────────────── */
function initCopyButtons() {
  document.querySelectorAll('.post-content pre').forEach((pre) => {
    const btn = document.createElement('button');
    btn.className = 'code-copy-btn';
    btn.textContent = '복사';
    btn.setAttribute('aria-label', '코드 복사');
    pre.style.position = 'relative';
    pre.appendChild(btn);
    btn.addEventListener('click', () => {
      const code = pre.querySelector('code');
      const text = code ? code.textContent : pre.textContent;
      navigator.clipboard.writeText(text).then(() => {
        btn.textContent = '✓ 복사됨';
        setTimeout(() => (btn.textContent = '복사'), 2000);
      }).catch(() => {});
    });
  });
}


/* ── 관리자 사이드바 토글 (모바일) ──────────────────────────── */
function initAdminSidebar() {
  const toggle = document.getElementById('admin-menu-toggle');
  const sidebar = document.getElementById('admin-sidebar');
  if (!toggle || !sidebar) return;
  toggle.addEventListener('click', () => sidebar.classList.toggle('open'));
  // 사이드바 외부 클릭 시 닫기
  document.addEventListener('click', (e) => {
    if (!sidebar.contains(e.target) && e.target !== toggle) {
      sidebar.classList.remove('open');
    }
  });
}


/* ── 코드 복사 버튼 스타일 주입 ─────────────────────────────── */
(function injectCodeCopyStyle() {
  const style = document.createElement('style');
  style.textContent = `
    .code-copy-btn {
      position: absolute; top: .6rem; right: .6rem;
      padding: .2rem .6rem; font-size: .75rem; font-weight: 600;
      background: rgba(255,255,255,.12); color: #e2e8f0;
      border: 1px solid rgba(255,255,255,.2); border-radius: 4px;
      cursor: pointer; transition: background .15s;
    }
    .code-copy-btn:hover { background: rgba(255,255,255,.22); }
  `;
  document.head.appendChild(style);
})();
