# OpenMontage Integration

OpenMontage is integrated as an external production plugin for `case-study`.

`case-study` remains the content decision system. It owns topic selection,
insight, script, retention, visual constraints, acceptance gates, and final
publish decisions. OpenMontage owns video-expression production: generated
assets, motion, subtitles, BGM, audio mix, render, and QA.

## Architecture

```text
case-study
  publish/<week>/<content>/openmontage_request.md
        |
        | export request
        v
OpenMontage sibling repo
  projects/<project-name>/
        |
        | production pass
        v
case-study
  publish/<week>/<content>/openmontage_production/
```

OpenMontage is intentionally not vendored into this repository. Keep it as a
sibling checkout so the integration is reversible and OpenMontage can be
upgraded independently.

Recommended sibling path:

```text
/Users/bubu/Documents/projects/OpenMontage
```

## Required Local Setup

OpenMontage needs its own `.env`. See:

```text
integrations/openmontage/openmontage.env.example
```

The current working setup uses:

- GPT Image 2 through an OpenAI-compatible relay
- Grok video through a Grok/xAI-compatible relay
- MiniMax TTS through a MiniMax-compatible relay
- local BGM from `case-study/bgm/`

## Contract

For every OpenMontage production pass, `case-study` must provide one production
request file:

```text
publish/<week>/<content>/openmontage_request.md
```

That request must lock:

- approved script
- core message and forbidden claims
- retention beat timing
- visual constraints
- asset policy
- subtitle policy
- BGM / ducking policy
- motion intent
- runtime decision rules
- output paths
- acceptance gates

OpenMontage must return:

```text
publish/<week>/<content>/openmontage_production/
├── final.mp4                  # ignored by git
├── final_silent.mp4           # ignored by git
├── contact_sheet.png          # ignored by git
├── generation_results.json
├── render_report.json
├── asset_manifest.json
├── edit_decisions.json
├── subtitle.srt
├── review.md
└── decision_log.md
```

Only `case-study` may decide whether to replace the platform publish file.
OpenMontage output must not overwrite `douyin/video_with_bgm.mp4` directly.

## Commands

Export a request into an OpenMontage project:

```bash
python3 integrations/openmontage/scripts/export_request.py \
  --content-dir publish/2026-W27/D02-会议纪要 \
  --project-dir /Users/bubu/Documents/projects/OpenMontage/projects/w27d02-meeting-minutes
```

Collect OpenMontage outputs back into `case-study`:

```bash
python3 integrations/openmontage/scripts/collect_output.py \
  --project-dir /Users/bubu/Documents/projects/OpenMontage/projects/w27d02-meeting-minutes \
  --content-dir publish/2026-W27/D02-会议纪要 \
  --source-dir /Users/bubu/Documents/projects/OpenMontage/projects/w27d02-meeting-minutes/renders_production
```

## W27D02 Reference

Production request:

```text
publish/2026-W27/D02-会议纪要/openmontage_request.md
```

Production output:

```text
publish/2026-W27/D02-会议纪要/openmontage_production/
```

Production builder snapshot:

```text
publish/2026-W27/D02-会议纪要/openmontage_production/build_production_pass.py
```

## Rollback

Rollback is simple because OpenMontage is isolated:

1. Do not replace `douyin/video_with_bgm.mp4`.
2. Delete or ignore `openmontage_production/`.
3. Disable OpenMontage routing for the content item.
4. Keep the original `case-study` production path unchanged.
