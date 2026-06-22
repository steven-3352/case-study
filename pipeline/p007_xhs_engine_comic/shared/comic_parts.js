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

  // 旧版素材堆 · 文件夹 + 黑金幻灯片
  legacyStack: function() {
    return `
      <svg viewBox="0 0 280 320" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:100%;">
        <rect x="20" y="80" width="200" height="150" rx="8" fill="#2b1810" stroke="#1a1a1a" stroke-width="6" transform="rotate(-6 120 155)"/>
        <rect x="40" y="60" width="200" height="150" rx="8" fill="#3d2914" stroke="#1a1a1a" stroke-width="6" transform="rotate(3 140 135)"/>
        <rect x="55" y="40" width="200" height="150" rx="8" fill="#ffd23f" stroke="#1a1a1a" stroke-width="7"/>
        <text x="155" y="110" text-anchor="middle" font-family="Hannotate SC" font-size="28" fill="#1a1a1a" font-weight="900">slides</text>
        <text x="155" y="150" text-anchor="middle" font-family="SF Mono" font-size="22" fill="#1a1a1a">legacy/</text>
        <path d="M 30 260 L 250 260" stroke="#e63946" stroke-width="8" stroke-linecap="round"/>
        <text x="140" y="300" text-anchor="middle" font-family="Hannotate SC" font-size="36" fill="#e63946" font-weight="900">v1 素材包</text>
      </svg>`;
  },

  // 新版 publish 包
  publishBox: function() {
    return `
      <svg viewBox="0 0 280 320" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:100%;">
        <rect x="40" y="50" width="200" height="180" rx="12" fill="#4361ee" stroke="#1a1a1a" stroke-width="7"/>
        <text x="140" y="110" text-anchor="middle" font-family="Hannotate SC" font-size="42" fill="#fff" font-weight="900">publish/</text>
        <text x="140" y="155" text-anchor="middle" font-family="SF Mono" font-size="20" fill="#fff">mp4 + 文案</text>
        <text x="140" y="185" text-anchor="middle" font-family="SF Mono" font-size="18" fill="#fff">insights ✓</text>
        <rect x="70" y="250" width="140" height="50" rx="8" fill="#2a9d3a" stroke="#1a1a1a" stroke-width="5"/>
        <text x="140" y="285" text-anchor="middle" font-family="Hannotate SC" font-size="32" fill="#fff" font-weight="900">v2 引擎</text>
      </svg>`;
  },

  // 小笔记本
  laptop: function() {
    return `
      <svg viewBox="0 0 300 220" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:100%;">
        <rect x="20" y="20" width="260" height="150" rx="10" fill="#1a1a1a" stroke="#1a1a1a" stroke-width="6"/>
        <rect x="32" y="32" width="236" height="126" rx="4" fill="#4361ee"/>
        <text x="150" y="100" text-anchor="middle" font-family="Hannotate SC" font-size="36" fill="#fff" font-weight="900">pipeline</text>
        <path d="M 10 170 L 290 170 L 320 210 L -10 210 Z" fill="#e8e0c8" stroke="#1a1a1a" stroke-width="6" stroke-linejoin="round"/>
      </svg>`;
  },

  // Agent 徽章 (旧版 · 保留兼容)
  agentBadge: function(label) {
    label = label || 'Agent';
    return `
      <svg viewBox="0 0 180 180" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:100%;">
        <circle cx="90" cy="90" r="72" fill="#fff3d4" stroke="#1a1a1a" stroke-width="7"/>
        <circle cx="90" cy="70" r="28" fill="#fde6c9" stroke="#1a1a1a" stroke-width="5"/>
        <path d="M 50 130 Q 90 155 130 130" stroke="#1a1a1a" stroke-width="5" fill="none"/>
        <text x="90" y="168" text-anchor="middle" font-family="Hannotate SC" font-size="22" fill="#1a1a1a" font-weight="900">${label}</text>
      </svg>`;
  },

  // 工种卡通头像 · 每个角色独立发型/表情/道具
  agentAvatar: function(role) {
    const skin = '#fde6c9';
    const ink = '#1a1a1a';
    const roles = {
      '深挖': {
        bg: '#dbeafe', shirt: '#4361ee',
        hair: `<path d="M 48 88 Q 50 28 100 24 Q 148 20 152 72 Q 156 108 140 120 L 120 90 Q 100 70 80 90 Z" fill="#1a1a1a"/>`,
        face: `<circle cx="82" cy="98" r="9" fill="${ink}"/><circle cx="84" cy="96" r="3" fill="#fff"/><circle cx="118" cy="98" r="9" fill="${ink}"/><circle cx="120" cy="96" r="3" fill="#fff"/><ellipse cx="100" cy="128" rx="12" ry="9" fill="${ink}"/>`,
        prop: `<circle cx="168" cy="168" r="26" fill="#fff" stroke="${ink}" stroke-width="5"/><circle cx="158" cy="168" r="10" fill="none" stroke="${ink}" stroke-width="4"/><line x1="166" y1="176" x2="182" y2="192" stroke="${ink}" stroke-width="5" stroke-linecap="round"/>`,
      },
      '记者': {
        bg: '#fff3d4', shirt: '#e63946',
        hair: `<rect x="52" y="36" width="96" height="28" rx="6" fill="${ink}"/><path d="M 48 64 Q 48 28 100 26 Q 152 28 152 64 Q 152 100 100 108 Q 48 100 48 64 Z" fill="#3d2914"/>`,
        face: `<circle cx="82" cy="100" r="6" fill="${ink}"/><circle cx="118" cy="100" r="6" fill="${ink}"/><line x1="78" y1="128" x2="122" y2="128" stroke="${ink}" stroke-width="5" stroke-linecap="round"/>`,
        prop: `<rect x="8" y="150" width="44" height="52" rx="6" fill="#fff" stroke="${ink}" stroke-width="5"/><line x1="16" y1="166" x2="44" y2="166" stroke="${ink}" stroke-width="3"/><line x1="16" y1="178" x2="40" y2="178" stroke="${ink}" stroke-width="3"/>`,
      },
      '编剧': {
        bg: '#fce7f3', shirt: '#7c3aed',
        hair: `<path d="M 44 70 Q 40 20 100 22 Q 160 24 156 80 Q 154 110 130 100 Q 110 60 70 100 Q 46 110 44 70 Z" fill="#5c3d2e"/>`,
        face: `<path d="M 72 98 Q 84 108 96 98" stroke="${ink}" stroke-width="5" fill="none" stroke-linecap="round"/><path d="M 104 98 Q 116 108 128 98" stroke="${ink}" stroke-width="5" fill="none" stroke-linecap="round"/><path d="M 78 126 Q 100 140 122 126" stroke="${ink}" stroke-width="5" fill="none" stroke-linecap="round"/>`,
        prop: `<rect x="158" y="42" width="10" height="48" rx="3" fill="#ffd23f" stroke="${ink}" stroke-width="4" transform="rotate(25 163 66)"/><polygon points="168,42 182,50 168,58" fill="#e63946" stroke="${ink}" stroke-width="3"/>`,
      },
      '导演': {
        bg: '#fee2e2', shirt: '#1a1a1a',
        hair: `<ellipse cx="100" cy="48" rx="54" ry="22" fill="${ink}"/><path d="M 48 64 Q 48 30 100 28 Q 152 30 152 70 Q 148 108 100 112 Q 52 108 48 64 Z" fill="#2b1810"/>`,
        face: `<circle cx="82" cy="100" r="6" fill="${ink}"/><circle cx="118" cy="100" r="6" fill="${ink}"/><line x1="80" y1="130" x2="120" y2="130" stroke="${ink}" stroke-width="6" stroke-linecap="round"/>`,
        prop: `<rect x="6" y="148" width="52" height="40" rx="4" fill="#ffd23f" stroke="${ink}" stroke-width="5"/><line x1="6" y1="158" x2="58" y2="158" stroke="${ink}" stroke-width="4"/><text x="32" y="178" text-anchor="middle" font-family="SF Mono" font-size="14" fill="${ink}" font-weight="900">ACTION</text>`,
      },
      '留存': {
        bg: '#dcfce7', shirt: '#16a34a',
        hair: `<path d="M 50 72 Q 46 24 100 22 Q 154 24 150 72 Q 148 96 130 88 L 110 60 L 90 88 L 70 60 L 52 88 Q 50 96 50 72 Z" fill="#c2410c"/>`,
        face: `<path d="M 70 96 Q 84 82 98 96" stroke="${ink}" stroke-width="6" fill="none" stroke-linecap="round"/><path d="M 102 96 Q 116 82 130 96" stroke="${ink}" stroke-width="6" fill="none" stroke-linecap="round"/><path d="M 72 124 Q 100 152 128 124" stroke="${ink}" stroke-width="7" fill="#e63946" stroke-linecap="round"/>`,
        prop: `<path d="M 162 158 Q 172 140 188 148 Q 180 168 162 168 Z" fill="#e63946" stroke="${ink}" stroke-width="4"/><text x="172" y="162" text-anchor="middle" font-size="16" fill="#fff">♥</text>`,
      },
      '声音': {
        bg: '#cffafe', shirt: '#0891b2',
        hair: `<path d="M 52 68 Q 50 26 100 24 Q 150 26 148 72 Q 140 100 100 104 Q 60 100 52 68 Z" fill="#1a1a1a"/>`,
        face: `<circle cx="80" cy="96" r="12" fill="#fff" stroke="${ink}" stroke-width="4"/><circle cx="80" cy="98" r="4" fill="${ink}"/><circle cx="120" cy="96" r="12" fill="#fff" stroke="${ink}" stroke-width="4"/><circle cx="120" cy="98" r="4" fill="${ink}"/><ellipse cx="100" cy="132" rx="16" ry="18" fill="${ink}"/>`,
        prop: `<path d="M 36 88 Q 20 100 20 120 Q 20 140 36 152" stroke="${ink}" stroke-width="6" fill="none" stroke-linecap="round"/><path d="M 164 88 Q 180 100 180 120 Q 180 140 164 152" stroke="${ink}" stroke-width="6" fill="none" stroke-linecap="round"/><line x1="36" y1="120" x2="164" y2="120" stroke="${ink}" stroke-width="5"/>`,
      },
      '合规': {
        bg: '#f0fdf4', shirt: '#15803d',
        hair: `<path d="M 48 66 Q 46 30 100 28 Q 154 30 152 66 Q 150 104 100 108 Q 50 104 48 66 Z" fill="#4a3728"/>`,
        face: `<rect x="68" y="92" width="28" height="14" rx="4" fill="none" stroke="${ink}" stroke-width="4"/><rect x="104" y="92" width="28" height="14" rx="4" fill="none" stroke="${ink}" stroke-width="4"/><line x1="82" y1="99" x2="82" y2="99" stroke="${ink}" stroke-width="6"/><line x1="118" y1="99" x2="118" y2="99" stroke="${ink}" stroke-width="6"/><line x1="78" y1="130" x2="122" y2="130" stroke="${ink}" stroke-width="5" stroke-linecap="round"/>`,
        prop: `<path d="M 158 148 L 172 136 L 192 148 L 192 178 Q 192 196 175 196 L 175 196 Q 158 196 158 178 Z" fill="#4361ee" stroke="${ink}" stroke-width="5"/><path d="M 168 168 L 176 176 L 188 160" stroke="#fff" stroke-width="5" fill="none" stroke-linecap="round"/>`,
      },
      '运营': {
        bg: '#ffedd5', shirt: '#ea580c',
        hair: `<path d="M 46 70 Q 42 18 100 20 Q 158 22 154 74 Q 150 108 128 96 Q 100 50 72 96 Q 50 108 46 70 Z" fill="#2b1810"/>`,
        face: `<path d="M 68 94 Q 82 80 96 94" stroke="${ink}" stroke-width="6" fill="none" stroke-linecap="round"/><path d="M 104 94 Q 118 80 132 94" stroke="${ink}" stroke-width="6" fill="none" stroke-linecap="round"/><path d="M 74 122 Q 100 146 126 122" stroke="${ink}" stroke-width="7" fill="#e63946" stroke-linecap="round"/>`,
        prop: `<path d="M 150 148 L 188 132 L 188 168 L 150 184 Z" fill="#ffd23f" stroke="${ink}" stroke-width="5"/><circle cx="142" cy="166" r="14" fill="#e63946" stroke="${ink}" stroke-width="4"/>`,
      },
      '领域': {
        bg: '#ede9fe', shirt: '#6d28d9',
        hair: `<path d="M 48 64 Q 44 22 100 20 Q 156 22 152 64 Q 148 112 100 116 Q 52 112 48 64 Z" fill="#78716c"/><path d="M 70 108 Q 100 130 130 108" stroke="#78716c" stroke-width="8" fill="none"/>`,
        face: `<circle cx="82" cy="98" r="7" fill="${ink}"/><circle cx="118" cy="98" r="7" fill="${ink}"/><path d="M 78 128 Q 100 118 122 128" stroke="${ink}" stroke-width="5" fill="none" stroke-linecap="round"/>`,
        prop: `<rect x="154" y="138" width="40" height="52" rx="6" fill="#4361ee" stroke="${ink}" stroke-width="5"/><line x1="162" y1="154" x2="186" y2="154" stroke="#fff" stroke-width="3"/><line x1="162" y1="166" x2="182" y2="166" stroke="#fff" stroke-width="3"/><line x1="162" y1="178" x2="186" y2="178" stroke="#fff" stroke-width="3"/>`,
      },
    };
    const r = roles[role] || roles['记者'];
    return `
      <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:100%;">
        <rect x="8" y="8" width="184" height="184" rx="36" fill="${r.bg}" stroke="${ink}" stroke-width="6"/>
        <ellipse cx="100" cy="178" rx="62" ry="28" fill="${r.shirt}" stroke="${ink}" stroke-width="5"/>
        <rect x="78" y="148" width="44" height="36" fill="${skin}" stroke="${ink}" stroke-width="4"/>
        <ellipse cx="100" cy="108" rx="52" ry="56" fill="${skin}" stroke="${ink}" stroke-width="6"/>
        ${r.hair}
        <ellipse cx="38" cy="112" rx="9" ry="14" fill="${skin}" stroke="${ink}" stroke-width="4"/>
        <ellipse cx="162" cy="112" rx="9" ry="14" fill="${skin}" stroke="${ink}" stroke-width="4"/>
        ${r.face}
        ${r.prop}
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
