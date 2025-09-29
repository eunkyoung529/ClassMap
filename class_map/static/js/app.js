// async function renderUserBadge() {
//     const el = document.getElementById('userBadge');
//     if (!el) return;
  
//     const access = localStorage.getItem('access');
//     if (!access) {
//       el.innerHTML = `
//         <a class="btn" href="/signup/">회원가입</a>
//         <a class="btn btn-primary" href="/login/">로그인</a>`;
//       return;
//     }
  
//     try {
//       // 여기서 질문한 코드가 사용됩니다
//       const meRes = await fetch('/api/auth/me/', {
//         headers: { Authorization: `Bearer ${access}` }
//       });
  
//       if (!meRes.ok) throw new Error('unauthenticated');
  
//       const me = await meRes.json();
//       const badge = me.plan === 'pro'
//         ? '<span style="padding:2px 6px;border-radius:8px;background:#7c3aed;color:#fff;font-size:12px;margin-left:6px;">PRO</span>'
//         : '<span style="padding:2px 6px;border-radius:8px;background:#333;color:#ddd;font-size:12px;margin-left:6px;">FREE</span>';
  
//       el.innerHTML = `
//         <span>${me.username}</span>${badge}
//         <a class="btn" style="margin-left:12px" href="javascript:void(0)" onclick="logout()">로그아웃</a>`;
//     } catch (e) {
//       // 토큰 만료/실패 시 로그아웃 버튼 대신 로그인 버튼 노출
//       el.innerHTML = `
//         <a class="btn" href="/signup/">회원가입</a>
//         <a class="btn btn-primary" href="/login/">로그인</a>`;
//     }
//   }
  
//   function logout() {
//     localStorage.removeItem('access');
//     localStorage.removeItem('refresh');
//     localStorage.removeItem('username');
//     localStorage.removeItem('plan');
//     location.href = '/';
//   }
  
//   window.addEventListener('DOMContentLoaded', renderUserBadge);
  

// static/js/app.js
async function renderUserBadge() {
    const el = document.getElementById('userBadge');
    if (!el) {
      console.warn('[app] #userBadge element not found');
      return;
    }
  
    const access = localStorage.getItem('access');
    if (!access) {
      el.innerHTML = `
        <a class="btn" href="/signup/">회원가입</a>
        <a class="btn btn-primary" href="/login/">로그인</a>`;
      console.log('[app] no access token, show guest buttons');
      return;
    }
  
    try {
      console.log('[app] calling /api/auth/me/');
      const meRes = await fetch('/api/auth/me/', {
        headers: { Authorization: `Bearer ${access}` }
      });
  
      if (!meRes.ok) {
        console.warn('[app] /me failed:', meRes.status);
        throw new Error('unauthenticated');
      }
  
      const me = await meRes.json();
      console.log('[app] /me ok:', me);
  
      const badge = me.plan === 'pro'
        ? '<span style="padding:2px 6px;border-radius:8px;background:#7c3aed;color:#fff;font-size:12px;margin-left:6px;">PRO</span>'
        : '<span style="padding:2px 6px;border-radius:8px;background:#333;color:#ddd;font-size:12px;margin-left:6px;">FREE</span>';
  
      el.innerHTML = `
        <span>${me.username}</span>${badge}
        <a class="btn" style="margin-left:12px" href="javascript:void(0)" onclick="logout()">로그아웃</a>`;
    } catch (e) {
      console.error('[app] renderUserBadge error:', e);
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
  
  window.addEventListener('DOMContentLoaded', renderUserBadge);
  