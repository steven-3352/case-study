/* ============================================================
   配方库(D5:配方是数据,不是代码)
   一引擎多配方:每份配方的 steps 顺序 = 用户操作的每一步(D21)
   引擎按此实例化 project 的 node_state;前端只渲染,不硬编码步骤
   ============================================================ */
window.RECIPES = {
  ad: {
    key:"ad", name:"带货视频", code:"recipe://video/ad",
    subProject:"带货", navGroup:"视频", tag:"商品 → 脚本 → 分镜 → 成片",
    blurb:"输入商品图与卖点,平台顺着脚本 → 分镜 → 生成 → 字幕一步步走。",
    inputs:[
      {key:"product_images", label:"商品图", type:"file", hint:"1–8 张,主图优先"},
      {key:"brief", label:"卖点 brief", type:"textarea", hint:"一句话说清卖什么、给谁"},
      {key:"ratio", label:"成片比例", type:"select", options:["9:16","16:9"]},
    ],
    steps:[
      {n:"00", id:"00_intake", title:"物料录入", tool:"intake_validate",
        sub:"商品图、卖点 brief、成片比例进来,做基础校验。",
        in:[["料","商品图 × N"],["料","卖点 brief"],["比例","9:16 / 16:9"]],
        out:[["产","manifest.yaml"],["产","校验报告"]], art:{type:"badge",label:"物料清单"}},
      {n:"01", id:"01_analysis", title:"需求分析", tool:"llm_analyze",
        sub:"LLM 读懂卖点与目标人群,定成片方向与脚本骨架。",
        in:[["自","00 manifest"]], out:[["产","brief 分析"],["产","脚本骨架"]], art:{type:"badge",label:"需求分析"}},
      {n:"02", id:"02_storyboard", title:"分镜", tool:"llm_storyboard",
        sub:"逐镜脚本。每镜标『展示帧(贴原商品图保真)』还是『生成帧(AI 出画)』。",
        in:[["自","01 分析"]], out:[["产","shots.yaml"],["产","分镜文档"]],
        art:{type:"badge",label:"分镜表 · display / generated 双身份"}},
      {n:"03", id:"03_keyframes", title:"首帧", tool:"gen_keyframe", gate:true, costly:true, unit:"image",
        sub:"每镜首帧图:展示帧直接贴原商品图兜底保真,生成帧走 AI。",
        in:[["自","02 shots"],["自","00 商品图"]], out:[["产","首帧图 × 镜数"]],
        art:{type:"grid",cells:["SH001","SH002","SH003"]}},
      {n:"04", id:"04_shots", title:"视频", tool:"gen_video", gate:true, costly:true, unit:"video",
        sub:"生成帧走 Seedance i2v 动起来;静态 / ken-burns 用本地 ffmpeg 免费兜底。",
        in:[["自","03 首帧"]], out:[["产","每镜 mp4"]], art:{type:"grid",cells:["SH001.mp4","SH002.mp4","SH003.mp4"]}},
      {n:"05", id:"05_delivery", title:"成片", tool:"compose",
        sub:"拼接成片 + 烧字幕(30fps / h264)。",
        in:[["自","04 各镜 mp4"]], out:[["产","final.mp4"],["产","subtitle"]],
        art:{type:"video",label:"带货成片"}},
    ]
  },

  mv: {
    key:"mv", name:"MV 视频", code:"recipe://video/mv",
    subProject:"MV", navGroup:"视频", tag:"歌曲 → 卡点 → 关键帧 → 拼接成片",
    blurb:"上传歌曲自动卡点,分镜与关键帧顺势生成,拼成跟着音乐走的 MV。",
    inputs:[
      {key:"audio", label:"歌曲音频", type:"file", hint:"mp3 / wav"},
      {key:"lyrics", label:"歌词", type:"textarea", hint:"lrc 或纯文本,自动对时间轴"},
      {key:"character", label:"人物图", type:"file", hint:"主角参考图"},
      {key:"intent", label:"创作意图", type:"textarea", hint:"想要的情绪 / 风格 / 故事"},
    ],
    steps:[
      {n:"00", id:"00_intake", title:"物料录入", tool:"intake_validate",
        sub:"音频 + 歌词 + 人物图 + 创作意图进来;探时长,出逐行时间轴。",
        in:[["料","音频 mp3"],["料","歌词 lrc"],["料","人物图"],["意","创作意图"]],
        out:[["产","manifest.yaml"],["产","lyrics_timed.json"]], art:{type:"badge",label:"物料 + 时间轴"}},
      {n:"01", id:"01_analysis", title:"导演规划", tool:"llm_analyze",
        sub:"节拍、段落地图、人物功能、故事框架、片头尾艺术字规划。",
        in:[["自","00 manifest + 时间轴"]],
        out:[["产","music_map.yaml"],["产","character_map"],["产","story.md"]], art:{type:"badge",label:"段落地图"}},
      {n:"02", id:"02_storyboard", title:"分镜", tool:"llm_storyboard",
        sub:"逐镜分镜 + 背景规划。镜数按音乐段落能量切分,铺满整曲。",
        in:[["自","01 music_map + character_map"]],
        out:[["产","shots.yaml"],["产","scene_groups"]], art:{type:"badge",label:"分镜表 · 按段落铺满全曲"}},
      {n:"03", id:"03_keyframes", title:"关键帧", tool:"gen_keyframe", gate:true, costly:true, unit:"image",
        sub:"每镜首帧 9:16;≥2 镜时拼出 storyboard_grid.png 作一屏拍板锚点。",
        in:[["自","02 shots"],["自","00 人物图"]],
        out:[["产","SH###_keyframe.png"],["产","storyboard_grid.png"]],
        art:{type:"grid",cells:["SH001","SH002","SH003","SH004","SH005","拼图锚点"]}},
      {n:"04", id:"04_shots", title:"视频", tool:"gen_video", gate:true, costly:true, unit:"video",
        sub:"每镜 Seedance i2v · 9:16 / 720p。可逐镜(shot)只补差的镜,不重烧全片。",
        in:[["自","03 关键帧"]], out:[["产","每镜 SH###.mp4"]],
        art:{type:"grid",cells:["SH001.mp4","SH002.mp4","SH003.mp4"]}},
      {n:"05", id:"05_delivery", title:"合成成片", tool:"compose",
        sub:"按时间轴拼接 + 烧字幕 + 片头尾艺术字。final.mp4 9:16 / 720p。",
        in:[["自","04 各镜 mp4"],["自","00 音频"],["自","01 title_card"]],
        out:[["产","final.mp4"],["产","subtitle.ass"]], art:{type:"video",label:"MV 成片 · 带音轨"}},
    ]
  },

  ad2: {
    key:"ad2", name:"动作迁移", code:"recipe://video/reference-remake",
    subProject:"动作迁移", navGroup:"视频", tag:"参考视频 → 去身份化 → 套你的人 → 拍同款",
    blurb:"丢一条参考视频,去身份化留下动作骨架,套你的人和风格重新生成。",
    inputs:[
      {key:"ref_video", label:"参考视频", type:"file", hint:"想拍同款的原片"},
      {key:"product_images", label:"商品 / 人物图", type:"file", hint:"要套上去的主体"},
      {key:"brief", label:"卖点 / 意图", type:"textarea", hint:"想要的成片方向"},
      {key:"rights", label:"权利声明", type:"select", options:["我已确认拥有使用权","仅个人学习用途"]},
    ],
    steps:[
      {n:"00", id:"00_intake", title:"物料 + 预检", tool:"intake_validate",
        sub:"参考视频 + 商品图 + 卖点 + 权利声明进来。三级预检:阻塞 / 可修 / 提示。",
        in:[["料","参考视频"],["料","商品图"],["料","卖点"],["权","权利声明"]],
        out:[["产","manifest.yaml"],["产","三级预检报告"]],
        art:{type:"badge",label:"预检报告 · blocking / fixable / advisory"}},
      {n:"01", id:"01_analysis", title:"需求分析", tool:"llm_analyze",
        sub:"读卖点 brief + 商品图,定成片方向与脚本骨架。",
        in:[["自","00 brief + 商品图"]], out:[["产","brief 分析"],["产","脚本骨架"]],
        art:{type:"badge",label:"需求分析"}},
      {n:"02", id:"02_storyboard", title:"分镜", tool:"llm_storyboard",
        sub:"逐镜脚本。每镜标展示帧 / 生成帧,并挂逐镜参考路线。",
        in:[["自","01 分析"]], out:[["产","shots.yaml"]],
        art:{type:"badge",label:"分镜表 · display / generated + 参考路线"}},
      {n:"03", id:"03_keyframes", title:"双身份关键帧", tool:"gen_keyframe", gate:true, costly:true, unit:"image",
        sub:"展示身份:source / composite 双指纹保真兜底;生成身份:AI 直出。",
        in:[["自","02 shots + 路线"]], out:[["产","关键帧 × 镜数(双身份)"]],
        art:{type:"grid",cells:["display·双指纹","generated·AI","display","generated"]}},
      {n:"04", id:"04_shots", title:"视频生成", tool:"gen_video", gate:true, costly:true, unit:"video", costGate:true,
        sub:"生成帧走 Seedance i2v 套你的人重生成;骨架路线消费去身份化产出的骨架 mp4。付费前 confirm-cost 成本确认门。",
        in:[["自","03 关键帧"],["旁","去身份化骨架 mp4"]], out:[["产","每镜 mp4"]],
        art:{type:"grid",cells:["SH001.mp4","SH002.mp4","SH003.mp4"]}},
      {n:"05", id:"05_delivery", title:"合成 + 验收", tool:"compose",
        sub:"VO / BGM / 字幕合成 + 成片验收。",
        in:[["自","04 各镜 mp4"]], out:[["产","final.mp4"],["产","验收报告"]],
        art:{type:"video",label:"拍同款成片"}},
    ]
  },

  img: {
    key:"img", name:"图片", code:"recipe://image/generate",
    subProject:"图片", navGroup:"图片", tag:"一句话 → 专业提示词 → 生成 → 选图",
    blurb:"你只说想要什么,平台替你补齐光线、风格(专业提示词),再生成供你挑图。",
    inputs:[
      {key:"idea", label:"你想要什么", type:"textarea", hint:"一句大白话,例如『赛博朋克风的猫咖店门口』"},
      {key:"count", label:"生成张数", type:"select", options:["4","6","9"]},
      {key:"ratio", label:"画幅", type:"select", options:["1:1","3:4","16:9"]},
    ],
    steps:[
      {n:"00", id:"00_idea", title:"输入想法", tool:"intake_validate",
        sub:"你的一句话想法 + 张数 + 画幅进来。",
        in:[["料","一句话想法"],["料","张数 / 画幅"]], out:[["产","intake.yaml"]], art:{type:"badge",label:"想法录入"}},
      {n:"01", id:"01_prompt", title:"专业提示词", tool:"prompt_pro",
        sub:"提示词积木把你的简单输入拼接 / 优化成含光线、风格、镜头的专业提示词。",
        in:[["自","00 想法"],["数","场景系统提示词"]], out:[["产","professional_prompt"]], art:{type:"badge",label:"专业提示词草案"}},
      {n:"02", id:"02_generate", title:"生成", tool:"gen_image", gate:true, costly:true, unit:"image",
        sub:"按专业提示词批量出图。",
        in:[["自","01 专业提示词"]], out:[["产","候选图 × 张数"]],
        art:{type:"grid",cells:["候选 1","候选 2","候选 3","候选 4"]}},
      {n:"03", id:"03_select", title:"选图", tool:"select",
        sub:"从候选里挑中意的,选中 = selected,其余留作 candidate。",
        in:[["自","02 候选图"]], out:[["产","selected × N"]], art:{type:"grid",cells:["★ 选中","候选","候选"]}},
    ]
  }
};

window.RECIPE_ORDER = ["ad","mv","ad2","img"];
