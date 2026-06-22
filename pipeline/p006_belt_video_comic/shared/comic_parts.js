// P006 · 漫画风可复用 SVG 简笔画
//
// 用法: 在模板里 <div class="char"></div> + JS 调 window.drawHead(selector, expression)
//
// 表情库:
//   confused / pained / happy / serious / curious / shocked / chill

window.svgParts = {
  // 简笔人头 · 圆头 + 头发 + 表情
  head: function(expression) {
    expression = expression || 'confused';
    const exprs = {
      confused: {
        leftEye: '<circle cx="78" cy="98" r="8" fill="#1a1a1a"/>',
        rightEye: '<circle cx="128" cy="98" r="8" fill="#1a1a1a"/>',
        mouth: '<path d="M 78 138 Q 103 132 128 138" stroke="#1a1a1a" stroke-width="6" fill="none" stroke-linecap="round"/>',
        brow: '<path d="M 65 78 L 85 84 M 121 84 L 141 78" stroke="#1a1a1a" stroke-width="5" stroke-linecap="round" fill="none"/>',
      },
      pained: {
        leftEye: '<path d="M 70 92 L 86 102 M 86 92 L 70 102" stroke="#1a1a1a" stroke-width="6" stroke-linecap="round"/>',
        rightEye: '<path d="M 120 92 L 136 102 M 136 92 L 120 102" stroke="#1a1a1a" stroke-width="6" stroke-linecap="round"/>',
        mouth: '<path d="M 70 142 Q 80 130 90 142 Q 100 130 110 142 Q 120 130 132 142" stroke="#1a1a1a" stroke-width="6" fill="none" stroke-linecap="round"/>',
        brow: '<path d="M 60 78 L 88 70 M 118 70 L 146 78" stroke="#1a1a1a" stroke-width="5" stroke-linecap="round" fill="none"/>',
      },
      happy: {
        leftEye: '<path d="M 65 95 Q 78 82 91 95" stroke="#1a1a1a" stroke-width="6" fill="none" stroke-linecap="round"/>',
        rightEye: '<path d="M 115 95 Q 128 82 141 95" stroke="#1a1a1a" stroke-width="6" fill="none" stroke-linecap="round"/>',
        mouth: '<path d="M 70 130 Q 103 168 136 130" stroke="#1a1a1a" stroke-width="7" fill="#e63946" stroke-linecap="round"/>',
        brow: '<path d="M 64 78 L 88 76 M 118 76 L 142 78" stroke="#1a1a1a" stroke-width="4" stroke-linecap="round" fill="none"/>',
      },
      serious: {
        leftEye: '<circle cx="78" cy="98" r="6" fill="#1a1a1a"/>',
        rightEye: '<circle cx="128" cy="98" r="6" fill="#1a1a1a"/>',
        mouth: '<line x1="78" y1="138" x2="128" y2="138" stroke="#1a1a1a" stroke-width="6" stroke-linecap="round"/>',
        brow: '<path d="M 62 76 L 90 86 M 116 86 L 144 76" stroke="#1a1a1a" stroke-width="6" stroke-linecap="round" fill="none"/>',
      },
      curious: {
        leftEye: '<circle cx="78" cy="98" r="10" fill="#1a1a1a"/><circle cx="80" cy="95" r="3" fill="#fff"/>',
        rightEye: '<circle cx="128" cy="98" r="10" fill="#1a1a1a"/><circle cx="130" cy="95" r="3" fill="#fff"/>',
        mouth: '<ellipse cx="103" cy="138" rx="14" ry="10" fill="#1a1a1a"/>',
        brow: '<path d="M 64 70 L 88 78 M 118 78 L 142 70" stroke="#1a1a1a" stroke-width="5" stroke-linecap="round" fill="none"/>',
      },
      shocked: {
        leftEye: '<circle cx="78" cy="98" r="14" fill="#fff" stroke="#1a1a1a" stroke-width="4"/><circle cx="78" cy="100" r="5" fill="#1a1a1a"/>',
        rightEye: '<circle cx="128" cy="98" r="14" fill="#fff" stroke="#1a1a1a" stroke-width="4"/><circle cx="128" cy="100" r="5" fill="#1a1a1a"/>',
        mouth: '<ellipse cx="103" cy="142" rx="20" ry="22" fill="#1a1a1a"/>',
        brow: '<path d="M 58 60 L 90 70 M 116 70 L 148 60" stroke="#1a1a1a" stroke-width="6" stroke-linecap="round" fill="none"/>',
      },
      chill: {
        leftEye: '<path d="M 65 98 Q 78 105 91 98" stroke="#1a1a1a" stroke-width="5" fill="none" stroke-linecap="round"/>',
        rightEye: '<path d="M 115 98 Q 128 105 141 98" stroke="#1a1a1a" stroke-width="5" fill="none" stroke-linecap="round"/>',
        mouth: '<path d="M 80 138 Q 103 148 126 138" stroke="#1a1a1a" stroke-width="6" fill="none" stroke-linecap="round"/>',
        brow: '<path d="M 64 80 L 88 80 M 118 80 L 142 80" stroke="#1a1a1a" stroke-width="4" stroke-linecap="round" fill="none"/>',
      },
    };
    const e = exprs[expression] || exprs.confused;
    return `
      <svg viewBox="0 0 206 220" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:100%;">
        <!-- 脖子 -->
        <rect x="85" y="180" width="36" height="40" fill="#fde6c9" stroke="#1a1a1a" stroke-width="5"/>
        <!-- 头 (椭圆 + 故意不平) -->
        <path d="M 103 18 C 60 18 24 60 24 105 C 24 150 60 188 103 188 C 146 188 182 150 182 105 C 182 60 146 18 103 18 Z"
              fill="#fde6c9" stroke="#1a1a1a" stroke-width="6"/>
        <!-- 头发 -->
        <path d="M 30 70 Q 60 -5 100 18 Q 145 -5 178 70 Q 178 50 160 36 Q 130 18 100 30 Q 70 18 40 36 Q 28 48 30 70 Z"
              fill="#2b1810"/>
        <!-- 耳朵 -->
        <ellipse cx="22" cy="110" rx="10" ry="16" fill="#fde6c9" stroke="#1a1a1a" stroke-width="5"/>
        <ellipse cx="184" cy="110" rx="10" ry="16" fill="#fde6c9" stroke="#1a1a1a" stroke-width="5"/>
        ${e.brow}
        ${e.leftEye}
        ${e.rightEye}
        ${e.mouth}
      </svg>`;
  },

  // 胶囊瓶 SVG
  pillBottle: function() {
    return `
      <svg viewBox="0 0 200 280" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:100%;">
        <!-- 瓶盖 -->
        <rect x="50" y="0" width="100" height="50" rx="6" fill="#e63946" stroke="#1a1a1a" stroke-width="6"/>
        <line x1="50" y1="50" x2="150" y2="50" stroke="#1a1a1a" stroke-width="3"/>
        <!-- 瓶身 -->
        <rect x="30" y="40" width="140" height="230" rx="10" fill="#fff" stroke="#1a1a1a" stroke-width="7"/>
        <!-- 标签 -->
        <rect x="42" y="80" width="116" height="140" fill="#4361ee" stroke="#1a1a1a" stroke-width="5"/>
        <text x="100" y="135" text-anchor="middle" font-family="Hannotate SC" font-size="42" fill="#fff" font-weight="900">VC</text>
        <text x="100" y="180" text-anchor="middle" font-family="SF Mono" font-size="22" fill="#fff" font-weight="700">90 caps</text>
        <text x="100" y="208" text-anchor="middle" font-family="Hannotate SC" font-size="20" fill="#fff">/胶囊/</text>
      </svg>`;
  },

  // 单颗胶囊 (横向)
  pillCapsule: function() {
    return `
      <svg viewBox="0 0 180 80" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:100%;">
        <rect x="6" y="6" width="80" height="68" rx="34" fill="#e63946" stroke="#1a1a1a" stroke-width="6"/>
        <rect x="86" y="6" width="88" height="68" rx="34" fill="#fff" stroke="#1a1a1a" stroke-width="6"/>
        <line x1="86" y1="12" x2="86" y2="68" stroke="#1a1a1a" stroke-width="5"/>
      </svg>`;
  },

  // 咀嚼片 (圆角方形)
  chewable: function(label) {
    label = label || '';
    return `
      <svg viewBox="0 0 180 180" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:100%;">
        <rect x="12" y="12" width="156" height="156" rx="40" fill="#ffd23f" stroke="#1a1a1a" stroke-width="7"/>
        <circle cx="60" cy="60" r="6" fill="#1a1a1a"/>
        <circle cx="120" cy="60" r="6" fill="#1a1a1a"/>
        <path d="M 55 110 Q 90 140 125 110" stroke="#1a1a1a" stroke-width="6" fill="none" stroke-linecap="round"/>
        <text x="90" y="160" text-anchor="middle" font-family="SF Mono" font-size="14" fill="#1a1a1a" font-weight="900">${label}</text>
      </svg>`;
  },

  // 手机壳
  phone: function() {
    return `
      <svg viewBox="0 0 220 380" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:100%;">
        <rect x="10" y="10" width="200" height="360" rx="28" fill="#fdfbf5" stroke="#1a1a1a" stroke-width="8"/>
        <rect x="20" y="50" width="180" height="290" fill="#e8e0c8"/>
        <rect x="85" y="20" width="50" height="14" rx="7" fill="#1a1a1a"/>
        <circle cx="110" cy="358" r="6" stroke="#1a1a1a" stroke-width="3" fill="none"/>
      </svg>`;
  },

  // 闪光星
  sparkle: function() {
    return `
      <svg viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:100%;">
        <path d="M 40 0 L 48 32 L 80 40 L 48 48 L 40 80 L 32 48 L 0 40 L 32 32 Z"
              fill="#ffd23f" stroke="#1a1a1a" stroke-width="4" stroke-linejoin="round"/>
      </svg>`;
  },
};

// 便捷函数: 写到任意 DOM 元素
window.drawHead = function(selector, expression) {
  const el = document.querySelector(selector);
  if (el) el.innerHTML = window.svgParts.head(expression);
};
window.drawPart = function(selector, name, arg) {
  const el = document.querySelector(selector);
  const fn = window.svgParts[name];
  if (el && fn) el.innerHTML = fn(arg);
};
