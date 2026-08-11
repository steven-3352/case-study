---
name: project_huashu-design-skill-install
description: huashu-design(花叔Design)skill 已装入 .agents/skills/,做 HTML 视觉产出(原型/落地页/幻灯片/信息图/风格探索)时挂载;核心=100%三方向硬门+反AI slop
metadata:
  node_type: memory
  type: reference
---

# huashu-design skill 安装登记(case-study 项目)

## 是什么

花叔(alchaincyf)的 **huashu-design** —— 把自己当**设计师**(不是程序员)的 HTML 视觉产出 skill。
适用:高保真原型 / 落地页·首页·官网视觉 / 幻灯片 deck / 信息图 / 动画 demo / 视觉方向探索 / 专家评审。
**不适用**:生产级 Web App / 需后端的系统(那走 `02_WORKFLOW.md` 正常工种协作)。

## 安装内容(局部装)

- 路径:`.agents/skills/huashu-design/`
- 装了:`SKILL.md`(61KB 方法论)+ `references/`(32 篇设计知识,如 design-styles / typography / critique-guide / brand-asset-protocol)
- **未装**:`assets/`(bgm mp3 · 28MB)+ 视频/pptx 导出 `scripts/`。原因:git clone 超时 + 这些只服务动画导出MP4/GIF、HTML→PPTX,与 web 设计需求无关。
- 用到动画导出/PPTX 导出时,从 upstream `github.com/alchaincyf/huashu-design` 补 `scripts/`+`assets/`。
- upstream 默认分支不是 main(contents API 用 master),clone 因大 mp3 超时,用 GitHub contents API base64 逐文件拉的。

## 触发登记

已在 `docs/RULES/06_SKILL_TRIGGERS.md` 加「网页/幻灯片视觉设计」一节。触发词:做原型/mockup/HTML页面/落地页/首页/官网视觉/PPT/幻灯片/信息图/设计风格/定风格/评审/"做个好看的·提升档次·不够高级"。

## 三个核心铁律(用它时必守)

1. **100% 三方向硬门**:任何新视觉设计先出 3 个差异化真实初稿给用户选,**指定风格/品牌也不豁免**。与项目 [[reference_paperdoll-mv-packaging-skill]] 无关,与 `03_VISUAL_CREATIVE_GATE.md`(20→8-12)同源同向——web/deck 走三方向,视频分镜走 20→8-12。
2. **反 AI slop = 禁AI味的加详版**:真正禁的是偷懒解(均匀深蓝 `#0D1117`+青紫霓虹 glow),有作者意图的暗色不在禁区。以 `04_CONTENT_CONSTRAINTS.md §3` 为最终约束。slop 清单:紫渐变/emoji当图标/圆角卡+左彩条/SVG手画产品图/Inter当display字体。
3. **Placeholder > 烂实现**、系统优先不填充、核心资产协议(要真 logo,不许瞎画)。

## 自带 3 套风格系统(可当三方向脚手架)

- **Pentagram**:黑白瑞士网格 + 强字体层级 + 红强调 `#E63946`(理性克制)
- **Build**:奢侈品级留白 70%+ + 超细字重 + 暖金 `#D4A574`(奢华极简)
- **Takram**:柔和科技感 + 自然色(米/灰/绿)+ 圆角 + 图表如艺术(东方温暖)

## 当前用途(2026-08-11 起)

平台架构重构 [[project_platform-refactor.md]] 的**首页视觉**:owner 已批"先装成项目 skill 再用",装完按三方向硬门出 3 版首页初稿(现有 preview/index.html interfere 编辑白算其中一版的候选)。preview 部署在 nginx `/preview/`。
