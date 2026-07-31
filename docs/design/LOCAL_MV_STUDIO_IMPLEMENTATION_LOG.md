# Local MV Studio · Implementation Log

## 2026-07-30 · Document Gate

- Architecture: `docs/design/LOCAL_MV_STUDIO_ARCHITECTURE.md`
- Architecture sha256: `fb8ff83f377e2eeb90b5fed0840107f96799a306b937ccd1b984f774d8272ab3`
- Independent reviewer: `gpt-5.6-terra`
- Verdict: `PASS` (G1-G10 all pass)
- Review: `docs/design/reviews/LOCAL_MV_STUDIO_DOCUMENT_REVIEW.md`
- Authorized implementation scope: M0-M1 only

## M0_T1_domain_contracts

- Worker: `gpt-5.6-luna`
- Packet cwd: repository-external temporary directory
- Result: completed and applied
- Worker test: 12 passed
- Independent edge tests initially found 3 failures:
  - boolean accepted as integer `seq` / `attempt`
  - invalid sequence leaked `TypeError`
  - Event accepted non-mapping payload
- Worker correction: completed
- Final repository test: `15 passed in 0.02s`
- Applied roots: `mv_platform/domain/`, `tests/mv_platform/unit/`
- Forbidden dependency scan: pass
- Existing render engine / assets modified: no

## M0_T2_config_and_sqlite

- Worker: `gpt-5.6-luna`
- Packet used `--ignore-user-config --ignore-rules`
- Result: not started
- Reason: two consecutive model invocations exhausted WebSocket retries; HTTPS fallback returned no response
- Candidate files produced: none
- Repository files modified by this task: none
- Resume point: reuse the frozen M0_T2 task packet contract, then independently audit SQLite transaction and path-boundary behavior before applying

## Cost Observation

- Repository-root workers inherited the full project rules and produced excessive context.
- The first compact packet still reported 111,616 input tokens (88,576 cached); its correction turn reported 101,317 input tokens (78,592 cached).
- `--ignore-user-config --ignore-rules` removed MCP/plugin noise, but the model transport timed out before token usage could be measured.
- Future worker launcher must make ignore flags the default and expose per-task input, cached-input and output token counters in the artifact manifest.

## M0_T2_config_and_sqlite · resumed

- Worker: `gpt-5.6-luna`
- Result: completed, independently reviewed, and applied
- Delivered: local-only settings, SQLite migration/repositories, atomic artifact store, traversal and symlink boundaries
- Final evidence: included in the M0-M1 suite (`91 passed`)
- Existing render engine / assets modified: no

## M1_T1_supervisor

- Worker: `gpt-5.6-luna`
- Result: completed, independently reviewed, and applied
- Delivered: spawn-only fake executor, deterministic parent-owned progress events, cancellation/recovery, staging isolation, forced child cleanup
- Supervisor model calls/tokens: `0 / 0`
- Final security evidence: concurrent isolation, cancellation, recovery, malformed-message and persistence-failure tests pass

## M1_T2_application_service

- Worker: `gpt-5.6-luna`
- Result: completed, independently reviewed, and applied
- Delivered: canonical project creation, atomic brief, deterministic/idempotent job submission, inspect/events/artifacts, queued cancellation
- Pre-interface repository result: `64 passed`

## M1_T3_api_cli

- Worker: `gpt-5.6-luna`
- Result: completed after independent contract corrections
- Delivered: shared runtime bootstrap, FastAPI REST/SSE, direct CLI, Codex-to-CLI delegation
- Independent contract findings corrected before apply:
  - absolute path / exception detail disclosure
  - CLI `--follow` exiting after one backlog read
  - `auto_start` executor fields dropped by the API adapter
- Contract result: `15 passed`
- Protected `mv_platform` packet copy matched the repository before apply
- Forbidden interface dependency scan: no matches

## M1_T4_security_e2e

- Independent reviewer: `gpt-5.6-terra`
- First verdict: `FAIL`
- Valid findings corrected:
  - configured-root parent symlinks were resolved before safety checks
  - known application errors could still disclose environment secrets
  - worker processes had no explicit environment allowlist
- Packet-layout-only finding: the first review snapshot merged tests into `input/mv_platform`, breaking one relative import test; the repository itself passed that test
- Correction review: `PASS` (G1-G10 all pass)
- Final evidence: `91 passed, 64 warnings`; security subset `12 passed`; forbidden interface scan has no matches
- Review: `docs/design/reviews/LOCAL_MV_STUDIO_M0_M1_REVIEW.md`

