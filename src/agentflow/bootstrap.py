from __future__ import annotations

import json
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

import yaml

from agentflow.loader import AgentFlow, ConfigurationError, find_project_file, load_yaml, parse_skill


SUPPORTED_CLIENTS = ("codex", "claude", "opencode", "omp")


def _skill_source_path(skill: dict[str, Any]) -> Path:
    return Path(skill.get("source_path", skill["path"]))


def _portable_name(skill: dict[str, Any]) -> str:
    raw = skill.get("name") or str(skill["id"]).split("/", 1)[-1]
    name = re.sub(r"[^a-z0-9]+", "-", str(raw).lower()).strip("-")
    if not name:
        raise ConfigurationError(f"Cannot derive portable skill name for {skill['id']}")
    return name


def _description(skill: dict[str, Any]) -> str:
    if skill.get("description"):
        return str(skill["description"])
    content = _skill_source_path(skill).read_text(encoding="utf-8")
    heading = next((line.removeprefix("# ").strip() for line in content.splitlines() if line.startswith("# ")), None)
    return f"Use the {heading or _portable_name(skill)} project workflow and follow its bundled instructions."


def _portable_skill_content(skill: dict[str, Any]) -> str:
    source = _skill_source_path(skill)
    content = source.read_text(encoding="utf-8")
    name = _portable_name(skill)
    description = _description(skill)
    body = content
    if content.startswith("---\n"):
        end = content.find("\n---\n", 4)
        if end < 0:
            raise ConfigurationError(f"Unclosed front matter: {source}")
        metadata = yaml.safe_load(content[4:end]) or {}
        if not isinstance(metadata, dict):
            raise ConfigurationError(f"Invalid front matter: {source}")
        metadata["name"] = name
        metadata["description"] = description
        body = content[end + 5 :].lstrip("\n")
        front = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True).rstrip()
    else:
        front = yaml.safe_dump({"name": name, "description": description}, sort_keys=False).rstrip()
    return f"---\n{front}\n---\n\n{body}"


def _write_text(path: Path, content: str, *, force: bool) -> str:
    if path.is_symlink():
        raise ConfigurationError(f"Refusing to write through symlink: {path}")
    if path.exists():
        if not path.is_file():
            raise ConfigurationError(f"Destination is not a file: {path}")
        if path.read_text(encoding="utf-8") == content:
            return "unchanged"
        if not force:
            return "conflict"
        action = "replaced"
    else:
        action = "created"
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(content)
        temporary = Path(handle.name)
    temporary.replace(path)
    return action


def _copy_skill(skill: dict[str, Any], destination: Path, *, force: bool) -> list[dict[str, str]]:
    source_dir = _skill_source_path(skill).parent
    report: list[dict[str, str]] = []
    for source in sorted(source_dir.rglob("*")):
        if not source.is_file() or "__pycache__" in source.parts or source.name == ".DS_Store":
            continue
        relative = source.relative_to(source_dir)
        target = destination / relative
        content = _portable_skill_content(skill) if relative.as_posix() == "SKILL.md" else source.read_text(encoding="utf-8") if source.suffix in {".md", ".py", ".js", ".mjs", ".json", ".yaml", ".yml", ".txt"} else None
        if content is None:
            if target.exists() and target.read_bytes() == source.read_bytes():
                action = "unchanged"
            elif target.exists() and not force:
                action = "conflict"
            else:
                existed = target.exists()
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
                action = "replaced" if existed else "created"
        else:
            action = _write_text(target, content, force=force)
        report.append({"path": str(target), "action": action})
    return report


def _copy_memory(source_root: Path, destination_root: Path, *, force: bool) -> list[dict[str, str]]:
    report: list[dict[str, str]] = []
    if not source_root.is_dir():
        return report
    for source in sorted(source_root.rglob("*")):
        if not source.is_file() or "__pycache__" in source.parts or source.name == ".DS_Store":
            continue
        relative = source.relative_to(source_root)
        target = destination_root / relative
        if source.suffix.lower() in {".md", ".txt", ".json", ".yaml", ".yml", ".toml"}:
            action = _write_text(target, source.read_text(encoding="utf-8"), force=force)
        else:
            if target.exists() and target.read_bytes() == source.read_bytes():
                action = "unchanged"
            elif target.exists() and not force:
                action = "conflict"
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                existed = target.exists()
                shutil.copyfile(source, target)
                action = "replaced" if existed else "created"
        report.append({"path": str(target), "action": action})
    return report


