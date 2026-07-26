---
name: visual-form-inspiration-library
description: 视觉形式灵感库机制——扩宽形式菜单让 agent 考虑更多表现方向；catalog.yaml 家族化 + resource_pool.yaml 资源落脚点；侦察动作待建
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d074aece-f256-4b3a-a861-3833b7f6a5b5
---

用户痛点：当前形式能满足脚本，但怕形式策略官每次只从熟路（P001 截图/GSAP/真人）里选，没见过更多可能。用户常主动推荐免费资源（Godot、yt-dlp 等）就是想给 agent「扩见识」。

**已落地（2026-07-11）：**
- `assets/formats/catalog.yaml` 扩成家族化菜单：10 家族 / 17 形式，每条带 `data_lever`（数据杠杆）/`cost`/`tech_risk` 三字段。新增家族：text_motion(kinetic typography)、data_viz、engine_3d、meme、paper_physical(whiteboard)。规则加 `min_distinct_families:3` + `every_shot_needs_data_lever`。
- `assets/formats/resource_pool.yaml`：给用户发现的免费资源一个带 license 的家。分 research_tools（yt-dlp/agent-reach 采料侦察工具，NOT 表现形式）+ asset_pool + engine_pool（Godot 等）。

**Why:** 扩菜单但守铁律 7「形式为数据服务」——赢在数据杠杆，不为炫而炫。项目标杆(WaytoAGI/七七/浙大猫学长)都不靠炫画面，是密 VO+干净+信息密度。

**How to apply:**
- 用户再抛新免费资源 → 别只讨论，登记进 resource_pool.yaml，标 license + data_lever + status，再进候选池。
- yt-dlp 类下载工具：仅研究拆解 + 拉 CC0/CC-BY 素材；**下载内容自带版权，禁剪进商用成片**。
- **免费 ≠ 可商用**：CC-BY-NC/GPL 资产禁用；引擎本身 vs 产出 vs 第三方资产三层 license 分开核。
- engine_3d（Godot/Three/Blender）落地前必走 SYSTEM §4.2 五维打分 + motion_tech_plan.md。

**待建（下一步 · 已与用户对齐设计，未实现）：** 「视觉侦察」动作——防形式主义三原则：①有数据缺口才触发（如钩子偏弱），非每条必跑；②带回参考必绑数据杠杆，答不出就扔；③「看完不采纳」是合法输出。等下次碰到钩子弱的选题实地跑一次验证。

相关：[[feedback_no-default-tech-stack]] [[feedback_audience-first]] [[feedback_dense-vo-no-bgm-default]]