## Updated Cost Observation

- M1_T3 Luna implementation: 365,101 input tokens (319,488 cached); correction: 193,720 input (156,928 cached).
- M1_T4 Terra first review: 569,412 input (506,368 cached); correction review: 329,169 input (285,952 cached).
- Repository-external cwd alone did not make workers cheap. The reliable launcher combination is `--ignore-rules` plus explicit `mcp_servers={}` / `plugins={}` and a minimal packet.
- Do not use `--ignore-user-config` with the current custom provider: it removes provider configuration and caused transport failure.
- `--ephemeral` sessions cannot be resumed. For tiny deterministic corrections, opening a fresh 100k+ worker turn costs more than applying the frozen-test-derived patch directly.

## 2026-07-31 · Directory And Product Boundary Correction

- Contract: `docs/design/LOCAL_MV_STUDIO_DIRECTORY_CONTRACT.md`
- Scope: M2 entry correction; M2 implementation has not started
- Corrected runtime defaults:
  - project roots use `<workspace>/projects/<slug>` instead of `pipeline/voice_room/<slug>`
  - application state uses `<workspace>/.mvstudio/` instead of repository-local `data/`
  - no-argument CLI/API startup selects an OS user-data directory; `MV_WORKSPACE_ROOT` remains the explicit override
- Source protection: Application Service rejects a workspace equal to or nested under the source repository.
- New project layout separates inputs, creative contracts, source/generated assets, outputs, and project-local `.mvstudio` work/log directories.
- Migration decision: classify `pipeline/` per file; do not relocate the mixed directory wholesale into the installable package.
- Verification: `93 passed, 65 warnings`; warnings are existing FastAPI/Starlette deprecations.
- Carry forward to M2: tests and cheap workers may write only to isolated workspace/job staging; protected source files must remain unchanged before and after execution.


## 2026-07-31 · M2 Engine Package And Isolation Adapter

- User scope decision: the Mingyue example is obsolete; M2 uses a deterministic synthetic fixture and no Mingyue visual-equivalence claim.
- Independent review: waived by the user for this iteration.
- Reusable engine implementation moved from `pipeline/mv_engine/` to `src/mvstudio/engines/mv/`; the old path contains only a compatibility namespace.
- Mingyue-specific engine tools moved to `archive/legacy/mv_engine_tools/`; generic frame digest moved to `tests/support/`.
- Added installable package metadata, explicit per-job Session use, and a bounded `legacy` supervisor executor.
- Synthetic concurrent jobs write only to their own `.mvstudio/jobs/<job_id>` staging directories.
- Verification: `95 passed, 65 warnings`; atom lock `15 cases/10 registered atoms` byte-identical; product imports from `pipeline`: zero.

## 2026-07-31 · M3 Director Compiler Foundation

- Manifest: `docs/design/LOCAL_MV_STUDIO_M3_MANIFEST.yaml`; milestone remains `in_progress`.
- Added a fail-closed director package contract for brief, music map, character map, visual score, asset paths, timeline continuity, energy arc, relationship shots, transitions, techniques, and animatic settings.
- Added deterministic compilation to story framework, asset plan, editorial/generation plan, human storyboard, and engine-neutral shots.
- Editorial shots remain separate from provider generation clips; i2v/hybrid clips are at least 4000 ms with explicit usable ranges and handles.
- Added a silent 540p structural Animatic renderer and ffprobe QC. Outputs are 540x960 for 9:16 or 960x540 for 16:9 and are explicitly marked not for external release.
- Added per-artifact schema/version, input hashes, content hash, producer, job/project identity, and draft status in `artifact-manifest.json`.
- Added a bounded spawn-based `director` Supervisor executor. It writes only to current job staging and keeps model/token counters at zero.
- Verification: `102 passed, 65 warnings`; M3 focused suite `7 passed`; atom lock `15 cases/10 registered atoms` byte-identical; product imports from `pipeline`: zero; `git diff --check` clean.
- Carry forward: next M3 slice must add raw audio/lyrics/portrait intake, deterministic media probing and lyric parsing, semantic map drafting through a bounded model port, approval transitions, and atomic publication into `projects/<slug>/creative|outputs`. Do not label M3 complete before those paths are tested end to end.

## 2026-07-31 · M3 Raw Intake And Controlled Publication

