import argparse
import json
import sqlite3
import sys
from pathlib import Path

from .core import WorkflowError, config, database, execute, read_json, resolve, check_project, inspect_import


def main():
    parser = argparse.ArgumentParser(description="Offline SEO workflow; never publishes or calls external services")
    sub = parser.add_subparsers(dest="command", required=True)
    plan = sub.add_parser("plan")
    plan.add_argument("--workflow", choices=["technical", "go"], default="technical")
    run = sub.add_parser("run")
    run.add_argument("--profile", required=True)
    run.add_argument("--manifest", required=True)
    run.add_argument("--workspace", required=True)
    run.add_argument("--workflow", choices=["technical", "go"], default="technical")
    preflight = sub.add_parser("preflight")
    preflight.add_argument("--profile", required=True)
    inspect = sub.add_parser("inspect-import")
    inspect.add_argument("--file", required=True)
    inspect.add_argument("--format", choices=["json", "csv", "xlsx"], required=True)
    inspect.add_argument("--sheet")
    status = sub.add_parser("status")
    status.add_argument("--workspace", required=True)
    status.add_argument("--project", required=True)
    artifact = sub.add_parser("resolve")
    artifact.add_argument("--workspace", required=True)
    artifact.add_argument("--project", required=True)
    artifact.add_argument("--run", required=True)
    artifact.add_argument("--artifact", required=True)
    roles = sub.add_parser("roles")
    roles.add_argument("--team")
    process = sub.add_parser("process", help="Coordinate Codex work products; no external execution")
    operations = process.add_subparsers(dest="operation", required=True)
    pp = operations.add_parser("plan")
    pp.add_argument("--workflow", required=True)
    ps = operations.add_parser("start")
    ps.add_argument("--profile", required=True)
    ps.add_argument("--workflow", required=True)
    ps.add_argument("--workspace", required=True)
    ps.add_argument("--synthetic", action="store_true")
    for name in ["source", "submit", "status", "mark", "template"]:
        command = operations.add_parser(name)
        command.add_argument("--workspace", required=True)
        command.add_argument("--project", required=True)
        command.add_argument("--run", required=True)
        if name in {"submit", "mark", "template"}:
            command.add_argument("--node", required=True)
        if name == "source":
            command.add_argument("--manifest", required=True)
        if name == "submit":
            command.add_argument("--result", required=True)
        if name == "mark":
            command.add_argument("--state", choices=["pending", "blocked_input", "blocked_permission", "not_applicable"], required=True)
            command.add_argument("--reason", required=True)
    args = parser.parse_args()
    try:
        if args.command == "roles":
            from .processes import catalog
            result = {k: v for k, v in catalog().items() if args.team is None or k.startswith(args.team + ".")}
        elif args.command == "process":
            from . import processes
            if args.operation == "plan":
                result = processes.plan(args.workflow)
            elif args.operation == "start":
                result = processes.start(args.profile, args.workflow, args.workspace, args.synthetic)
            elif args.operation == "source":
                result = processes.add_source(args.workspace, args.project, args.run, args.manifest)
            elif args.operation == "submit":
                result = processes.submit(args.workspace, args.project, args.run, args.node, args.result)
            elif args.operation == "mark":
                result = processes.mark(args.workspace, args.project, args.run, args.node, args.state, args.reason)
            elif args.operation == "template":
                result = processes.template(args.workspace, args.project, args.run, args.node)
            else:
                result = processes.status(args.workspace, args.project, args.run)
        elif args.command == "plan":
            result = {"nodes": config("workflows")[args.workflow], "executable_scope": "offline technical import only", "analysis_status": "partial"}
        elif args.command == "preflight":
            profile = read_json(args.profile)
            check_project(profile)
            result = {"project_id": profile["project_id"], "local_import": "available",
                      "drive": "adapter_not_implemented", "labrika": "not_verified", "gsc": "not_verified",
                      "yandex_webmaster": "not_verified", "yandex_metrika": "not_verified", "wordstat": "not_verified",
                      "paid_calls": "not_implemented", "publication": "not_implemented",
                      "access_probe": "not_performed_by_cli",
                      "session_tools": "not_inherited; see dated read-only probe evidence in docs/access-verification.md"}
        elif args.command == "inspect-import":
            result = inspect_import(args.file, args.format, args.sheet)
        elif args.command == "run":
            result = execute(args.profile, args.manifest, args.workspace, args.workflow)
        else:
            if not (Path(args.workspace) / "state.sqlite3").is_file():
                raise WorkflowError("No local registry; run has not been executed")
            with database(args.workspace) as con:
                if args.command == "resolve":
                    result = {"path": str(resolve(con, args.project, args.run, args.artifact, args.workspace))}
                else:
                    result = [dict(zip(["run_id", "status", "created_at", "path"], row)) for row in con.execute(
                        "SELECT run_id,status,created_at,output_path FROM runs WHERE project_id=? ORDER BY created_at", (args.project,))]
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (WorkflowError, OSError, ValueError, KeyError, sqlite3.Error) as exc:
        print(f"Blocked: {exc}", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
