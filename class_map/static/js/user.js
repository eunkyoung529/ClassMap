console.log('[user.js] loaded');

async function renderUserBadge() {
  const el = document.getElementById('userBadge');
  if (!el) { console.warn('[user] #userBadge not found'); return; }

  const access = localStorage.getItem('access');
  if (!access) {
    el.innerHTML = `
      <a class="btn" href="/signup/">회원가입</a>
      <a class="btn btn-primary" href="/login/">로그인</a>`;
    console.log('[user] guest: show signup/login');
    return;
  }

  try {
    console.log('[user] GET /api/auth/me/');
    const meRes = await fetch('/api/auth/me/', { headers: { Authorization: `Bearer ${access}` } });
    if (!meRes.ok) throw new Error('unauthenticated');
    const me = await meRes.json();

    const badge = me.plan === 'pro'
      ? '<span style="padding:2px 6px;border-radius:8px;background:#7c3aed;color:#fff;font-size:12px;margin-left:6px;">PRO</span>'
      : '<span style="padding:2px 6px;border-radius:8px;background:#333;color:#ddd;font-size:12px;margin-left:6px;">FREE</span>';

    el.innerHTML = `
      <span>${me.username}</span>${badge}
      <a class="btn btn-accent" style="margin-left:12px" href="javascript:void(0)" onclick="logout()">로그아웃</a>`;
    console.log('[user] me ok:', me);
  } catch (e) {
    console.warn('[user] /me failed, fallback to guest:', e);
    el.innerHTML = `
      <a class="btn" href="/signup/">회원가입</a>
      <a class="btn btn-primary" href="/login/">로그인</a>`;
  }
}

function logout() {
  localStorage.removeItem('access');
  localStorage.removeItem('refresh');
  localStorage.removeItem('username');
  localStorage.removeItem('plan');
  location.href = '/';
}

/** CTA: 비로그인일 때만 보이기 (로그인하면 숨김) */
async function renderCtaVisibility() {
  const cta = document.getElementById('cta');
  if (!cta) { console.warn('[user] #cta not found'); return; }

  // 기본값: 보이기
  cta.style.setProperty('display', 'block', 'important');

  const access = localStorage.getItem('access');
  if (!access) { console.log('[user] CTA: guest → show'); return; }

  // 로그인 추정 → 먼저 숨김 처리해서 깜빡임 제거
  cta.style.setProperty('display', 'none', 'important');

  try {
    const meRes = await fetch('/api/auth/me/', { headers: { Authorization: `Bearer ${access}` } });
    if (meRes.ok) {
      console.log('[user] CTA: logged-in → keep hidden');
      // keep hidden
    } else {
      console.warn('[user] CTA: token invalid → show');
      cta.style.setProperty('display', 'block', 'important');
    }
  } catch {
    console.warn('[user] CTA: /me error → show');
    cta.style.setProperty('display', 'block', 'important');
  }
}

// DOM 로드 시 한 번만 실행
window.addEventListener('DOMContentLoaded', () => {
  renderUserBadge();
  renderCtaVisibility();
});
