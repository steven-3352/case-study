---
name: project_shortfilm-memory-piece
description: 40 岁北方男 + 南方女(北方长大)居家温馨回忆短片项目 · 2026-07-12 定型 · 写实电影感 · 人设已锁
metadata: 
  node_type: memory
  type: project
  originSessionId: 9b1fed5d-f0e8-44bb-92c5-cf637a4f1774
---

# 40 岁夫妻回忆短片 · 项目基线

**定型时间**：2026-07-12
**当前代号**：`shortfilm_memory`（用户未拍板正式代号；勿擅自改名）
**主题词**：回忆、失恋、不得已、思念（用户原话）
**基调**：居家、生活片段、温馨、主打回忆

## 人物基线（已锁 · 勿改设定）

**男主**：40 岁、北方人、圆寸、浓眉、微胖、170 cm
**女主**：40 岁、南方人（在北方长大）、长发、鸭蛋脸、167 cm、100 斤（约 50 kg）
**女主对男主的爱称**：**熊熊**（2026-07-12 冬夜卧室片段揭示；不是男主爱称女主，是女主给男主起的爱称）

## 人设参考图（reference lock）

- 男主：`tmp/shortfilm_memory/character_design/male_v1_front.png` (2:3 竖构，客厅端茶望远，反 AI 磨皮达标)
- 女主：`tmp/shortfilm_memory/character_design/female_v1_front.png` (中转层判成 3:2 横构，用户接受，做 reference 用不受影响)
- 画风锚点：Kodak Portra 400 胶片、50mm 浅景深、暖色家居自然光、写实电影感、**反 AI 磨皮/磨白光**
- 生成脚本：`pipeline/gen_character_portrait.py`（含 STYLE_ANCHOR + MALE_PROMPT + FEMALE_PROMPT，可直接抄改）

## 技术栈

- 出图：GPT-image-2 via tonbirds 中转（`GPT_IMAGE_*` env 三件套）
- 人物一致性：多帧场景用 `client.images.edit` + 人设图作 reference 锁面孔
- 输出目录：`tmp/shortfilm_memory/`（临时位置；用户如要挪正式目录再迁）
- 画布：1024×1536 原生（GPT-image-2 上限）→ 后期升采样 1080×1620 / 1080×1920

## Why

用户 2026-07-12 明确"这个小短片以后任务定型了"，意味着后续会继续做（可能多个片段/多次迭代），需要人设图、画风、色调、代号一次锁定。避免每次重问、避免长相漂移。

## How to apply

**触发关键词**：短片、回忆、思念、熊熊、40 岁夫妻、居家片段、南方冬夜卧室、我们那部片子
- 触发即进本项目上下文，不重新对齐人设/画风
- 出新片段时用 `pipeline/gen_character_portrait.py` 的 STYLE_ANCHOR 复用画风
- 人物一致性走 image.edit + 上面两张 png 作 reference
- **不属于主引擎 pipeline**：不进 `queue/topics.yaml`，不走 [[feedback_multi-role-collab]] 15 步。这是个人情感副线短片
- 不属于 [[project_audience-open-skin-per-topic]]（该规则针对 AI 工具选题）

## 已完成片段

- **S01 · 南方冬夜卧室**（2026-07-12 · 24s · 720×1280）
  - 4 段 Grok 视频（S01/S02/S03/S04 · 5+5+8+6=24s）
  - 4 张 GPT-image-2 静图作首帧锁一致性
  - 5 条 edge-tts 中文对白（女·男·女+男·男）
  - BGM《迟来情深》0:40-1:04 主歌段
  - 硬字幕（libass · PingFang fallback）
  - 成品：`tmp/shortfilm_memory/scenes/S01_winter_bedroom/final/S01_winter_bedroom_final.mp4`

## BGM 认证（金曲）

- 文件：`assets/audio/hook_pack_01/我爱的女孩叫丫头-最终版本.mp3`
- **真名**：《迟来情深》（"我爱的女孩叫丫头"是副歌 hook / suno 生成 / 作者 jackfor001 / 4'33"）
- 歌词与本项目主题**严丝合缝**：40 岁 / 五年 / 断崖似的转身 / 离别来得太匆忙 / 从此再没有你的消息 / 昔日的爱人 曾经最亲的人 如今隔着咫尺却成了最陌生的路人
- 后续片段可以继续复用不同段落做 BGM，建立"同一主题曲"的整片氛围锚

## 计划中片段

- **S01 · 南方冬夜卧室**：女主叉腰假生气"不开空调你要冻死熊熊吗" → 男主掀被招手 → 相拥入睡 → 清晨男主亲吻熟睡的女主（4 张关键帧 · in progress）