def _merge_env_example(path: Path, keys: list[str]) -> str:
    if path.is_symlink():
        raise ConfigurationError(f"Refusing to write through symlink: {path}")
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    present = {
        line.split("=", 1)[0].removeprefix("export ").strip()
        for line in existing.splitlines()
        if "=" in line and not line.lstrip().startswith("#")
    }
    additions = [f"{key}=\n" for key in keys if key not in present]
    if not additions:
        return "unchanged"
    content = existing + ("" if not existing or existing.endswith("\n") else "\n") + "".join(additions)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(content)
        temporary = Path(handle.name)
    temporary.replace(path)
    return "merged" if existing else "created"


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _codex_agent_toml(agent: dict[str, Any]) -> str:
    cfg = agent["agent"]
    lines = [
        f"name = {_toml_string(str(cfg['id']))}",
        f"description = {_toml_string(str(cfg.get('role', cfg['id'])))}",
    ]
    if cfg.get("model"):
        lines.append(f"model = {_toml_string(str(cfg['model']))}")
    if cfg.get("model_provider"):
        lines.append(f"model_provider = {_toml_string(str(cfg['model_provider']))}")
    if cfg.get("model_reasoning_effort"):
        lines.append(f"model_reasoning_effort = {_toml_string(str(cfg['model_reasoning_effort']))}")
    if cfg.get("sandbox_mode"):
        lines.append(f"sandbox_mode = {_toml_string(str(cfg['sandbox_mode']))}")
    instructions = str(cfg.get("instructions", cfg.get("role", "Follow the active AgentFlow step."))).strip()
    lines.extend(["", 'developer_instructions = """', instructions.replace('"""', '\"\"\"'), '"""', ""])
    return "\n".join(lines)


def _claude_agent_markdown(agent: dict[str, Any]) -> str:
    cfg = agent["agent"]
    capabilities = set(cfg.get("allowed_capabilities", []))
    tools = ["Read", "Grep", "Glob", "Bash", "Skill"]
    if capabilities & {"code_write", "document_write", "project_write"}:
        tools.extend(["Edit", "Write"])
    front = {
        "name": cfg["id"],
        "description": cfg.get("role", cfg["id"]),
        "model": "inherit",
        "tools": ", ".join(tools),
    }
    body = str(cfg.get("instructions", cfg.get("role", "Follow the active AgentFlow step."))).strip()
    return f"---\n{yaml.safe_dump(front, sort_keys=False, allow_unicode=True).rstrip()}\n---\n\n{body}\n"


def _mcp_servers(profile_ids: set[str]) -> dict[str, Any]:
    servers: dict[str, Any] = {}
    if "shopify-dev-mcp" in profile_ids:
        servers["shopify-dev-mcp"] = {"command": "npx", "args": ["-y", "@shopify/dev-mcp@latest"]}
    if "figma-readonly" in profile_ids:
        servers["figma-desktop-mcp"] = {
            "type": "http",
            "url": "http://127.0.0.1:3845/mcp",
        }
        servers["figma-developer-mcp"] = {
            "type": "stdio",
            "command": "npx",
            "args": ["-y", "figma-developer-mcp", "--stdio"],
            "env": {"FIGMA_API_KEY": "${FIGMA_API_KEY}"},
        }
    return servers


def _codex_config(agents: list[dict[str, Any]], profiles: set[str]) -> str:
    """Render the project-scoped Codex layer.

    Codex deliberately ignores ``model_providers`` in a project-local
    ``.codex/config.toml`` because provider and authentication settings are
    machine-local.  Custom agent TOMLs are discovered automatically from
    ``.codex/agents``; registering them again with ``config_file`` both is
    unnecessary and, when written relative to this file, resolves to the
    incorrect ``.codex/.codex/agents`` path.  Keep this file limited to
    project-scoped settings (MCP and feature flags).
    """
    lines = [
        "# Generated by AgentFlow. Secrets remain in environment variables.",
        "",
        "[features]",
        "multi_agent = true",
        "",
        "[agents]",
        "# Standalone files under .codex/agents/ are discovered as custom subagents.",
        "enabled = true",
        "max_concurrent_threads_per_session = 4",
        "",
    ]
    if "shopify-dev-mcp" in profiles:
        lines.extend(["[mcp_servers.shopify-dev-mcp]", 'command = "npx"', 'args = ["-y", "@shopify/dev-mcp@latest"]', ""])
    if "figma-readonly" in profiles:
        lines.extend(["[mcp_servers.figma-desktop-mcp]", 'url = "http://127.0.0.1:3845/mcp"', ""])
        lines.extend(["[mcp_servers.figma-developer-mcp]", 'command = "npx"', 'args = ["-y", "figma-developer-mcp", "--stdio"]', 'env_vars = ["FIGMA_API_KEY"]', ""])
    lines.extend([
        "# Custom agents are discovered automatically from .codex/agents/*.toml.",
        "# Codex provider definitions (model_providers.*) belong in ~/.codex/config.toml.",
        "# The project .env is not sourced automatically; export its keys before starting Codex.",
        "",
    ])
    return "\n".join(lines)


