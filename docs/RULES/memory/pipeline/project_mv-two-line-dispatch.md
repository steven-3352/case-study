---
name: project_mv-two-line-dispatch
description: 做片触发后先分派两套出片引擎(生成式 conductor vs 程序化 paperdoll),别硬走 A→F
metadata:
  type: project
---

「做片」触发词命中后,**第一步不是进阶段,是分派**:本仓库有两套出片引擎,触发词相同、目录/命令完全不同,走错线会把用户带进跑不通的流程。

**判据**(问用户或从物料推断两件事):主体是不是真人照片 / 要不要调生成模型出画面。
- **线 G · 生成式(默认 · 维护中 · 能跑)**:真人照片 + 调图像/i2v 模型。引擎 `mv-agent/conductor` 六步 `00_intake→01_analysis→02_storyboard→03_keyframes→04_shots→05_delivery`,`run <片名>` 驱动,每步 approval 拍板。核心逻辑已收敛进 `src/mvstudio`(见 [[project_lyrics-shared-core-convergence]])。
- **线 P · 程序化 paperdoll**:美术风/纸娃娃、无写实照片、本地逐帧渲染。这才是 `11_MV_DIALOGUE_PLAYBOOK.md` 正文 A→F 描述的那条。参考实现 `pipeline/voice_room/mingyue/`。

**已知勘误(未修)**:playbook 正文里的 `python3 -m mv_engine.tools.render_cached` / `solve_shots` 命令入口**不存在**——`pipeline/mv_engine/` 下只有 `__init__.py`。真实渲染脚本在 `pipeline/voice_room/*.py`(`mingyue_render.py` / `paperdoll_engine.py` / `mingyue_atoms.py`)。修命令路径属 `docs/RULES/` 改动,需 owner 拍板。

**Why:** 两套引擎撞同一触发词,playbook 原来硬写"按 6 阶段 A→F 主导",默认把用户带进线 P——而线 P 的示范渲染命令起手就 `ModuleNotFoundError`。能跑、在维护、核心已收敛的其实是线 G(conductor)。

**How to apply:** 命中做片触发词 → 先读 `11_MV_DIALOGUE_PLAYBOOK.md`「路线分流」段判 G/P → 拿不准就问"真人照片还是美术风、要不要调模型" → 默认线 G。禁止不分派直接进 A→F。

反例:❌ 一命中"做片"就照 playbook 跑 `mv_engine.tools.render_cached`(入口不存在,当场挂)。❌ 拿着真人照片却走线 P 的求解器/帧渲(范式不匹配)。

关联:[[project_lyrics-shared-core-convergence]](线 G 核心已收敛)。