- Added project-scoped three-input intake for one audio file, one lyrics file, and one or more character images.
- Application Service validates every project input path, rejects traversal, backslashes, symlinks, missing files, and cross-directory type mismatches, then copies bytes into the current Job staging before execution.
- Added deterministic ffprobe audio metadata, UTF-8 timed LRC parsing, explicit `alignment_required` for plain lyrics, and Pillow image metadata/hash inspection without rewriting source portrait pixels.
- Added the bounded `director_intake` Supervisor executor; it reads only the Job-local input copy and writes `intake/intake_manifest.json` plus timed lyric data when present.
- Corrected Director compiler manifests to use the real supervised Job ID instead of a placeholder identity.
- Added explicit Application Service approval and controlled publication. Publication rechecks project/Job identity, manifest status, content hashes, declared paths, symlinks, and destination conflicts before writing `creative/` and `outputs/`.
- Existing differing project artifacts are never overwritten. Same-hash publication is idempotent; conflicting content fails closed.
- Publication control records live under project `.mvstudio/jobs/<job_id>/`, not in source or `pipeline/`.
- Verification: `112 passed, 65 warnings`; M3 focused suite `11 passed`; atom lock `15 cases/10 registered atoms` byte-identical; product imports from `pipeline`: zero.
- M3 remains `in_progress`. Carry forward: implement bounded beat/lyric alignment and semantic map drafting ports, then expose the complete ordinary-user workflow through CLI/API without source-code edits.

## 2026-07-31 · M3 Deterministic Audio Analysis And Bounded Map Drafting

- Added deterministic ffmpeg PCM decoding plus 50 ms RMS, onset, energy, and BPM candidate analysis. Analysis is restricted to the Job-local audio copy and rechecks the intake sha256 before any model cost.
- Added bounded semantic task contracts for the architecture allowlist events `lyrics.semantic_segment.requested` and `relationship_map.draft_requested`.
- Every semantic call freezes the configured model, byte/token budgets, reason, input contract hash, output schema hash, response hash, and reported token usage.
- The model only groups immutable timed lyric line IDs and drafts character functions/relationships. Python retains ownership of timestamps, section boundaries, audio-derived energy, cues, source assets, and file writes.
- Portrait paths, portrait hashes, and portrait pixels are excluded from semantic model payloads.
- Semantic grouping must cover every timed lyric line exactly once in original order. Multi-character drafts require a valid relationship; unknown characters, groups, fields, reordered lines, budget overruns, hash drift, and symlinks fail closed.
- Added draft outputs under Job staging: `creative/beats.json`, `lyrics_semantic.json`, `music_map.yaml`, `character_map.yaml`, and `model_audit.json`.
- Added a real compiler approval gate: `music_map`, `character_map`, and `visual_score` must each carry `status: approved`; `draft_self_generated` can no longer authorize compilation.
- Verification: `122 passed, 65 warnings`; M3 focused suite `27 passed`.
- M3 remains `in_progress`. Carry forward: implement a concrete low-cost model adapter, plain-lyric alignment provider, story/visual-score drafting and Application Service/CLI/API orchestration.

## 2026-07-31 · M3 Ordinary-User Director Actions

- Added fixed API actions: `POST /api/v1/jobs/{job_id}/director/intake`, `director/approve`, and `director/publish`.
- Added matching CLI actions: `mvstudio job director-intake|director-approve|director-publish <job_id>`.
- These actions accept only a Job ID and delegate to Application Service. They do not expose staging paths, output destinations, cwd, shell, executor names, or executor payloads.
- API and CLI return the same structured Application Service results and retain existing redacted error behavior.
- Verification: `124 passed, 69 warnings`; interface contract suite `17 passed`. Warning increase is from exercising the existing FastAPI startup/shutdown deprecation path in two additional contract tests.
- M3 remains `in_progress`. Carry forward: add the concrete semantic provider and map workflow action, plain-lyric alignment, then story framework/visual-score drafting through approval to Animatic.

## 2026-07-31 · M3 OpenAI-Compatible Semantic Provider