def _opencode_config(agents: list[dict[str, Any]], profiles: set[str]) -> str:
    mcp: dict[str, Any] = {}
    for name, server in _mcp_servers(profiles).items():
        if server.get("type") == "http":
            entry = {"type": "remote", "url": server["url"], "enabled": True}
        else:
            entry = {"type": "local", "command": [server["command"], *server.get("args", [])], "enabled": True}
            if server.get("env"):
                entry["environment"] = {key: "{env:" + key + "}" for key in server["env"]}
        mcp[name] = entry
    agent_entries: dict[str, Any] = {}
    for agent in agents:
        cfg = agent["agent"]
        entry: dict[str, Any] = {
            "mode": "subagent" if cfg["id"] != "coordinator" else "primary",
            "description": cfg.get("role", cfg["id"]),
            "prompt": str(cfg.get("instructions", cfg.get("role", "Follow the active AgentFlow step."))).strip(),
        }
        if cfg.get("model") and cfg.get("model_provider"):
            entry["model"] = f"{cfg['model_provider']}/{cfg['model']}"
        agent_entries[str(cfg["id"])] = entry
    return json.dumps({"$schema": "https://opencode.ai/config.json", "mcp": mcp, "agent": agent_entries}, ensure_ascii=False, indent=2) + "\n"


