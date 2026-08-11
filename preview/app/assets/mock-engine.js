/* ============================================================
   模拟引擎 Studio —— 前台完整流程的"假后端"
   忠实架构:引擎唯一持有并写状态(D8)、node_state 状态机 + 级联失效(D9)、
   成本账本(D10)、事件账本(D8)、中间产物(D18)。前端只读渲染 + 上报意图(D17)。
   数据落 localStorage,刷新不丢。所有页面只通过 window.Studio 交互。
   ============================================================ */
window.Studio = (function(){
  "use strict";
  const LS_KEY = "studio.state.v3";
  const PRICE = { image: 0.5, video: 0.6 /* 元/秒 */, llm: 0.02 };
  const ICON = { done:"✓", awaiting:"⏸", running:"⋯", pending:"", rejected:"↩" };
  const STATE_ZH = { done:"已通过", awaiting:"待拍板", running:"生成中", pending:"未开始", rejected:"已打回" };

  let state = null;
  const listeners = [];

  function now(){ return Date.now(); }
  function uid(p){ state.seq += 1; return (p||"id")+"-"+state.seq.toString(36)+"-"+now().toString(36).slice(-4); }
  function save(){ try{ localStorage.setItem(LS_KEY, JSON.stringify(state)); }catch(e){} notify(); }
  function notify(){ listeners.forEach(fn=>{ try{fn(state);}catch(e){} }); }
  function load(){
    try{ const raw = localStorage.getItem(LS_KEY); if(raw){ state = JSON.parse(raw); return; } }catch(e){}
    state = null;
  }

  /* ---- 占位素材:暖调纸感 SVG(零 AI 味 · 无蓝紫/无光斑) ---- */
  function placeholder(label, ratio, variant){
    const dims = {"9:16":[360,640],"16:9":[640,360],"3:4":[480,640],"1:1":[520,520],"video":[640,360]}[ratio||"16:9"]||[640,360];
    const [w,h] = dims;
    const paper = "#f3efe8", ink = "#1a1714", gold = "#b08d57", faint = "#9c938a";
    const play = variant==="video" ? `<circle cx="${w/2}" cy="${h/2}" r="30" fill="none" stroke="${gold}" stroke-width="2"/><path d="M${w/2-8} ${h/2-13} L${w/2+16} ${h/2} L${w/2-8} ${h/2+13} Z" fill="${gold}"/>` : "";
    const star = variant==="selected" ? `<text x="${w-26}" y="30" font-size="22" fill="${gold}">★</text>` : "";
    const svg = `<svg xmlns='http://www.w3.org/2000/svg' width='${w}' height='${h}' viewBox='0 0 ${w} ${h}'>`+
      `<rect width='100%' height='100%' fill='${paper}'/>`+
      `<rect x='10' y='10' width='${w-20}' height='${h-20}' fill='none' stroke='${ink}' stroke-opacity='0.10'/>`+
      `<rect x='10' y='10' width='${w-20}' height='${h-20}' fill='none' stroke='${gold}' stroke-opacity='0.22' stroke-dasharray='2 6'/>`+
      play + star +
      `<text x='24' y='${h-40}' font-family='Inter,Arial' font-size='15' fill='${ink}' fill-opacity='0.82'>${escapeXml(label)}</text>`+
      `<text x='24' y='${h-20}' font-family='Inter,Arial' font-size='11' fill='${faint}' letter-spacing='1'>AI 占位 · 待真实产物替换</text>`+
      `</svg>`;
    return "data:image/svg+xml;utf8,"+encodeURIComponent(svg);
  }
  function escapeXml(s){ return String(s).replace(/[<>&]/g,c=>({"<":"&lt;",">":"&gt;","&":"&amp;"}[c])); }

  /* ---- 产物生成:一步可多产物(D18) ---- */
  function ratioOf(project){ const d=project.data||{}; return d.ratio || (project.recipe==="mv"||project.recipe==="ad2"?"9:16":"16:9"); }
  function makeArtifacts(project, step){
    const art = step.art, out = [];
    const ratio = ratioOf(project);
    if(art.type==="grid"){
      art.cells.forEach((c,i)=>{
        const isVid = /mp4|视频/.test(c) || step.unit==="video";
        out.push({ id:uid("art"), node_id:step.id, kind:isVid?"video":"image",
          status:(step.id==="03_select"&&i===0)?"selected":"candidate",
          label:c, address:placeholder(c, isVid?"video":ratio, isVid?"video":(step.id==="03_select"&&i===0?"selected":"")) });
      });
    } else if(art.type==="video"){
      out.push({ id:uid("art"), node_id:step.id, kind:"video", status:"selected",
        label:art.label, address:placeholder(art.label,"video","video") });
    } else {
      out.push({ id:uid("art"), node_id:step.id, kind:"doc", status:"selected",
        label:art.label, address:placeholder(art.label, ratio) });
    }
    return out;
  }
  function stepCost(project, step){
    if(step.unit==="image"){ const n=(step.art.cells||[]).length||4; return +(PRICE.image*n).toFixed(4); }
    if(step.unit==="video"){ const n=(step.art.cells||[]).length||3; return +(PRICE.video*3*n).toFixed(4); }
    return PRICE.llm;
  }

  /* ---- 事件账本(D8 追加式) ---- */
  function logEvent(project, kind, msg, src){
    project.events.unshift({ id:uid("ev"), ts:now(), kind, msg, src:src||"" });
    if(project.events.length>60) project.events.length=60;
  }
  /* ---- 成本账本(D10) ---- */
  function accrue(project, step){
    const cost = stepCost(project, step);
    project.jobs.unshift({ id:uid("job"), node_id:step.id, provider: step.unit==="video"?"seedance-2.0":(step.unit==="image"?"image-gen":"llm"),
      status:"done", estimated_cost:cost, actual_cost:cost, unit:step.unit||"llm", ts:now() });
    return cost;
  }
  function costTotal(project){
    const t = { llm:0, image:0, video:0, total:0 };
    (project.jobs||[]).forEach(j=>{ t[j.unit==="video"?"video":(j.unit==="image"?"image":"llm")]+=j.actual_cost; t.total+=j.actual_cost; });
    return t;
  }

  /* ---- 项目实例化:从配方长出 node_state 序列 ---- */
  function nodesFromRecipe(recipeKey){
    const r = RECIPES[recipeKey];
    return r.steps.map((s,i)=>({ node_id:s.id, n:s.n, status: i===0?"awaiting":"pending", artifacts:[], needsCostConfirm:false, meta:{} }));
  }
  function firstOpenIndex(project){
    const i = project.nodes.findIndex(n=>n.status==="awaiting"||n.status==="running");
    if(i>=0) return i;
    const p = project.nodes.findIndex(n=>n.status==="pending");
    return p>=0 ? p : project.nodes.length-1;
  }

  /* ---- 状态机推进:意图 → 引擎写状态(D9 级联) ---- */
  function recipeStep(project, node){ return RECIPES[project.recipe].steps.find(s=>s.id===node.node_id); }

  // 让某步"跑完停靠":生成产物、必要时记账,落 awaiting(带成本门的先不记账)
  function materialize(project, idx){
    const node = project.nodes[idx];
    const step = recipeStep(project, node);
    if(step.costGate){
      node.status = "awaiting"; node.needsCostConfirm = true; node.artifacts = [];
      logEvent(project, "engine", `<b>${step.n} ${step.title}</b> 待成本确认(confirm-cost),确认后才付费生成`, "engine");
      return;
    }
    if(step.costly){ const c = accrue(project, step); logEvent(project, "engine", `记账:<b>${step.n} ${step.title}</b> 实际成本 ¥${c.toFixed(2)}`, "engine"); }
    node.artifacts = makeArtifacts(project, step);
    node.status = "awaiting"; node.needsCostConfirm = false;
    logEvent(project, "engine", `<b>${step.n} ${step.title}</b> 跑完,停在拍板点(awaiting_approval)`, "engine");
  }

  function advance(project, fromIdx){
    // 当前步 done → 推进下一 pending 步"跑起来并停靠"
    const next = project.nodes[fromIdx+1];
    if(!next){
      project.status = "done"; project.finishedAt = now();
      logEvent(project, "engine", `配方已到末步,产线走完 → 成片就绪`, "engine");
      return;
    }
    if(next.status==="pending"){ materialize(project, fromIdx+1); }
  }

  function act(projectId, intent, payload){
    const project = getProject(projectId); if(!project) return;
    const idx = (payload && typeof payload.index==="number") ? payload.index : firstOpenIndex(project);
    const node = project.nodes[idx]; if(!node) return;
    const step = recipeStep(project, node);

    if(intent==="ok"){
      if(node.needsCostConfirm){ logEvent(project,"engine",`该步需先确认成本再通过`,"engine"); save(); return; }
      // 首步(物料/想法)通过时若还没产物,先补产物
      if(node.artifacts.length===0 && !step.costGate){ if(step.costly){ const c=accrue(project,step); logEvent(project,"engine",`记账:<b>${step.n} ${step.title}</b> ¥${c.toFixed(2)}`,"engine"); } node.artifacts = makeArtifacts(project, step); }
      node.status = "done";
      logEvent(project, "intent", `通过 <b>${step.n} ${step.title}</b>`, "操作台 → 引擎");
      advance(project, idx);
    } else if(intent==="reject"){
      node.status = "awaiting"; node.needsCostConfirm = false; node.artifacts = [];
      logEvent(project, "intent", `打回 <b>${step.n} ${step.title}</b>`, "操作台 → 引擎");
      let reset = 0;
      for(let k=idx+1;k<project.nodes.length;k++){ const nd=project.nodes[k]; if(nd.status!=="pending"){ nd.status="pending"; nd.artifacts=[]; nd.needsCostConfirm=false; reset++; } }
      // 打回后本步重新"跑一遍"停靠(级联下游作废)
      materialize(project, idx);
      logEvent(project, "engine", `级联作废(D9)—— ${step.n} 之后 <b>${reset}</b> 步重置未开始,重排等重跑`, "engine");
      if(project.status==="done"){ project.status="active"; project.finishedAt=null; }
    } else if(intent==="cost-confirm"){
      const c = accrue(project, step);
      node.needsCostConfirm = false; node.artifacts = makeArtifacts(project, step);
      logEvent(project, "intent", `确认成本 ¥${c.toFixed(2)} · 授权 <b>${step.n} ${step.title}</b> 付费生成`, "操作台 → 引擎");
      logEvent(project, "engine", `authorize_submission 通过 → 生成完成,停在拍板点`, "engine");
    } else if(intent==="shot"){
      logEvent(project, "intent", `逐镜补做 <b>${step.n} ${step.title}</b>(shot 模式 · 只补差镜,不推进状态机)`, "操作台 → 引擎");
    }
    save();
  }

  /* ---- 数据访问 ---- */
  function getProject(id){ return state.projects.find(p=>p.id===id) || null; }
  function tenantProjects(){ const t = state.session && state.session.tenant_id; return state.projects.filter(p=>!t || p.tenant_id===t); }

  /* ---- 种子数据(首次进站即有内容看) ---- */
  function seed(){
    state = { seq:0, session:null, users:[], tenants:[], projects:[] };
    const tenant = { id:"t-demo", name:"演示工作区", config:{ hard_limit: 200 } };
    state.tenants.push(tenant);
    state.users.push({ id:"u-demo", username:"demo", password:"demo123", tenant_id:tenant.id, role:"owner" });

    // 项目 1:MV,停在关键帧待拍板(前两步已过)
    const p1 = newProjectRaw("t-demo","mv","《夏夜》· 城市漫游 MV",{ intent:"城市夜景、霓虹、青春感", ratio:"9:16" });
    driveTo(p1, "03_keyframes");
    // 项目 2:带货,停在需求分析
    const p2 = newProjectRaw("t-demo","ad","保温杯 · 冬季带货",{ brief:"316 不锈钢 · 24h 保温 · 送女友", ratio:"9:16" });
    driveTo(p2, "01_analysis");
    // 项目 3:动作迁移,停在成本门(演示建议包)
    const p3 = newProjectRaw("t-demo","ad2","爆款跳舞 · 拍同款",{ brief:"套用热门运镜,换我的产品", ratio:"9:16" });
    driveTo(p3, "04_shots");
    // 项目 4:图片,已完成(进作品库)
    const p4 = newProjectRaw("t-demo","img","猫咖店门口 · 赛博朋克",{ idea:"赛博朋克风的猫咖店门口,暖光", ratio:"3:4", count:"4" });
    driveToDone(p4);
    // 项目 5:MV 已完成(进作品库)
    const p5 = newProjectRaw("t-demo","mv","《告白》· 校园回忆",{ intent:"暖色、胶片颗粒、初恋", ratio:"9:16" });
    driveToDone(p5);
    state.projects.push(p1,p2,p3,p4,p5);
    save();
  }
  function newProjectRaw(tenantId, recipeKey, title, data){
    return { id:uid("prj"), tenant_id:tenantId, recipe:recipeKey, subProject:RECIPES[recipeKey].subProject,
      title, data:data||{}, status:"active", nodes:nodesFromRecipe(recipeKey), jobs:[], events:[],
      createdAt: now(), finishedAt:null };
  }
  // 把项目推进到 targetNodeId(之前的步全 done 并带产物),target 落 awaiting
  function driveTo(project, targetNodeId){
    logEvent(project, "engine", `载入配方 <b>${RECIPES[project.recipe].name}</b> · ${project.nodes.length} 步`, "engine");
    for(let i=0;i<project.nodes.length;i++){
      const node = project.nodes[i]; const step = recipeStep(project, node);
      if(node.node_id===targetNodeId){ materialize(project, i); break; }
      if(step.costly && !step.costGate) accrue(project, step);
      node.artifacts = makeArtifacts(project, step); node.status="done";
      logEvent(project, "engine", `<b>${step.n} ${step.title}</b> 已通过`, "engine");
    }
  }
  function driveToDone(project){
    for(let i=0;i<project.nodes.length;i++){
      const node = project.nodes[i]; const step = recipeStep(project, node);
      if(step.costly) accrue(project, step);
      node.artifacts = makeArtifacts(project, step); node.status="done"; node.needsCostConfirm=false;
    }
    project.status="done"; project.finishedAt = now() - 86400000;
    logEvent(project, "engine", `产线走完 → 成片就绪`, "engine");
  }

  function ensureState(){ load(); if(!state || !state.projects) seed(); }

  /* ============================ 公开 API ============================ */
  const api = {
    ICON, STATE_ZH, PRICE, placeholder,
    onChange(fn){ listeners.push(fn); return ()=>{ const i=listeners.indexOf(fn); if(i>=0) listeners.splice(i,1); }; },
    reset(){ seed(); return state; },

    auth:{
      current(){ return state.session; },
      login(username, password){
        const u = state.users.find(x=>x.username===username);
        if(!u){ // 演示:未知用户名自动注册
          const t = { id:uid("t"), name:username+" 的工作区", config:{hard_limit:200} };
          state.tenants.push(t);
          const nu = { id:uid("u"), username, password, tenant_id:t.id, role:"owner" };
          state.users.push(nu);
          state.session = { user_id:nu.id, username, tenant_id:t.id };
          save(); return { ok:true, created:true };
        }
        if(u.password!==password) return { ok:false, error:"密码不正确(演示账号 demo / demo123)" };
        state.session = { user_id:u.id, username:u.username, tenant_id:u.tenant_id };
        save(); return { ok:true };
      },
      register(username, password){ return api.auth.login(username, password); },
      logout(){ state.session=null; save(); },
      quickDemo(){ return api.auth.login("demo","demo123"); },
    },

    recipes:{ list(){ return RECIPE_ORDER.map(k=>RECIPES[k]); }, get(k){ return RECIPES[k]||null; } },

    projects:{
      list(){ return tenantProjects().slice().sort((a,b)=>b.createdAt-a.createdAt); },
      get(id){ return getProject(id); },
      create(recipeKey, title, data){
        const t = (state.session && state.session.tenant_id) || "t-demo";
        const p = newProjectRaw(t, recipeKey, title||RECIPES[recipeKey].name+" 项目", data||{});
        logEvent(p, "engine", `载入配方 <b>${RECIPES[recipeKey].name}</b> · ${p.nodes.length} 步 · 等待物料`, "engine");
        state.projects.push(p); save(); return p;
      },
      remove(id){ const i=state.projects.findIndex(p=>p.id===id); if(i>=0){ state.projects.splice(i,1); save(); } },
      act, costTotal,
      progress(p){ const done=p.nodes.filter(n=>n.status==="done").length; return { done, total:p.nodes.length }; },
      currentNode(p){ return p.nodes[firstOpenIndex(p)]; },
    },

    works:{
      list(){ // 已完成项目 = 作品
        return tenantProjects().filter(p=>p.status==="done").map(p=>{
          const last = p.nodes[p.nodes.length-1];
          const cover = (last.artifacts[0] && last.artifacts[0].address) || placeholder(p.title, ratioOf(p));
          return { id:p.id, title:p.title, subProject:p.subProject, recipe:p.recipe, cover, ratio:ratioOf(p), finishedAt:p.finishedAt };
        });
      }
    }
  };

  ensureState();
  return api;
})();
