# Decision Log

- Runtime considered: Remotion, HyperFrames, FFmpeg.
- Selected: FFmpeg frame compositor for this production pass.
- Reason: HyperFrames unavailable; deterministic subtitle/UI frame rendering was fastest to validate production gates.
- Asset policy: reused OpenMontage-generated trial assets because they already satisfy "new generated assets" and are traceable; did not reuse P004 illustrations as primary visuals.
- Audio: local Pixelland BGM plus generated short SFX; no paid music generation.
