# OpenMontage Production Request · W27D02

> status: production-ready request  
> owner: case-study  
> executor: OpenMontage  
> content_id: W27D02  
> topic: 开完会就走，纪要和待办 AI 已发群  
> platform: douyin  
> aspect_ratio: 9:16  
> target_resolution: 1080x1920  
> target_duration: 35-40s  

## 1. Content Lock

OpenMontage must not rewrite the core argument. It may tighten subtitle line breaks and on-screen labels for readability, but must preserve the approved script, message hierarchy, and CTA.

### Approved Script

Use `scripts/script_three_versions.md` version `vA · 凡尔赛反差版` as the locked script.

```text
0-3s：散会了，同事还在写纪要，我直接走了。
3-11s：不是我摆烂——纪要和待办，群里早自动发好了。
11-22s：我那套系统全程在听：散会就出结构化纪要，每条待办谁负责、什么时候交，自动 @ 到人，到期还提醒。我把它干活的样子做出来给你看。
22-30s：以前开完会最烦的不是会，是会后熬夜整理、追着每个人要进度。
30-36s：现在我只管讨论拍板，记录追办交给它。
36-40s：你们公司开会，纪要是谁在整理？是不是最烦的活？评论区说说，下条我真做给你看。
```

### Core Message

- Value anchor: `开会的价值是讨论和拍板——记录和追待办，根本不该是人干的活。`
- P0 must land:
  - 我开会全程不记录，专注讨论拍板。
  - 散会 AI 自动出结构化纪要 + 待办。
  - 待办自动 @ 到人 + 到期提醒。
  - 这套流程是我真实在用的演绎。
- P1 may support:
  - 同事还在整理白板/回放录音/熬夜写纪要。
  - 人负责讨论拍板，AI 负责记录追办。

### Forbidden Claims

- Do not promise exact accuracy, exact minutes saved, or guaranteed delivery time.
- Do not claim AI replaces human decision-making.
- Do not name or imitate a real SaaS brand UI.
- Do not use real customer data, real company names, or real chat avatars.
- Do not invent case results not present in `insights/core_message.md`.

## 2. Retention Plan

### Beat Timing

| Time | Beat | Viewer Job | Required Visual |
|---|---|---|---|
| 0-3s | Stop-scroll hook | Understand the contrast immediately | Meeting ends, coworkers still organizing notes, protagonist leaves, group notification appears |
| 3-11s | Reveal | Understand this is not laziness | Group message / meeting-minutes card appears as already sent |
| 11-22s | Main proof | Understand action items are assigned and followed | Task cards with owner, deadline, @ mention, reminder state |
| 22-30s | Pain contrast | Feel the old workflow pain | Old workflow: replay audio / rewrite whiteboard / chase progress |
| 30-36s | Value anchor | Remember the principle | People discuss and decide; AI records and follows up |
| 36-40s | Self-proof + CTA | Comment with their own meeting pain | "真在用" signal + comment question |

### Hook Requirement

First 1 second must visually show a workplace meeting context. First 3 seconds must show the contrast: `别人还在整理，我已经走了`.

### CTA

Use the locked CTA:

```text
你们公司开会，纪要是谁在整理？是不是最烦的活？评论区说说，下条我真做给你看。
```

## 3. Visual Constraints

Use `design/design_language.md` as the source of truth.

### Palette

| Token | Hex | Use |
|---|---|---|
| canvas | `#F6F7F9` | UI canvas and neutral background |
| surface | `#FFFFFF` | cards |
| ink | `#17202A` | main text |
| muted | `#6B7280` | secondary labels |
| accent | `#1F7AFF` | group message, @ state, primary highlight |
| success | `#18A058` | sent / completed / reminder active |
| warning | `#F59E0B` | deadline / bell |
| contrast | `#EF4444` | old workflow pain |

### Typography

- Chinese UI font priority: `PingFang SC`, `Hiragino Sans`, `Arial`, `sans-serif`.
- Hook display: 76-88px, heavy weight.
- Scene headline: 54-64px, heavy weight.
- Card body: 34-42px.
- Data labels: 30-36px, high contrast.

### Layout Rules

- No visible card inside another decorative card.
- Max 2 concurrent overlay layers.
- Captions must not cover owner/deadline/task fields.
- Avoid brand-like UI. Use generic abstract chat/task cards.
- Avoid random gradients, glassmorphism, neon tech backgrounds, and decorative visual noise.

## 4. Asset Policy

This production pass must not be a reuse of the existing P004 visual path. Existing files may be used only as references, not as primary visual assets.

### Required New Assets

| Asset | Required Count | Preferred Provider | Purpose |
|---|---:|---|---|
| True motion hook clip | 1 | Grok `grok-imagine-video` or real stock B-roll | Meeting-room stop-scroll hook |
| True motion contrast clip | 1 | Grok `grok-imagine-video` or real stock B-roll | Old workflow pain contrast |
| UI support images | 2 | GPT Image 2 | Minutes card and task tracking card base visuals |
| UI motion layer | 3 scenes | Remotion or HyperFrames | Minutes reveal, task assignment, reminder state |
| Voiceover | 1 | MiniMax TTS | Locked script narration |
| BGM bed | 1 | local library / royalty-free / generated | Light workplace rhythm |
| SFX | 2-3 | local / royalty-free | group ding, reminder bell, transition tick |

### Allowed Sources

