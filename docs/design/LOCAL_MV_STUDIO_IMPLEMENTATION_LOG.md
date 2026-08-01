# Local MV Studio · Implementation Log

## 2026-08-01 · Web MVP User Test Surface

- Added a same-origin FastAPI Web workspace at `/` with responsive desktop/mobile layouts.
- Ordinary-user flow now covers project creation and selection, job creation, automatic test execution, status polling, event history, artifacts, cancellation, and fixed director actions.
- Added safe read-only project and project-job list contracts; project roots and absolute paths are not exposed.
- Web polling advances the zero-token Supervisor before returning status, fixing jobs that otherwise remained visually `running` unless an SSE consumer was connected.
- Fixed async form lifecycle handling so successful project/job creation updates the current page without a manual reload.
- Verification: final contract suite `22 passed`; full final suite `201 passed`; JavaScript syntax and `git diff --check` pass.
- Browser evidence: Chrome desktop 1440x1000 and mobile 390x844; create project -> create auto-start job -> `succeeded`; zero console errors and no mobile horizontal overflow.
- Test service: `http://127.0.0.1:8790`, isolated workspace `/tmp/local-mv-studio-web-8790`.

### Project deletion follow-up

- Added permanent project deletion through a fixed `DELETE /api/v1/projects/{project_id}` contract.
- Deletion requires an exact slug confirmation and refuses projects with running Jobs.
- Successful deletion removes the project directory, Job staging directories, and associated artifacts, events, statuses, Jobs, and project database rows.
- Web confirmation uses an explicit danger dialog; after deletion it selects the next project or returns to the empty state.
- Browser evidence: create project -> type slug -> permanent delete -> empty project list; zero console errors.
- Latest test service: `http://127.0.0.1:8791`, isolated workspace `/tmp/local-mv-studio-web-8791`.

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

## 2026-07-31 · M3 Evidence-Backed Plain-Lyric Alignment

- Intake now preserves non-empty plain lyrics as `intake/lyrics_plain.json` with original line numbers and source digest. Empty lyrics and mixed timed/plain files fail closed instead of silently dropping content.
- Added a bounded alignment contract that rechecks the staged audio hash, preserves every source line exactly, requires strictly advancing starts within the probed duration, validates confidence, and writes timed lyrics plus separate audit and provider-evidence artifacts.
- Added a local Faster Whisper adapter with word timestamps. The model is explicitly selected through `MVSTUDIO_WHISPER_MODEL`, loaded with `local_files_only=true`, and never downloaded or replaced by an online/equal-spacing fallback.
- Normalized transcription must exactly cover the supplied lyrics, and each lyric line must begin at a distinct provider word boundary. Transcript drift, missing speech, missing models, symlink replacement, changed audio, or incomplete evidence blocks before map drafting.
- Existing configured-semantic and offline-unclassified Animatic actions now accept either timed LRC or verified provider-aligned plain lyrics and return `lyrics_alignment_mode`. Runtime and evidence files stay under `<workspace>/.mvstudio/jobs/<job-id>`; only the non-approved preview enters the user project's outputs directory.
- Local cached-model smoke loaded Faster Whisper Small and correctly rejected a synthetic tone-only WAV with no word timestamp evidence. No retired example material was used.
- Full verification: 155 passed, 69 warnings; focused alignment/Animatic suite 25 passed; atom lock 15 cases/10 registered atoms byte-identical; product imports from pipeline: zero; git diff --check clean.
- M3 remains `in_progress`. Carry forward: creative visual-score drafting and a valid configured semantic provider route; offline semantic placeholders and failed lyric alignment cannot satisfy creative acceptance.

## 2026-07-31 · M3 Creative Visual Score And Completion

- Upgraded `director-animatic-test` from a structural preview to the configured-model creative path. It now makes a third bounded, schema-hashed, token/byte-limited call for shot-level creative decisions and publishes only `outputs/creative_animatic_<job-id>.mp4`.
- Python retains structural authority: model output cannot change shot IDs/order, timeline, sections, energy, cast, lyrics, beats, or source assets. Only allowlisted leverage, composition, primary action, first/last frame, transition, technique, and missing-asset descriptions are merged.
- Every creative shot must be present once in structural order, have distinct purpose/action, use bounded text, use allowlisted enums, and end with transition `none`. Any violation fails before writing the creative score or submitting the worker.
- The offline command remains a separate two-call, zero-token, unclassified structural path and continues to publish only `outputs/structural_animatic_<job-id>.mp4`; there is no provider fallback between the actions.
- Both paths retain `draft_self_generated` and `approval_required=true`, cross the credential-free spawn worker, compile story/asset/generation/storyboard/shot artifacts, render 540p, preserve source portraits, and use the existing explicit approval/publication gates.
- Real configured-provider execution remains deployment-blocked by the local placeholder credential and upstream 503 evidence already recorded above. This is now an explicit operational prerequisite, not missing repository implementation.
- Final verification: 160 passed, 69 warnings; creative planner/Animatic focused suite 20 passed; atom lock 15 cases/10 registered atoms byte-identical; product imports from pipeline: zero; git diff --check clean.
- M3 status is `complete`. M4 may begin only with approved M3 artifacts and covers keyframe selection, media-provider generation, per-shot diagnosis, final compositing, and QC.

## 2026-07-31 · M3 Real Configured-Model Smoke

