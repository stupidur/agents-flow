from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import yaml

from agentflow.loader import AgentFlow, ConfigurationError, load_yaml
from agentflow.bootstrap import SUPPORTED_CLIENTS, bootstrap_project
from agentflow.runtime import (
    default_sandbox,
    execute_codex,
    prepare_workflow_bundle,
    prepare_run,
    resolve_output_path,
    write_json,
)


def parse_value(raw: str) -> Any:
    return yaml.safe_load(raw)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agentflow", description="Resolve project-scoped agent workflows")
    parser.add_argument("--system-root", type=Path, help="Central configuration directory; otherwise use AGENT_SYSTEM_ROOT or global registration")
    parser.add_argument("--global-root", type=Path, default=Path(os.environ.get("AGENTFLOW_GLOBAL_ROOT", Path.home() / ".agents")), help="Shared global layer directory (default: ~/.agents)")
    commands = parser.add_subparsers(dest="command", required=True)

    plan = commands.add_parser("plan", help="Generate a workflow handoff package")
    plan.add_argument("workflow")
    plan.add_argument("--project", type=Path, default=Path.cwd())
    plan.add_argument("--set", action="append", default=[], metavar="KEY=VALUE")
    plan.add_argument("--prompt", help="Task instructions to include in workflow.md")
    plan.add_argument("--output", type=Path, metavar="FILE", help="Also write the raw plan JSON to FILE")
    plan.add_argument("--output-dir", type=Path, metavar="DIR", help="Write the workflow package to DIR")
    plan.add_argument("--stdout", action="store_true", help="Also print the full machine-readable plan")

    run = commands.add_parser("run", help="Persist a plan and execute it with Codex")
    run.add_argument("workflow")
    run.add_argument("--project", type=Path, default=Path.cwd())
    run.add_argument("--set", action="append", default=[], metavar="KEY=VALUE")
    run.add_argument("--prompt", required=True, help="Task instructions for the workflow executor")
    run.add_argument(
        "--sandbox",
        choices=["read-only", "workspace-write"],
        help="Codex sandbox policy; defaults to the least privilege required by the plan",
    )
    run.add_argument("--dry-run", action="store_true", help="Write the run files without starting Codex")
    run.add_argument(
        "--skip-git-repo-check",
        action="store_true",
        help="Pass --skip-git-repo-check to Codex",
    )

    register = commands.add_parser("register", help="Create a lightweight project entry")
    register_scope = register.add_mutually_exclusive_group()
    register_scope.add_argument("--project", type=Path, default=Path.cwd())
    register_scope.add_argument("--global", dest="global_scope", action="store_true", help="Register the global shared layer instead of a project")
    register.add_argument("--global-root", type=Path, default=argparse.SUPPRESS)
    register.add_argument("--type", choices=["default", "java", "shopify"], required=True)
    register.add_argument("--project-id")
    register.add_argument("--force", action="store_true")

    bootstrap = commands.add_parser("bootstrap", help="Materialize portable skills and client adapters")
    bootstrap_scope = bootstrap.add_mutually_exclusive_group()
    bootstrap_scope.add_argument("--project", type=Path, default=Path.cwd())
    bootstrap_scope.add_argument("--global", dest="global_scope", action="store_true", help="Materialize the global shared layer instead of a project")
    bootstrap.add_argument("--global-root", type=Path, default=argparse.SUPPRESS)
    bootstrap.add_argument("--client", action="append", choices=SUPPORTED_CLIENTS, default=[])
    bootstrap.add_argument("--force", action="store_true")

    commands.add_parser("validate", help="Validate projects and their allowed workflows")
    commands.add_parser("doctor", help="Check local orchestration prerequisites")
    return parser


def parse_flags(values: list[str]) -> dict[str, Any]:
    flags: dict[str, Any] = {}
    for value in values:
        if "=" not in value:
            raise ConfigurationError(f"Expected KEY=VALUE, got: {value}")
        key, raw = value.split("=", 1)
        if not key:
            raise ConfigurationError("Flag names cannot be empty")
        flags[key] = parse_value(raw)
    return flags


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        system_root = args.system_root or os.environ.get("AGENT_SYSTEM_ROOT")
        if system_root is None:
            global_file = args.global_root.expanduser() / "project.yaml"
            if global_file.is_file():
                global_config = load_yaml(global_file)
                if global_config.get("scope") == "global":
                    system_root = global_config.get("system_root")
        flow = AgentFlow(Path(system_root) if system_root else Path.cwd(), args.global_root)
        if args.command == "plan":
            result = flow.plan(args.workflow, args.project, parse_flags(args.set))
            bundle = prepare_workflow_bundle(result, args.prompt or "", args.output_dir)
            if args.output:
                output_path = resolve_output_path(Path(result["project_root"]), args.output)
                write_json(output_path, json.loads(Path(bundle["plan_path"]).read_text(encoding="utf-8")))
                bundle["additional_plan_path"] = str(output_path)
            print(json.dumps(bundle, ensure_ascii=False, indent=2))
            if args.stdout:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        if args.command == "run":
            plan = flow.plan(args.workflow, args.project, parse_flags(args.set))
            project_root = Path(plan["project_root"])
            required_agent_files = [
                project_root / ".codex" / "agents" / f"{step['agent']}.toml"
                for step in plan["steps"]
            ]
            if not (project_root / ".codex" / "config.toml").is_file() or any(
                not path.is_file() for path in required_agent_files
            ):
                bootstrap_result = bootstrap_project(flow, project_root, ["codex"])
                if bootstrap_result["conflicts"]:
                    raise ConfigurationError(
                        "Codex bootstrap has conflicts; rerun bootstrap with --force after reviewing: "
                        + ", ".join(bootstrap_result["conflicts"])
                    )

            sandbox = args.sandbox or default_sandbox(plan)
            run_result = prepare_run(plan, args.prompt, sandbox)
            printable = {key: value for key, value in run_result.items() if key != "prompt"}
            print(json.dumps(printable, ensure_ascii=False, indent=2))
            if args.dry_run:
                return 0
            exit_code = execute_codex(run_result, skip_git_repo_check=args.skip_git_repo_check)
            final_metadata = json.loads(Path(run_result["metadata_path"]).read_text(encoding="utf-8"))
            print(json.dumps(final_metadata, ensure_ascii=False, indent=2))
            return exit_code
        if args.command == "validate":
            errors = flow.validate()
            if errors:
                print("\n".join(errors))
                return 1
            print("Agent Flow configuration is valid.")
            return 0
        if args.command == "register":
            if args.global_scope:
                result = flow.register_global(args.type, args.project_id, force=args.force)
            else:
                result = flow.register_project(args.project, args.type, args.project_id, force=args.force)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        if args.command == "bootstrap":
            result = bootstrap_project(flow, args.project, args.client, force=args.force, global_scope=args.global_scope)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 1 if result["conflicts"] else 0
        print(json.dumps(flow.doctor(), ensure_ascii=False, indent=2))
        return 0
    except ConfigurationError as exc:
        print(f"error: {exc}")
        return 2
