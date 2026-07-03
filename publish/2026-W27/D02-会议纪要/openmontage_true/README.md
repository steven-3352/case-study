# W27D02 OpenMontage True Hybrid Trial

## Output

- `final.mp4` — OpenMontage hybrid rough cut, 1080x1920, 35.16s.
- `contact_sheet.png` — QA frame sheet sampled from the final render.
- `generation_results.json` — provider outputs, request ids, costs, and artifact paths.
- `render_report.json` — render metadata copied from the OpenMontage project.
- `build_hybrid_trial.py` — reproducible local composition script.

## OpenMontage Project

```text
/Users/bubu/Documents/projects/OpenMontage/projects/w27d02-meeting-minutes/
```

## Pipeline Decision

- Pipeline: `hybrid`
- Anchor medium: Grok generated workplace video clips
- Support layers: GPT Image 2 UI support cards, Chinese overlay cards, MiniMax narration
- Runtime used: FFmpeg composition over OpenMontage-generated assets
- Reason: HyperFrames was unavailable in preflight; Remotion was available, but this rough-cut needed fast validation of the asset-generation layer more than React component complexity.

## Generated Assets

| Asset | Provider | Purpose |
|---|---|---|
| `01_hook_meeting_exit.mp4` | Grok `grok-imagine-video` | Meeting-room hook with direct-leave contrast |
| `04_contrast_old_new.mp4` | Grok `grok-imagine-video` | Old workflow vs new workflow contrast |
| `02_minutes_card_support.png` | GPT Image 2 | Meeting-summary UI support visual |
| `03_todo_tracking_support.png` | GPT Image 2 | Task ownership/deadline UI support visual |
| `voiceover.mp3` | MiniMax TTS | Full narration |

## Trial Result

This is a real OpenMontage-style trial, not a reuse of existing P004 images. It validates that the external layer can produce new video/image/audio assets and return a finished vertical cut to `case-study`.

Current rough-cut gaps:

- No full word-by-word subtitle burn yet.
- No BGM or audio ducking yet.
- Grok people/office continuity is acceptable for a trial but not production-final.
- Composition is FFmpeg-based; a later pass should use Remotion or HyperFrames once the chosen runtime is locked.
