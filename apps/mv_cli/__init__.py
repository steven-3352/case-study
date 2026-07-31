import argparse
import json
import sys
import time
from pathlib import Path

from mv_platform.application.service import ApplicationError, ApplicationNotFound
from apps.runtime import build_service, load_runtime_environment


def _parser():
    parser = argparse.ArgumentParser(prog="mvstudio")
    parser.add_argument(
        "--workspace",
        help="user-owned MV Studio workspace; defaults to the operating-system application data directory",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    doctor = sub.add_parser("doctor"); doctor.add_argument("--json", action="store_true")
    project = sub.add_parser("project").add_subparsers(dest="project_command", required=True)
    create = project.add_parser("create"); create.add_argument("--brief", required=True); create.add_argument("--slug", required=True); create.add_argument("--project-id"); create.add_argument("--json", action="store_true")
    job = sub.add_parser("job").add_subparsers(dest="job_command", required=True)
    submit = job.add_parser("submit"); submit.add_argument("--project", required=True); submit.add_argument("--operation", required=True); submit.add_argument("--input-digest", required=True); submit.add_argument("--input-ref", action="append", default=[]); submit.add_argument("--output", action="append", default=[]); submit.add_argument("--idempotency-key"); submit.add_argument("--start", action="store_true"); submit.add_argument("--json", action="store_true")
    inspect = job.add_parser("inspect"); inspect.add_argument("id"); inspect.add_argument("--json", action="store_true")
    ev = job.add_parser("events"); ev.add_argument("id"); ev.add_argument("--after", type=int, default=0); ev.add_argument("--follow", action="store_true")
    cancel = job.add_parser("cancel"); cancel.add_argument("id"); cancel.add_argument("--grace", type=float, default=1.0); cancel.add_argument("--json", action="store_true")
    director_intake = job.add_parser("director-intake"); director_intake.add_argument("id"); director_intake.add_argument("--json", action="store_true")
    director_animatic = job.add_parser("director-animatic-test"); director_animatic.add_argument("id"); director_animatic.add_argument("--json", action="store_true")
    director_animatic_offline = job.add_parser("director-animatic-offline-test"); director_animatic_offline.add_argument("id"); director_animatic_offline.add_argument("--json", action="store_true")
    director_approve = job.add_parser("director-approve"); director_approve.add_argument("id"); director_approve.add_argument("--json", action="store_true")
    director_publish = job.add_parser("director-publish"); director_publish.add_argument("id"); director_publish.add_argument("--json", action="store_true")
    return parser


def main(argv=None, service=None):
    args = _parser().parse_args(argv)
    owned = service is None
    if owned:
        load_runtime_environment()
    service = service or build_service(Path(args.workspace) if args.workspace else None)
    try:
        if args.command == "doctor":
            result = {"status": "ready"}
        elif args.command == "project":
            brief = json.loads(Path(args.brief).read_text(encoding="utf-8"))
            result = service.create_project(args.slug, brief, args.project_id)
        elif args.job_command == "submit":
            result = service.submit_job(args.project, args.operation, args.input_digest, args.input_ref, args.output, args.idempotency_key, auto_start=args.start)
        elif args.job_command == "inspect":
            result = service.inspect_job(args.id)
        elif args.job_command == "events":
            cursor = args.after
            terminal_seen = False
            while True:
                if getattr(service, "supervisor", None) is not None:
                    service.supervisor.tick()
                events = service.list_events(args.id, cursor)
                for event in events:
                    print(json.dumps({"id": event.seq, "event": event.event_type, "data": event.payload}, sort_keys=True, default=str, separators=(",", ":")))
                    cursor = event.seq
                if not args.follow:
                    return 0
                inspection = service.inspect_job(args.id)
                is_terminal = inspection.status.runtime_state.value in {
                    "succeeded", "failed", "blocked", "cancelled"
                }
                if is_terminal:
                    if events:
                        return 0
                    if terminal_seen:
                        return 0
                    terminal_seen = True
                else:
                    terminal_seen = False
                time.sleep(0 if terminal_seen else 0.25)
        elif args.job_command == "director-intake":
            result = service.start_director_intake(args.id)
        elif args.job_command == "director-animatic-test":
            result = service.start_director_animatic_test(args.id)
        elif args.job_command == "director-animatic-offline-test":
            result = service.start_director_animatic_offline_test(args.id)
        elif args.job_command == "director-approve":
            result = service.approve_director_artifacts(args.id)
        elif args.job_command == "director-publish":
            result = service.publish_director_artifacts(args.id)
        else:
            result = service.cancel_job(args.id, args.grace)
        print(json.dumps(result if isinstance(result, dict) else _json(result), sort_keys=True, separators=(",", ":")))
        return 0
    except ApplicationNotFound as exc:
        print("not found", file=sys.stderr); return 3
    except (ApplicationError, OSError, ValueError, json.JSONDecodeError) as exc:
        print("input/application error", file=sys.stderr); return 2
    finally:
        if owned and getattr(service, "supervisor", None) is not None:
            service.shutdown()


def _json(value):
    from apps.mv_api import _jsonable
    if hasattr(value, "job_spec") and hasattr(value, "status"):
        result = {"job_spec": _jsonable(value.job_spec), "status": _jsonable(value.status),
                  "canonical_job_digest": value.canonical_job_digest}
        if hasattr(value, "events"):
            result["events"] = _jsonable(value.events)
            result["artifacts"] = _jsonable(value.artifacts)
        return result
    if hasattr(value, "project") and hasattr(value, "brief"):
        return {"project": _jsonable(value.project), "brief": _jsonable(value.brief),
                "project_id": value.project_id, "slug": value.slug,
                "brief_sha256": value.brief_sha256}
    return _jsonable(value)


if __name__ == "__main__":
    raise SystemExit(main())
