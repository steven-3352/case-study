/* ============================================================
   共享顶栏 nav.js —— 所有页面 <header id="site-nav"></header> 处注入
   用法:<script src="assets/nav.js" data-here="home"></script>
   data-here ∈ home | workspace | gallery | console
   ============================================================ */
(function(){
  "use strict";
  function mountNav(){
    const host = document.getElementById("site-nav");
    if(!host) return;
    const script = document.currentScript || document.querySelector('script[src*="nav.js"]');
    const here = (script && script.getAttribute("data-here")) || "";
    const sess = (window.Studio && Studio.auth.current()) || null;

    const link = (id, href, label)=>`<a href="${href}" class="${here===id?'here':''}">${label}</a>`;
    const authArea = sess
      ? `<span class="nav-user"><span class="avatar">${(sess.username||"?").slice(0,1).toUpperCase()}</span>${sess.username}</span>
         <a href="#" class="nav-login" id="nav-logout">退出</a>`
      : `<a href="login.html" class="nav-login">登录</a>`;

    host.className = "nav";
    host.innerHTML = `
      <div class="nav-inner">
        <a class="brand" href="index.html"><span class="mark"></span>内容工作台</a>
        <nav class="menu">
          <span class="nav-dd">
            <a class="${here==='console'?'here':''}">视频<span class="caret">▾</span></a>
            <div class="panel">
              <a href="workspace.html?recipe=ad">带货视频<span class="tag">商品 → 脚本 → 成片</span></a>
              <a href="workspace.html?recipe=mv">MV 视频<span class="tag">歌曲 → 卡点 → 成片</span></a>
              <a href="workspace.html?recipe=ad2">动作迁移<span class="tag">拍同款 · 参考翻拍</span></a>
            </div>
          </span>
          <a href="workspace.html?recipe=img">图片</a>
          <a href="#" title="其他系统 · 暂未开放" style="opacity:.5;cursor:not-allowed">漫剧</a>
          ${link('workspace','workspace.html','工作台')}
          ${link('gallery','gallery.html','作品浏览')}
          <button class="theme-toggle" id="theme-toggle" type="button" aria-label="切换深浅色"><span class="glyph">◐</span><span class="label">深色</span></button>
          ${authArea}
        </nav>
      </div>`;

    const lo = document.getElementById("nav-logout");
    if(lo) lo.addEventListener("click", e=>{ e.preventDefault(); Studio.auth.logout(); location.href="index.html"; });

    // 主题
    const root=document.documentElement, btn=document.getElementById("theme-toggle");
    if(btn){
      const label=btn.querySelector(".label"), glyph=btn.querySelector(".glyph");
      function apply(t){ root.setAttribute("data-theme",t); label.textContent=t==="dark"?"浅色":"深色"; glyph.textContent=t==="dark"?"☀":"◐"; try{localStorage.setItem("preview-theme",t);}catch(e){} }
      let saved; try{saved=localStorage.getItem("preview-theme");}catch(e){}
      apply(saved==="dark"?"dark":"light");
      btn.addEventListener("click",()=>apply(root.getAttribute("data-theme")==="dark"?"light":"dark"));
    }
  }

  /* 全站 toast 助手 */
  window.toast = function(msg){
    let t = document.getElementById("global-toast");
    if(!t){ t=document.createElement("div"); t.id="global-toast"; t.className="toast"; document.body.appendChild(t); }
    t.textContent = msg; t.classList.add("show");
    clearTimeout(window.__toastT); window.__toastT = setTimeout(()=>t.classList.remove("show"), 2200);
  };

  if(document.readyState==="loading") document.addEventListener("DOMContentLoaded", mountNav);
  else mountNav();
})();
