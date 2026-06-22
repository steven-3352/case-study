// P004 · GSAP 渲染帧钩子
//
// 每个模板在 <script> 末尾构建一条 paused 的 gsap.timeline,
// 然后调 registerTimeline(tl)。capture_frames.py 通过 page.evaluate 调用:
//   window.__duration  → 拿总时长(秒)
//   window.__renderFrame(t) → 跳到任意时间点
//
// 不依赖真实播放,可以确定性渲染任意 fps。

window.__timeline = null;
window.__duration = 0;

window.registerTimeline = function (tl) {
  tl.pause();
  window.__timeline = tl;
  window.__duration = tl.duration();
};

window.__renderFrame = function (t) {
  if (!window.__timeline) return;
  // clamp 防止超过总时长
  const d = window.__timeline.duration();
  const clamped = Math.max(0, Math.min(t, d));
  window.__timeline.time(clamped);
};

// 注入参数 — capture_frames.py 在 navigate 前用 addInitScript 设置
// window.__data = {...}
window.getData = function () {
  return window.__data || {};
};

// 打字机效果 helper · 按字符数 stagger 到 timeline
window.typewriter = function (selector, text, opts = {}) {
  const el = document.querySelector(selector);
  if (!el) return null;
  el.textContent = "";
  const chars = Array.from(text);
  const spans = chars.map((c) => {
    const s = document.createElement("span");
    s.textContent = c;
    s.style.opacity = 0;
    el.appendChild(s);
    return s;
  });
  return gsap.to(spans, {
    opacity: 1,
    duration: opts.duration || 0.02,
    stagger: opts.stagger || 0.06,
    ease: "none",
  });
};

// 数字滚出动效 · 用于"23"/"9"/"500"/"2" 等关键数字
window.countUp = function (selector, from, to, opts = {}) {
  const el = document.querySelector(selector);
  if (!el) return null;
  const obj = { v: from };
  el.textContent = String(from);
  return gsap.to(obj, {
    v: to,
    duration: opts.duration || 0.8,
    ease: opts.ease || "power2.out",
    onUpdate: () => {
      el.textContent = String(Math.round(obj.v));
    },
  });
};
