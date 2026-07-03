# OpenMontage Request · W27D02

```yaml
content_id: W27D02
source_project: case-study
platform: douyin
duration_s: 40
output_dir: publish/2026-W27/D02-会议纪要/openmontage
mode: trial_preview
external_openmontage_repo: not_available_locally
local_surrogate: true
```

## Goal

Create a 40s 9:16 hybrid meeting montage for:

> 散会了，同事还在写纪要，我直接走了。

The output must improve video feel and workplace immediacy without changing the approved script, facts, value anchor, or CTA.

## Locked Inputs

- `../meta.yaml`
- `../scripts/script_three_versions.md` vA
- `../retention_beat_sheet.md`
- `../design/form_strategy.md`
- `../design/design_language.md`
- `../design/storyboard.yaml`
- `../douyin/publish.md`

## Visual Commitments

1. 0-3s: meeting ends, coworkers still sorting notes, narrator leaves, group-message card appears.
2. 3-11s: minutes card already sent to group.
3. 11-22s: todo list with owner, deadline, @, reminder.
4. 22-30s: split-screen old workflow vs new workflow.
5. 30-40s: self-proof with phone + comment CTA.

## Restrictions

- Do not imitate Feishu, WeCom, DingTalk, or any real SaaS UI.
- Do not invent a new product claim.
- Do not change the CTA.
- Do not overwrite `../douyin/video_with_bgm.mp4`.

## Trial Output

Because external OpenMontage is not available on this machine, this request is executed as a local montage surrogate:

- `preview.mp4`: local preview for route evaluation.
- `final.mp4`: copy of preview only if review passes.
- `asset_log.md`: source and license notes.
- `decision_log.md`: generation decisions and limitations.
