// W27D01 · 共享角色数据 + 构造器（hook/compare/proof 复用）
window.D01_AGENTS = [
  {h:"#ff9478",b:"#ff7a59",p:"🎬",n:"编导"},
  {h:"#6fd6a6",b:"#48c78e",p:"✍️",n:"编剧"},
  {h:"#6fb0e0",b:"#3e8ed0",p:"📋",n:"记者"},
  {h:"#f7bd86",b:"#f4a261",p:"✂️",n:"剪辑"},
  {h:"#c79cff",b:"#b07cff",p:"📣",n:"运营"},
];
// 返回单个角色 innerHTML（外层 .char 由调用方建，便于定位/缩放）
window.charInner = function(a, opts){
  opts = opts || {};
  const showName = opts.name !== false;
  return `
    <div class="arm l" style="background:${a.b}"></div>
    <div class="arm r" style="background:${a.b}"></div>
    <div class="body" style="background:${a.b}"></div>
    <div class="head" style="background:${a.h}">
      <div class="prop">${a.p}</div>
      <div class="brow l"></div><div class="brow r"></div>
      <div class="eye l"><div class="pupil"></div></div>
      <div class="eye r"><div class="pupil"></div></div>
      <div class="mouth"></div>
    </div>
    ${showName?`<div class="nm">${a.n}</div>`:""}`;
};
// 在容器内按横排建 5 个角色，返回元素数组
window.buildRow = function(container, xs, top, expr, opts){
  return window.D01_AGENTS.map((a,i)=>{
    const d=document.createElement("div");
    d.className="char "+(expr||"")+ (opts&&opts.cls?(" "+opts.cls):"");
    d.id=(opts&&opts.idprefix||"c")+i;
    d.style.left=xs[i]+"px"; d.style.top=top+"px";
    if(opts&&opts.scale) d.style.transform="scale("+opts.scale+")";
    d.innerHTML=window.charInner(a,opts);
    container.appendChild(d);
    return d;
  });
};