- GPT Image 2 through configured relay.
- Grok `grok-imagine-video` through configured relay.
- MiniMax TTS through configured relay.
- Pexels/Coverr/Archive/Wikimedia if real B-roll fits and license is traceable.
- Local royalty-free music library if available.

### Disallowed Sources

- Existing P004 illustrations as primary visual assets.
- Real SaaS screenshots.
- Real enterprise chat UI, logos, or customer data.
- Untraceable downloaded social/video materials.

### Cost Cap

Target production cap: `$2.00`.

Suggested allocation:

- Grok video: up to 3 clips, 4-5s each, 480p unless 720p is explicitly needed.
- GPT Image 2: up to 4 medium-quality images.
- MiniMax TTS: 1 full pass + at most 2 short voice samples.
- Music/SFX: prefer local or royalty-free before paid generation.

## 5. Audio And Subtitle Policy

### Voiceover

- Provider: MiniMax TTS.
- Model: `speech-2.8-turbo`.
- Preferred voice: current configured MiniMax Chinese male voice unless a sample review rejects it.
- Tone: light, confident, slightly "凡尔赛", but not salesy.
- Speed target: fit 35-40s without sounding rushed.

### BGM

- Mood: upbeat workplace rhythm, light, clean, not comedic.
- Must not dominate the VO.
- Start immediately at 0s with a small emphasis around the notification moment.
- Fade out under CTA.

### Ducking / Loudness

- VO must remain primary.
- BGM target: approximately -18 to -22 LUFS under speech, or visibly ducked during VO.
- SFX must be short and lower than VO.
- No BGM-only intro.

### Subtitles

Production pass must include platform-safe burned subtitles.

- Subtitle mode: word-group subtitles, not full-line transcript blocks.
- Position: bottom safe zone, above platform UI and not covering task fields.
- Style: white text with dark shadow/stroke; max 2 lines.
- Line length: <= 14 Chinese characters per line where possible.
- Hook subtitle must appear within first 0.5s.
- Subtitles may be suppressed or moved during task-card closeups if they collide with owner/deadline fields.

## 6. Motion Intent

Motion must clarify the workflow, not decorate it.

### Required UI Motions

| Scene | Motion |
|---|---|
| 0-3s hook | group notification card pops in on the beat; protagonist movement remains visible |
| 3-11s minutes | summary card expands from message bubble; three sections reveal in order |
| 11-22s tasks | task cards stack one by one; owner avatar lights; @ mention highlights; deadline chip appears; reminder bell pulses once |
| 22-30s contrast | old workflow side gets red label; new workflow side gets green label; no dense text |
| 30-40s CTA | value anchor resolves into CTA; motion slows for readability |

### No-Go Effects

- No fast kinetic text that reduces comprehension.
- No decorative bokeh/orb backgrounds.
- No spinning cards, heavy 3D flips, or noisy transitions.
- No motion that hides owner/deadline/@ fields.

## 7. Runtime Decision

OpenMontage should present and log runtime options before the final production pass.

Preferred runtime:

- `remotion` if available: best for source/generative video plus React UI overlays and subtitles.

Fallback:

- `hyperframes` if UI motion is HTML/GSAP-native and the runtime is available.
- `ffmpeg` only for rough validation or if both higher-level runtimes are blocked.

The final `render_report` must record:

- runtime selected,
- options considered,
- reason for selection,
- known blockers or substitutions.

## 8. Output Requirements

OpenMontage must output all files under a non-destructive trial path first.

```text
publish/2026-W27/D02-会议纪要/openmontage_production/
├── final.mp4
├── final_silent.mp4
├── contact_sheet.png
├── generation_results.json
├── render_report.json
├── asset_manifest.json
├── edit_decisions.json
├── subtitle.srt
├── review.md
└── decision_log.md
```

Do not overwrite:

```text
publish/2026-W27/D02-会议纪要/douyin/video_with_bgm.mp4
```

Replacement is a `case-study` decision after review.

## 9. Acceptance Gates

### Hard Gates

- Content accuracy: no forbidden claims, no brand imitation, no fake customer data.
- Duration: 35-40s.
- Format: 1080x1920, H.264/AAC, playable by ffprobe.
- Hook: first 3 seconds visually communicate the contrast.
- Subtitle readability: key subtitles readable on mobile-sized frame.
- Task readability: at least one frame clearly shows owner + deadline + @/reminder.
- Audio: VO intelligible throughout; BGM/SFX do not cover speech.
- Traceability: all generated/provider assets listed in `generation_results.json` or `asset_manifest.json`.

### Quality Gates

Score each from 1-10:

| Gate | Pass Threshold |
|---|---:|
| 3s stop-scroll strength | >= 8 |
| script fidelity | >= 9 |
| workflow comprehension | >= 8 |
| visual polish | >= 8 |
| subtitle/audio integration | >= 8 |
| improvement over original P004 version | >= 7 |

### Publish Decision

`case-study` may replace the original Douyin file only if:

- all hard gates pass,
- average quality score >= 8,
- and `improvement over original P004 version >= 7`.

If it fails, keep it as an OpenMontage learning artifact and do not publish.

## 10. Review Questions For Case-Study

OpenMontage should return answers to these questions in `review.md`:

1. Does the first 3 seconds beat the original P004 hook?
2. Does the viewer understand "自动纪要 + 待办 + @ + 到期提醒" without relying only on VO?
3. Did UI motion improve comprehension or just add decoration?
4. Are subtitles readable without covering task fields?
5. Is the video more publishable than the original, or only more novel?
