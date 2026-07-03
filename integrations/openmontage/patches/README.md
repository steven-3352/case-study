# OpenMontage Local Patch Manifest

This repository does not vendor OpenMontage source. The sibling checkout at
`/Users/bubu/Documents/projects/OpenMontage` currently carries local changes
needed by the case-study integration.

## Required OpenMontage Changes

Files changed in the sibling OpenMontage checkout:

- `.env.example`
- `tools/graphics/openai_image.py`
- `tools/graphics/image_gen.py`
- `tools/graphics/grok_image.py`
- `tools/video/grok_video.py`
- `tools/audio/minimax_tts.py`

## Purpose

The changes add:

- OpenAI-compatible relay support for GPT Image 2:
  - `OPENAI_BASE_URL`
  - `OPENAI_IMAGE_BASE_URL`
  - `OPENAI_IMAGE_MODEL`
- Grok/xAI-compatible relay support for image/video:
  - `GROK_BASE_URL`
  - `XAI_BASE_URL`
  - `GROK_VIDEO_MODEL`
  - `GROK_VIDEO_CREATE_PATH`
  - `GROK_VIDEO_STATUS_PATH_TEMPLATE`
- MiniMax TTS as an OpenMontage `tts` provider:
  - `MINIMAX_API_KEY`
  - `MINIMAX_BASE_URL`
  - `MINIMAX_GROUP_ID`
  - `MINIMAX_TTS_MODEL`
  - `MINIMAX_TTS_VOICE_ID`

## Current Validation

Validated locally:

- GPT Image 2 image generation succeeds through relay.
- Grok `grok-imagine-video` generation and `vidgen.x.ai` download succeed with network proxy enabled.
- MiniMax TTS async generation succeeds and is selected by `tts_selector`.

## Upstreaming Recommendation

For long-term stability, push these changes to either:

1. a fork of `calesthio/OpenMontage`, then pin case-study to that fork/commit; or
2. upstream OpenMontage via pull request.

Until then, keep this manifest plus `openmontage.env.example` as the integration
contract in the case-study GitHub repository.
