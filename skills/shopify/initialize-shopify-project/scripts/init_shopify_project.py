#!/usr/bin/env python3
"""Safely install the bundled Shopify project baseline into a local repository."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_DIR / "assets" / "templates"

FILE_MAPPINGS = {
    "codex/config.toml": ".codex/config.toml",
    "claude/mcp.json": ".claude/mcp.json",
    "opencode/opencode.json": ".opencode/opencode.json",
    "omp/config.yml": ".omp/config.yml",
    "omp/mcp.json": ".omp/mcp.json",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install Shopify agent rules and local tool configuration."
    )
    parser.add_argument("--target", type=Path, required=True, help="Shopify project root")
    parser.add_argument("--global-root", type=Path, help="Reuse the installed global rules and client adapters without copying a project-local layer")
    parser.add_argument("--dry-run", action="store_true", help="Report without writing")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace conflicting mapped files; never replaces .env or .gitignore",
    )
    parser.add_argument(
        "--copy-guides",
        action="store_true",
        help="Copy workspace guides into .agents/guides",
    )
    parser.add_argument("--json", action="store_true", help="Emit a JSON report")
    return parser.parse_args()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def assert_safe_destination(path: Path) -> None:
    if path.is_symlink():
        raise RuntimeError(f"refusing to write through symlink: {path}")


def install_file(
    source: Path,
    destination: Path,
    *,
    dry_run: bool,
    force: bool,
) -> str:
    assert_safe_destination(destination)
    if destination.exists():
        if not destination.is_file():
            raise RuntimeError(f"destination is not a file: {destination}")
        if source.read_bytes() == destination.read_bytes():
            return "unchanged"
        if not force:
            return "conflict"
        action = "replaced"
    else:
        action = "created"

    if not dry_run:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    return action


def merge_line_file(source: Path, destination: Path, *, dry_run: bool) -> str:
    assert_safe_destination(destination)
    existed = destination.exists()
    existing = read_text(destination) if existed else ""
    existing_lines = set(existing.splitlines())
    missing = [line for line in read_text(source).splitlines() if line not in existing_lines]
    if not missing:
        return "unchanged"
    if not dry_run:
        destination.parent.mkdir(parents=True, exist_ok=True)
        separator = "" if not existing or existing.endswith("\n") else "\n"
        block = "\n".join(missing).rstrip() + "\n"
        destination.write_text(existing + separator + block, encoding="utf-8")
    return "merged" if existed else "created"


def env_keys(content: str) -> set[str]:
    keys: set[str] = set()
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key = line.split("=", 1)[0].removeprefix("export ").strip()
        if key:
            keys.add(key)
    return keys


def merge_env(source: Path, destination: Path, *, dry_run: bool) -> str:
    assert_safe_destination(destination)
    existed = destination.exists()
    existing = read_text(destination) if existed else ""
    present = env_keys(existing)
    additions = []
    for raw_line in read_text(source).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key = line.split("=", 1)[0].strip()
        if key not in present:
            additions.append(f"{key}=")
    if not additions:
        return "unchanged"
    if not dry_run:
        destination.parent.mkdir(parents=True, exist_ok=True)
        separator = "" if not existing or existing.endswith("\n") else "\n"
        destination.write_text(
            existing + separator + "\n".join(additions) + "\n", encoding="utf-8"
        )
    return "merged" if existed else "created"


def all_rule_mappings() -> dict[str, str]:
    mappings: dict[str, str] = {}
    for source in sorted((TEMPLATES / "rules").rglob("*.md")):
        relative = source.relative_to(TEMPLATES).as_posix()
        mappings[relative] = f".agents/{relative}"
    return mappings


def all_guide_mappings() -> dict[str, str]:
    mappings: dict[str, str] = {}
    for source in sorted((TEMPLATES / "guides").rglob("*.md")):
        relative = source.relative_to(TEMPLATES / "guides").as_posix()
        mappings[f"guides/{relative}"] = f".agents/guides/{relative}"
    return mappings


def main() -> int:
    args = parse_args()
    target = args.target.expanduser().resolve()
    if not target.exists() or not target.is_dir():
        print(f"error: target is not an existing directory: {target}", file=sys.stderr)
        return 2
    if not TEMPLATES.is_dir():
        print(f"error: bundled templates are missing: {TEMPLATES}", file=sys.stderr)
        return 2

    global_root = args.global_root.expanduser().resolve() if args.global_root else None
    inherited_rules: list[Path] = []
    if global_root:
        required = [global_root / "AGENTS.md"]
        inherited_rules = [global_root / name for name in all_rule_mappings()]
        required.extend(inherited_rules)
        missing = [str(path) for path in required if not path.is_file()]
        if missing:
            print(f"error: global layer is incomplete: {', '.join(missing)}", file=sys.stderr)
            return 2
    mappings = {} if global_root else {**FILE_MAPPINGS, **all_rule_mappings()}
    if args.copy_guides:
        mappings.update(all_guide_mappings())

    report: list[dict[str, str]] = []
    report.extend({"path": str(path), "action": "inherited"} for path in inherited_rules)
    try:
        for source_name, destination_name in sorted(mappings.items()):
            source = TEMPLATES / source_name
            if not source.is_file():
                raise RuntimeError(f"missing bundled template: {source}")
            action = install_file(
                source,
                target / destination_name,
                dry_run=args.dry_run,
                force=args.force,
            )
            report.append({"path": destination_name, "action": action})

        env_action = merge_env(TEMPLATES / "env/.env", target / ".env", dry_run=args.dry_run)
        report.append({"path": ".env", "action": env_action})
        ignore_action = merge_line_file(
            TEMPLATES / "gitignore/shopify-project.gitignore",
            target / ".gitignore",
            dry_run=args.dry_run,
        )
        report.append({"path": ".gitignore", "action": ignore_action})
    except (OSError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({"target": str(target), "global_root": str(global_root) if global_root else None, "dry_run": args.dry_run, "files": report}, indent=2))
    else:
        mode = "DRY RUN" if args.dry_run else "APPLIED"
        print(f"{mode}: {target}")
        for item in report:
            print(f"{item['action']:>9}  {item['path']}")

    conflicts = [item for item in report if item["action"] == "conflict"]
    if conflicts:
        print(
            "conflicts preserved; merge them manually or rerun with explicit --force",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