def bootstrap_project(flow: AgentFlow, project_path: Path, clients: list[str], *, force: bool = False) -> dict[str, Any]:
    project_file = find_project_file(project_path)
    if project_file is None:
        raise ConfigurationError("Register the target project before bootstrapping clients")
    project, project_root = flow.load_project(project_path)
    selected = list(dict.fromkeys(clients or SUPPORTED_CLIENTS))
    invalid = [client for client in selected if client not in SUPPORTED_CLIENTS]
    if invalid:
        raise ConfigurationError(f"Unsupported clients: {invalid}")

    skills: dict[str, dict[str, Any]] = {}
    agent_ids: set[str] = set()
    profile_ids: set[str] = set()
    for workflow_id in project.get("allowed_workflows", []):
        plan = flow._build_plan(workflow_id, project, project_root, {}, include_conditional=True)
        for step in plan["steps"]:
            agent_ids.add(str(step["agent"]))
            profile_ids.update(step["mcp_profiles"])
            for source in step["skill_sources"]:
                parsed = parse_skill(_skill_source_path(source))
                parsed.update(source)
                skills[source["id"]] = parsed
        for source in plan.get("executor_skill_sources", []):
            parsed = parse_skill(_skill_source_path(source))
            parsed.update(source)
            skills[source["id"]] = parsed
    # Materialize the portable browser fallback. GPT/Codex uses its installed
    # Computer Use plugin first; non-GPT clients can use this CLI adapter.
    if "browser-preview" in profile_ids:
        ego = flow._load_skill("shared/ego-browser", project)
        skills[ego["id"]] = ego

    agents = [flow._load_agent(agent_id) for agent_id in sorted(agent_ids)]
    names: dict[str, str] = {}
    for skill_id, skill in skills.items():
        name = _portable_name(skill)
        if name in names and names[name] != skill_id:
            raise ConfigurationError(f"Portable skill name collision: {names[name]} and {skill_id}")
        names[name] = skill_id

    report: list[dict[str, str]] = []
    report.extend(_copy_memory(flow.system_root / "memory", project_root / ".agents" / "memory", force=force))
    for skill in skills.values():
        report.extend(_copy_skill(skill, project_root / ".agents" / "skills" / _portable_name(skill), force=force))
    rules_root = flow.system_root / "rules"
    if rules_root.is_dir():
        for source in sorted(rules_root.rglob("*.md")):
            target = project_root / ".agents" / "rules" / source.relative_to(rules_root)
            report.append({"path": str(target), "action": _write_text(target, source.read_text(encoding="utf-8"), force=force)})
    for agent in agents:
        agent_id = str(agent["agent"]["id"])
        target = project_root / ".agents" / "agents" / f"{agent_id}.yaml"
        report.append({"path": str(target), "action": _write_text(target, yaml.safe_dump(agent, sort_keys=False, allow_unicode=True), force=force)})
    for profile_id in sorted(profile_ids):
        profile = load_yaml(flow.system_root / "mcp" / "profiles" / f"{profile_id}.yaml")
        target = project_root / ".agents" / "mcp" / "profiles" / f"{profile_id}.yaml"
        report.append({"path": str(target), "action": _write_text(target, yaml.safe_dump(profile, sort_keys=False, allow_unicode=True), force=force)})

    providers = {str(agent["agent"].get("model_provider")) for agent in agents if agent["agent"].get("model_provider")}
    credentials: list[str] = []
    if "figma-readonly" in profile_ids:
        credentials.append("FIGMA_API_KEY")
    if "minimax" in providers:
        credentials.append("MINIMAX_API_KEY")
    if "deepseek" in providers:
        credentials.append("DEEPSEEK_API_KEY")
    manifest = {
        "generated_by": "agentflow",
        "clients": selected,
        "portable_mcp_servers": sorted(_mcp_servers(profile_ids)),
        "native_or_skill_adapters": {
            "project-files": "client built-in filesystem tools",
            "browser-preview": "Computer Use plugin first in ChatGPT/Codex; ego-browser skill/CLI only after recorded unavailability or failure, and as the portable non-GPT fallback",
            "github-readonly": "Use exactly the Workflow-declared GitHub MCP or Skill/gh CLI route",
            "basecamp-readonly": "Use exactly the Workflow-declared Basecamp MCP or Skill/CLI route",
            "public-web-search": "client built-in web search",
        },
        "credentials": credentials,
    }
    report.append({"path": str(project_root / ".agents/mcp/manifest.json"), "action": _write_text(project_root / ".agents/mcp/manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", force=force)})

    if "codex" in selected:
        report.append({"path": str(project_root / ".codex/config.toml"), "action": _write_text(project_root / ".codex/config.toml", _codex_config(agents, profile_ids), force=force)})
        for agent in agents:
            agent_id = str(agent["agent"]["id"])
            target = project_root / ".codex" / "agents" / f"{agent_id}.toml"
            report.append({"path": str(target), "action": _write_text(target, _codex_agent_toml(agent), force=force)})
    if "claude" in selected or "omp" in selected:
        for agent in agents:
            agent_id = str(agent["agent"]["id"])
            target = project_root / ".claude" / "agents" / f"{agent_id}.md"
            report.append({"path": str(target), "action": _write_text(target, _claude_agent_markdown(agent), force=force)})
        for skill in skills.values():
            name = _portable_name(skill)
            shim = f"---\nname: {name}\ndescription: {json.dumps(_description(skill), ensure_ascii=False)}\n---\n\nRead and follow `../../../.agents/skills/{name}/SKILL.md` completely. Resolve its supporting files from that canonical directory.\n"
            target = project_root / ".claude" / "skills" / name / "SKILL.md"
            report.append({"path": str(target), "action": _write_text(target, shim, force=force)})
    if "claude" in selected or "omp" in selected:
        shared_mcp = json.dumps({"mcpServers": _mcp_servers(profile_ids)}, ensure_ascii=False, indent=2) + "\n"
        report.append({"path": str(project_root / ".mcp.json"), "action": _write_text(project_root / ".mcp.json", shared_mcp, force=force)})
    if "opencode" in selected:
        report.append({"path": str(project_root / "opencode.json"), "action": _write_text(project_root / "opencode.json", _opencode_config(agents, profile_ids), force=force)})
    if "omp" in selected:
        omp_config = "setupVersion: 1\n# OMP discovers .agents skills, .claude agents, and root .mcp.json.\n"
        report.append({"path": str(project_root / ".omp/config.yml"), "action": _write_text(project_root / ".omp/config.yml", omp_config, force=force)})

    env_example = project_root / ".env.example"
    env_action = _merge_env_example(env_example, credentials)
    if env_action != "unchanged" or env_example.exists():
        report.append({"path": str(env_example), "action": env_action})

    conflicts = [item for item in report if item["action"] == "conflict"]
    return {
        "project_root": str(project_root),
        "clients": selected,
        "skills": sorted(names),
        "agents": sorted(agent_ids),
        "mcp_profiles": sorted(profile_ids),
        "memory_files": sorted(
            item["path"] for item in report if "/.agents/memory/" in item["path"]
        ),
        "files": report,
        "conflicts": [item["path"] for item in conflicts],
    }
