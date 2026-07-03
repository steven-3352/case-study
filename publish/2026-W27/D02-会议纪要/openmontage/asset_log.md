# Asset Log · W27D02 OpenMontage Trial

> 状态：local montage surrogate  
> 外部 OpenMontage 仓库：本机未发现，未执行真实 OpenMontage pipeline。

## Source Assets

| Asset | Path | Source | Usage | License / Risk |
|-------|------|--------|-------|----------------|
| Meeting room | `assets/characters/w27d02/meeting_room.png` | GPT-image generated | 0-11s meeting / minutes scenes | AI generated, internal trial |
| Tired coworker | `assets/characters/w27d02/tired.png` | GPT-image generated | old workflow side | AI generated, internal trial |
| Relaxed worker | `assets/characters/w27d02/relaxed.png` | GPT-image generated | new workflow side | AI generated, internal trial; known nit: gender mismatch vs male narrator |
| Phone proof | `assets/characters/w27d02/me_phone.png` | GPT-image generated | CTA / self-proof | AI generated, internal trial |
| Worker avatar | `assets/characters/w27d02/test_worker.png` | GPT-image generated | todo owner visual | AI generated, internal trial |
| Worker avatar | `assets/characters/w27d02/female_worker.png` | GPT-image generated | todo owner visual | AI generated, internal trial |
| Original audio | `douyin/video_with_bgm.mp4` audio stream | Current project render | trial preview audio | Internal project output |

## Generated Assets

| Asset | Path | Method |
|-------|------|--------|
| Scene PNGs | `openmontage/scenes/*.png` | Playwright screenshot from local HTML |
| Preview video | `openmontage/preview.mp4` | ffmpeg image loops + original audio |
| Final candidate | `openmontage/final.mp4` | Copy of preview only after review decision |

## License Notes

- No external footage was downloaded in this trial.
- No third-party brand UI, logo, real person image, or customer data is intentionally included.
- This asset log is sufficient for internal route evaluation, not for claiming a full OpenMontage production run.
