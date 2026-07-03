# Decision Log · W27D02 OpenMontage Trial

## Decision

Run a local montage surrogate because the external OpenMontage repository is not available on this machine.

## Why This Still Counts As A Plugin Trial

- Uses the same file boundary proposed for OpenMontage: `publish/.../openmontage/`.
- Does not overwrite the original Douyin video.
- Consumes locked project inputs: script, retention, form strategy, design language, storyboard.
- Produces asset and decision logs for review.

## What This Trial Can Evaluate

- Whether the D02 concept benefits from a more montage-like meeting flow.
- Whether `openmontage_brief.md` is concrete enough to guide production.
- Whether the回流验收 template catches content, visual, and technical issues.

## What This Trial Cannot Evaluate

- Real OpenMontage agent planning quality.
- External B-roll retrieval and licensing.
- Remotion / HyperFrames implementation quality.
- Full video QA from OpenMontage itself.

## Route Choices

| Choice | Reason |
|--------|--------|
| Use GPT-image assets already generated for D02 | Avoid network/API dependency and keep trial reversible |
| Use original video audio | Preserve approved VO/BGM timing |
| Use browser-rendered scene PNGs | Current ffmpeg build lacks drawtext; browser handles Chinese text correctly |
| Keep preview static with simple scene cuts | Focus on route validation rather than final polish |

## Known Limitations

- Preview is closer to a montage storyboard than a polished OpenMontage final.
- No new real meeting B-roll is included.
- `relaxed.png` still has the known gender mismatch noted in `meta.yaml`.
- Full subtitles are not re-burned; large scene text carries the main visual message.

## QA Summary

```text
preview.mp4
duration: 40.000000
video: 1080x1920, 30fps
audio: AAC mono 44.1kHz
```

Frame review:

- 0-3s: meeting-room contrast and "minutes + todos sent" card are readable.
- 3-11s: minutes card is readable.
- 11-22s: todo owner / deadline / @ fields are readable.
- 22-30s: split contrast works, but gender mismatch remains.
- 30-40s: CTA card is readable.

Decision:

- Keep as route validation.
- Do not replace `douyin/video_with_bgm.mp4`.
