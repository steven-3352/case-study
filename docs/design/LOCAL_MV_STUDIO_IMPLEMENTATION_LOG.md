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