- Added a concrete OpenAI-compatible adapter for the bounded semantic model port using the existing `LLM_BASE_URL`, `LLM_API_KEY`, and task-selected model contract.
- The adapter uses a fixed `/chat/completions` endpoint, JSON-only response mode, fixed system instruction, temperature zero, timeout, response byte limit, and the task token budget.
- External HTTP is HTTPS-only except loopback HTTP. URL credentials, query strings, fragments, non-HTTP schemes, malformed envelopes, non-JSON model content, oversized responses, and transport failures fail closed.
- Provider errors are redacted; API keys and upstream error details are never included in application exceptions or audit output.
- Provider usage is returned as `ModelResult` and remains subject to the caller's total token hard limit.
- Verification: `132 passed, 69 warnings`; provider plus bounded-drafting focused suite `15 passed`.
- M3 remains `in_progress`. Carry forward: wire map drafting into a dedicated Job/Application action, then add story/visual-score drafting and the one-command LRC-to-Animatic test workflow.

## 2026-07-31 · M3 One-Command Structural Animatic Test

- Added deterministic structural visual-score planning from music map, character map, lyric semantics, and project brief.
- Python owns section boundaries, energy, cues, source assets, cast assignment, shot IDs, and timeline continuity. The planner emits one structural shot per section and blocks flat energy, gaps, missing relationships, unknown lyrics, and invalid cues.
- Multi-character plans always include a relationship/peak group shot. Every shot has a unique structural purpose, one primary action, first/last frame contracts, a shared transition element, and source-portrait references.
- Added the fixed ordinary-user action director-animatic-test to CLI and API. It accepts only a queued operation=animatic Job ID and no paths, executor settings, staging directory, or output destination.
- The application copies project inputs into Job staging, validates timed LRC intake, runs two bounded/audited semantic calls in the application process, and submits only the draft package to a credential-free spawn worker.
- The worker compiles the package only in explicit structural-test mode and renders a silent 540p Animatic. Maps, visual score, compiled artifacts, and manifest remain draft_self_generated with approval_required=true.
- The action waits for the worker and publishes only the clearly named preview to projects/<slug>/outputs/structural_animatic_<job-id>.mp4. Source portraits remain byte-identical; runtime inputs, logs, maps, and manifests remain under <workspace>/.mvstudio/jobs/<job-id>.
- Offline end-to-end evidence: real WAV/LRC/PNG parsing, fake bounded semantic port, spawn worker, ffmpeg render, ffprobe 540x960 validation, manifest checks, project output publication, and source-image hash preservation all pass.
- Full verification: 137 passed, 69 warnings; focused workflow/interface suite 47 passed; atom lock 15 cases/10 registered atoms byte-identical; product imports from pipeline: zero; git diff --check clean.
- Real-provider smoke is blocked by external configuration, not hidden as passed: configured LLM_API_KEY is a 3-character placeholder and returned HTTP 401; one valid key from the same configured gateway authenticated but claude-opus-4-8 returned HTTP 503 on two attempts. No endpoint or credential value was logged.
- M3 remains in_progress. Carry forward: install a valid semantic credential/model route, rerun the same real smoke, then implement plain-text lyric alignment and creative (not merely structural) visual-score drafting.

## 2026-07-31 · M3 Explicit Offline Structural Test

- Added `director-animatic-offline-test` to the Application Service, CLI, and API so ordinary users can exercise the complete LRC-to-540p path without editing source code or configuring a network model.
- The offline port is deliberately non-semantic: every timed lyric remains an independent `unclassified_lyric`, emotion is `unclassified`, character functions follow declared brief order, and multi-character relationships are explicitly marked as structural placeholders with no semantic claim.
- Offline execution is an explicit action, never a silent fallback from the configured-model action. Its fixed audit model is `offline-structural-v1`, both bounded calls report zero input/output tokens, and all generated artifacts remain `draft_self_generated` with approval required.
- The output boundary is unchanged: runtime data stays under `<workspace>/.mvstudio/jobs/<job-id>` and the preview is published only to `projects/<slug>/outputs/structural_animatic_<job-id>.mp4`; no code, logs, temporary files, or outputs are written under `pipeline/`.
- Independent-process smoke evidence uses a new temporary workspace with generated WAV/LRC/PNG inputs, crosses the spawn worker and ffmpeg boundary, and produces a 3-second 540x960 MP4. It does not use the retired example material.
- Full verification: 141 passed, 69 warnings; atom lock 15 cases/10 registered atoms byte-identical; product imports from pipeline: zero; git diff --check clean.
- M3 remains `in_progress`. Carry forward: add plain-text lyric alignment, then creative visual-score drafting and a valid configured semantic provider route; offline placeholders must never satisfy those semantic acceptance requirements.
