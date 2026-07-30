# Local MV Studio M0-M1 Independent Correction Review

Verdict: **PASS**

Scope: correction review of immutable `input/repo` under `M1_T4_security_e2e`.
The reviewed architecture SHA-256 is
`fb8ff83f377e2eeb90b5fed0840107f96799a306b937ccd1b984f774d8272ab3`.
It matches both `INPUT_MANIFEST.json` and the SHA-256 computed for
`docs/design/LOCAL_MV_STUDIO_ARCHITECTURE.md`.

## Prior FAIL History and Reproduction

The prior review was **FAIL** for three claims. Each was reproduced against the
corrected immutable snapshot and is now corrected.

1. **G9 symlinked configured root:** the frozen fixture creates
   `pipeline -> outside` and calls `build_service(tmp_path)`. It now raises
   `ApplicationBlocked` before `data/app.sqlite3` exists. The protection is
   enforced while resolving configured roots in
   `mv_platform/application/service.py`: the resolved candidate must remain
   under the resolved workspace, and `initialize()` rejects a symlink or a
   resolved path that differs from the configured path before migration or
   directory creation. This is covered by
   `test_symlink_escape_fails_before_initialize_or_project_write`.

2. **G9 API/CLI secret disclosure:** with an application exception containing
   `/private/review/secret.txt M0_M1_REVIEW_SECRET_VALUE`, the API returns HTTP
   423 with the fixed detail `blocked`; the CLI returns 2 and writes the fixed
   text `input/application error` to stderr. Neither output contains the path
   or the inherited secret. This is covered by
   `test_api_and_cli_do_not_disclose_paths_or_inherited_secrets`.

3. **G1 runtime import:** the formerly failing
   `test_runtime_import_has_no_filesystem_side_effects` passes under the required
   command from `input/repo` with `PYTHONPATH=.`. The full frozen suite passes.

## Required Commands

```text
$ cd input/repo
$ PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/mv_platform -q
91 passed, 64 warnings in 3.24s

$ rg -n "mingyue_render|paperdoll_engine|render_frame|multiprocessing|ffmpeg" apps/mv_api apps/mv_cli apps/mv_codex
(no matches; exit status 1)
```

The 64 warnings are FastAPI `on_event` deprecation warnings and do not represent
test failures. No tests or production files were changed for this review.

## Worker Environment Allowlist

The worker boundary was explicitly verified by the frozen security fixture.
With `M0_M1_REVIEW_SECRET=must-not-reach-worker`, direct execution of `_worker`
observed no such variable. Before executor code is invoked, `_worker` rebuilds
`os.environ` from the fixed `_CHILD_ENV_ALLOWLIST` only:
`LANG`, `LC_ALL`, `LC_CTYPE`, `PATH`, `SYSTEMROOT`, `TZ`, and `WINDIR`.
`test_worker_environment_is_reduced_to_allowlist` passed, including the subset
assertion for the observed child environment.

## Gate Results

| Gate | Result | Corrected/current evidence |
| --- | --- | --- |
| G1 | PASS | Complete frozen suite: 91 passed; runtime-import regression passes. |
| G2 | PASS | Frozen interface and security coverage passes loopback health/ready and initialization behavior. |
| G3 | PASS | CLI/API canonical digest assertions pass in contract and security coverage. |
| G4 | PASS | Security fixture verifies two fake jobs, terminal lifecycle, ordered replay, and isolated events. |
| G5 | PASS | Security fixture verifies running cancellation reaps the worker and publishes no artifact. |
| G6 | PASS | Security fixture verifies duplicate idempotent submission creates no second staging side effect. |
| G7 | PASS | Security fixture verifies supervisor model and token counters are both zero. |
| G8 | PASS | Security fixture verifies concurrent job staging and event isolation. |
| G9 | PASS | Injection/traversal checks, corrected symlink pre-write rejection, redacted API/CLI errors, and worker allowlist fixture all pass. |
| G10 | PASS | Required interface-layer renderer/process/ffmpeg search has no matches. |

Final binary verdict: **PASS**