- Re-ran the configured-model creative action in a new temporary workspace with generated WAV/LRC/PNG inputs after valid `LLM_BASE_URL`, `LLM_API_KEY`, and `LLM_MODEL` configuration became available. No retired example material was used.
- The first real calls exposed two contract gaps that fixture providers had hidden: model tasks sent only an output-schema hash instead of the schema body, and the creative schema did not enumerate transition values or permit an empty shared element for a final `none` transition.
- `ModelTask` now carries the output schema body. The schema is included in the provider request, byte budget, and input-contract hash while the separate output-schema hash remains in the audit contract.
- The creative transition schema now enumerates every allowlisted transition. Python normalizes an empty final `none` shared element to `final held composition`; every non-`none` transition still requires a non-empty shared element.
- The real action completed with `semantic_mode=configured_model`, `visual_score_mode=creative_model_draft`, `status=draft_self_generated`, and three audited model calls. Reported token pairs were 345/191, 425/320, and 1363/757.
- The credential-free worker rendered a 3-second 540x960 creative Animatic. Both staged portrait copies remained byte-identical to their project inputs, and `creative/model_audit.json` contained no credential value.
- Smoke workspace evidence: `/tmp/mvstudio-real-smoke-4clxaype`; published preview: `projects/real-provider-smoke/outputs/creative_animatic_job-df3e27f228a93989a4e5ee93b3d04084.mp4` within that workspace.
- M3 has no remaining configured-model credential blocker. Deployment still requires the documented environment variables, and the explicit offline structural action remains the credential-free test path.
- CLI and API owned-service startup now load the repository-root `.env` without overriding explicitly exported environment variables, so ordinary users do not need to source credentials manually or edit code.

## 2026-08-01 · Web Director Workflow Streaming, Recovery, And Pagination

- OpenAI-compatible LLM requests used by the Web workflow now require SSE streaming with `stream=true` and `stream_options.include_usage=true`; a non-streaming upstream response fails closed. Final usage comes from the upstream stream and records input, cache-read, and output tokens separately.
- Visual-storyboard drafting runs as one streamed request per shot. The Qingyi2 browser workflow produced all 25 shots from the imported director spreadsheet contract, including its sixth row, without replacing the user-visible Chinese editable prompts.
- Publication recovery is idempotent and auditable. A retry may replace only a file whose prior ownership and bytes are proven by the old `publication.json`, artifact manifest, and SHA-256; unknown or user-authored files still produce a conflict. A completed but unpublished Job can finish publication without repeating model calls or charges.
- Material-reference comparison is order-independent, and a current successful run no longer exposes an obsolete failed-run recovery panel.
- The Web project view now paginates runtime records and cost details independently at 10 rows per page. Each table has its own previous/next controls and page indicator, and both reset to page 1 when the selected project changes.
- Cost rows show the real `input_tokens`, `cache_read_tokens`, and `output_tokens` fields instead of an undefined aggregate. Existing image, video-duration, retry, failure, translation, and per-shot cost records remain visible through the same project ledger.
- Real Chromium verification passed on `project-3531246c03670d497567f9eae3ddf2e6`: runtime records reached page 2/2, cost details reached page 2/15, each page contained at most 10 rows, adjacent pages had different first records, no `undefined` text appeared, and the browser console reported no errors.
- Recovery evidence: `job-b27e500f87d75a72d64e6a7b5f6b8251` finished with `runtime_state=succeeded` and `business_stage=exported`; its cost remained `CNY 0.03467560`, proving publication recovery did not bill model work twice.
- Final verification: `232 passed, 96 warnings`; `node --check apps/mv_api/static/app.js`; `git diff --check`; real Chromium workflow and pagination checks passed. The warnings are the existing FastAPI `on_event` deprecation warnings.

## 2026-08-01 · GPT-image-2 Shot Background And Complete First-Frame Generation

- Added a visible `用 GPT-image-2 生成背景` action to every storyboard shot and a separate complete character-and-background first-frame action to the keyframe workbench. Each action states `¥0.50 / 张` before invocation.
- Background direction now consumes the bound lyric and time range, character director function and traits, source-art style anchors, music emotion and energy, story function, composition, first/last-frame contract, adjacent-shot continuity, project canvas, lighting and palette constraints. Character images are style references only for a background plate; the prompt explicitly forbids drawing people into the background.
- Complete first-frame generation requires an approved storyboard and an approved or user-supplied background. Reference order is explicit: background first, then the shot's character source images for identity, face, hair, costume, accessories, proportion and original-art-style preservation.
- Both Chinese system and task prompts are user-visible and editable. Runtime prompt conversion uses the existing streamed semantic provider, records its input/cache/output token cost, and stores the source prompt hash in `creative/image-generation-audit.json`.
- Successful GPT-image-2 outputs are decoded, verified, normalized to PNG, stored under project-owned `assets/generated/backgrounds/` or `assets/generated/keyframes/`, and billed at `¥0.50` with shot ID, model, request ID and output path. Failed attempts are recorded with zero image quantity; invalid returned image content is treated as a billable provider output and is not exposed as a valid candidate.
- Focused verification only, per user instruction to defer broad acceptance: director-context/reference/cost unit path passed; relevant HTTP contract tests passed; JavaScript syntax and `git diff --check` passed. Full browser and full-suite acceptance intentionally deferred until the remaining workflow changes are complete.
