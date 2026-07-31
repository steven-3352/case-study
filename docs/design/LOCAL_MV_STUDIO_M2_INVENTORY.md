# Local MV Studio M2 Legacy Inventory

Status: pre-implementation inventory
Date: 2026-07-31

## 1. Finding

M2 cannot treat the current `pipeline/mv_engine/` directory as a package that can be moved wholesale.
It contains reusable engine modules, Mingyue-specific command tools, compatibility imports, and code that
writes to repository-local output paths. The migration unit is one file or one dependency cluster.

The Mingyue example is obsolete and is not an M2 golden or product dependency. M2 uses a tracked,
deterministic synthetic fixture for package, session, concurrency, and source-write verification.

## 2. Classification

| Current files | Classification | M2 destination | Rule |
|---|---|---|---|
| `pipeline/mv_engine/{camera,compose,config,ease,fx,items,render,shot}.py` | reusable deterministic engine | `src/mvstudio/engines/mv/` | move implementation; no repository paths |
| `pipeline/mv_engine/atoms/` | reusable deterministic atoms and lock | `src/mvstudio/engines/mv/atoms/` | preserve `lock.json` byte contract |
| `pipeline/mv_engine/solver/` | reusable solver | `src/mvstudio/engines/mv/solver/` | preserve H1-H7 behavior |
| `pipeline/mv_engine/{assets,session,track,cache}.py` | reusable but state/path coupled | refactor into `src/mvstudio/engines/mv/` | explicit session; no module singleton |
| `pipeline/mv_engine/tools/frame_digest.py` | generic verification utility | `tests/support/frame_digest.py` | moved; writes only explicit destination |
| other `pipeline/mv_engine/tools/*.py` | obsolete Mingyue commands | `archive/legacy/mv_engine_tools/` | archived, never a product API |
| `pipeline/voice_room/mingyue*` | obsolete example | later archive/removal task | not imported, migrated, or used for tests |
| local `publish/语音厅/...` frames/assets | obsolete local output | outside M2 | never a product or CI dependency |

Compatibility shims may temporarily remain under `pipeline/mv_engine/`, but they may only import the new
package and emit no files. New application or interface code must not import `pipeline.*`.

## 3. State And Write Risks

1. `mv_engine.session._CURRENT` is a process-global mutable singleton.
2. `mingyue_render` configures the singleton during module import.
3. `mingyue_render` owns mutable `_LAYER`, `_YAML_SHOTS_CACHE`, `_WORKER`, and module-level `OUT`.
4. legacy tools mutate `mr.OUT`, `paperdoll_engine._PATHS`, and the session singleton.
5. `track.Session` accepts the entire `mingyue_render` module as its runtime contract.
6. several tools discover the repository root and hard-code `pipeline/voice_room` or `publish`.

M2 must isolate these globals behind a process-local legacy adapter and make all output/cache roots explicit.
Two jobs may share read-only fixture inputs, but may not share mutable session objects or output directories.

## 4. Synthetic Verification Fixture

M2 verifies the executor boundary without external media:

```text
tests/mvstudio/
  engine/test_session.py
  integration/test_legacy_adapter.py
```

The fixture produces only deterministic JSON in per-job staging. The migrated atom lock remains the
byte-level engine behavior check. No Mingyue equivalence claim remains in the M2 contract.

## 5. Source Protection Baseline

The protected set is every tracked file under `apps/`, `mv_platform/`, `pipeline/mv_engine/`,
`pipeline/voice_room/mingyue*`, `src/`, `tests/fixtures/`, and `docs/RULES/`. Acceptance computes hashes
before and after each adapter run. Runtime writes are allowed only under the supplied workspace:

```text
<workspace>/.mvstudio/jobs/<job_id>/
<workspace>/projects/<slug>/assets/generated/
<workspace>/projects/<slug>/outputs/
```

Any changed protected hash, new repository-local output, symlink escape, or cross-job reference is a hard fail.
