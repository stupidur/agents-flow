from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agentflow.loader import ConfigurationError


def default_sandbox(plan: dict[str, Any]) -> str:
    """Choose the least-privileged sandbox that can satisfy a workflow."""
    write_capabilities = {"code_write", "document_write"}
    if any(write_capabilities.intersection(step.get("capabilities", [])) for step in plan.get("steps", [])):
        return "workspace-write"
    return "read-only"


def _write_text(path: Path, content: str) -> Path:
    if path.is_symlink():
        raise ConfigurationError(f"Refusing to write through symlink: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def write_json(path: Path, value: dict[str, Any]) -> Path:
    return _write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def resolve_output_path(project_root: Path, output: Path) -> Path:
    """Resolve a plan output path relative to the target project."""
    if output.is_absolute():
        return output.expanduser().resolve()
    return (project_root / output).resolve()


def _new_run_directory(project_root: Path, workflow_id: str) -> tuple[str, Path]:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = project_root / ".agentflow" / "runs"
    task_id = f"{workflow_id}-{timestamp}"
    run_dir = base / task_id
    suffix = 2
    while run_dir.exists():
        task_id = f"{workflow_id}-{timestamp}-{suffix}"
        run_dir = base / task_id
        suffix += 1
    run_dir.mkdir(parents=True, exist_ok=False)
    return task_id, run_dir


def _new_workflow_directory(project_root: Path, workflow_id: str) -> tuple[str, Path]:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = project_root / ".agentflow" / "workflows"
    task_id = f"{workflow_id}-{timestamp}"
    workflow_dir = base / task_id
    suffix = 2
    while workflow_dir.exists():
        task_id = f"{workflow_id}-{timestamp}-{suffix}"
        workflow_dir = base / task_id
        suffix += 1
    workflow_dir.mkdir(parents=True, exist_ok=False)
    return task_id, workflow_dir


def _relative_to_project(path: Path, project_root: Path) -> str:
    try:
        return str(path.relative_to(project_root))
    except ValueError:
        return str(path)


def _portable_dependency_path(value: str, global_root: str | None = None) -> str:
    path = Path(value)
    if global_root and path.is_absolute() and path.is_relative_to(Path(global_root)):
        return value
    parts = path.parts
    for marker, prefix in (("rules", ".agents/rules"), ("references", ".agents/references")):
        if marker in parts:
            index = len(parts) - 1 - parts[::-1].index(marker)
            suffix = Path(*parts[index + 1:]) if index + 1 < len(parts) else Path()
            return str(Path(prefix) / suffix)
    return value


def _global_context_text(plan: dict[str, Any]) -> str:
    context = plan.get("global_context")
    if not context:
        return ""
    return (
        f"Read the global instructions `{context['agents_md']}` before acting. "
        f"The shared layer `{context['root']}` is read-only task context; it is not the project root. "
        f"Use the global memory index `{context['memory_index']}` only for task-relevant context. "
        "Read and obey applicable global rules alongside project rules; do not silently weaken them. "
        "If instructions conflict, follow explicit user instructions and report the conflict. "
        "When creating or updating project AGENTS.md, include a global-rules section referencing "
        "the global instructions and applicable rule paths. Keep task requirements evidence-based "
        "and all task writes inside the target project. Resolve .agents/ paths in Skills through "
        "the plan's explicit global Skill, Rule, memory, and MCP file paths when the local layer is absent."
    )


def _materialize_task_paths(value: Any, task_id: str) -> Any:
    if isinstance(value, dict):
        return {key: _materialize_task_paths(item, task_id) for key, item in value.items()}
    if isinstance(value, list):
        return [_materialize_task_paths(item, task_id) for item in value]
    if isinstance(value, str):
        return value.replace("<task-id>", task_id)
    return value


def _output_contract_text(outputs: list[dict[str, Any]]) -> str:
    if not outputs:
        return "none"
    values = []
    for output in outputs:
        target = output.get("path") or output.get("transport", "agent_result")
        required = "required" if output.get("required", True) else "optional"
        values.append(f"`{output['id']}` -> `{target}` ({required})")
    return ", ".join(values)


def _input_contract_text(inputs: list[dict[str, Any]]) -> str:
    if not inputs:
        return "none"
    return ", ".join(f"`{item['step']}.{item['artifact']}`" for item in inputs)


def build_execution_prompt(plan: dict[str, Any], task_prompt: str, plan_path: Path) -> str:
    project_root = Path(plan["project_root"])
    plan_reference = _relative_to_project(plan_path, project_root)
    steps = plan.get("steps", [])
    step_lines = []
    for index, step in enumerate(steps, start=1):
        skills = ", ".join(step.get("skills", [])) or "none"
        rules = ", ".join(_portable_dependency_path(rule, plan.get("global_context", {}).get("root")) for rule in step.get("rules", [])) or "none"
        mcp_profiles = ", ".join(step.get("mcp_profiles", [])) or "none"
        outputs = _output_contract_text(step.get("outputs", []))
        inputs_from = _input_contract_text(step.get("inputs_from", []))
        gates = ", ".join(gate.get("id", "") for gate in step.get("gates", [])) or "none"
        requires_gates = ", ".join(step.get("requires_gates", [])) or "none"
        remote_read = step.get("remote_read")
        route = ""
        if remote_read:
            if remote_read.get("type") == "skill":
                route = (
                    f" remote-read: use Skill `{remote_read.get('skill')}` "
                    f"via `{remote_read.get('command')}` only (read-only); "
                    f"on unavailable: `{remote_read.get('on_unavailable', 'stop')}`."
                )
            else:
                route = (
                    f" remote-read: use MCP profile `{remote_read.get('profile')}` only; "
                    f"on unavailable: `{remote_read.get('on_unavailable', 'stop')}`."
                )
        approval = "approval required" if step.get("approval_required") else "no approval flag"
        step_lines.append(
            f"{index}. `{step['id']}` using agent `{step['agent']}`; "
            f"skills: {skills}; rules: {rules}; MCP profiles: {mcp_profiles}; "
            f"inputs_from: {inputs_from}; outputs: {outputs}; gates: {gates}; "
            f"requires_gates: {requires_gates};{route} {approval}."
        )

    steps_text = "\n".join(step_lines) or "No executable steps were selected."
    executor_skills = ", ".join(plan.get("executor_skills", [])) or "none"
    inputs = plan.get("inputs", {})
    return f"""You are the execution coordinator for an AgentFlow workflow.

Active workflow: `{plan['workflow']}`
Handoff contract version: `{plan.get('contract_version', 'missing')}`
Plan file: `{plan_reference}`
Executor Skill: {executor_skills}
Inputs: {json.dumps(inputs, ensure_ascii=False, sort_keys=True)}

Read the plan file before changing anything. Execute the selected steps in order;
the plan is authoritative and is not merely a suggestion. Do not silently skip a
step. Use the project's materialized `.agents/skills/` files and `.codex/agents/`
agents when they are available. Only use the MCP profiles listed for the current
step. Respect every `approval_required` marker and ask for approval before a
write operation that the step marks as requiring approval.

If `.agents/memory/README.md` exists, read it and load only memory files relevant
to this task. Memory is contextual guidance only; the handoff, `AGENTS.md`, and
Rules take precedence.

For every step, read the full rule files listed under `rules` before changing
matching files. Apply the rule-routing decision from the selected Skill rather
than treating the rule list as background context.

Selected steps:
{steps_text}

{_global_context_text(plan)}

Execution requirements:
- Keep all file changes inside the target project.
- Dispatch each step to its listed Agent ID through the client's multi-agent tool;
  do not substitute the primary Agent.
- Before declaring a tool unavailable, search delayed-loaded tools for the
  required Agent route and the installed Computer Use plugin Skill/server.
- Before each step, report the step, Agent ID, read Skills/Rules, and MCP scope.
- When dispatching a step, pass the child Agent the complete step contract:
  capabilities, Skills, Rules, MCP scope, inputs_from, and every output's
  transport and exact path. Do not dispatch only the generic Agent role.
- Before acting, verify every required `inputs_from` artifact exists and read it completely.
- Write every declared file output to its exact path and verify it exists, or return
  every declared `agent_result` as parseable structured JSON under its exact artifact ID.
- A step that requires a gate may start only after that gate has passed. If the gate or
  source policy declares `skip_dependents`, mark that step and its dependent branch
  skipped with the exact reason, then continue unrelated steps; never run a dependent
  step without its gate or source artifact.
- If a remote-read route declares `on_unavailable: skip_dependents`, write the declared
  unavailable/status artifact, mark the remote-read step unavailable, skip only its
  dependent branch, and continue unrelated steps. Do not switch routes or invent data.
- Follow `source_policy` exactly; when it says `artifact-only`, do not substitute local files, branch names, filenames, or assumptions.
- For each remote-read route, use exactly the declared Skill/command or MCP profile;
  never switch routes.
- In ChatGPT/Codex, use the installed Computer Use plugin first for browser and
  desktop UI interaction. Record unavailability, unsupported operations, or actual
  call failure before falling back to `ego-browser`; if Ego Browser is also
  unavailable, unsupported, or fails, use `playwright-cli` under the same
  browser-preview profile. Non-GPT clients start with Ego Browser. Browser CLI
  fallbacks do not replace native desktop control or expand remote-write permissions.
- For steps sharing a `parallel_group`, use independent subagents only when that
  is supported by the current client; otherwise execute them independently and
  merge their findings before continuing.
- Run the relevant tests after implementation steps.
- At the end, summarize completed steps, skipped steps (with reasons), tests, and
  changed files, Agent IDs, tools, and visual evidence. Do not claim completion
  until all required steps are complete. Do not run `agentflow run` recursively.

User task:
{task_prompt.strip()}
"""


def build_workflow_markdown(plan: dict[str, Any], task_prompt: str, plan_path: Path) -> str:
    project_root = Path(plan["project_root"])
    plan_reference = _relative_to_project(plan_path, project_root)
    lines = [
        f"# AgentFlow Workflow: `{plan['workflow']}`",
        "",
        "> This is a generated handoff file. Read it before acting. Execute the workflow directly; do not invoke `agentflow run`.",
        "",
        "## Task",
        "",
        task_prompt.strip() or "Fill in the task-specific request before handing this file to an agent.",
        "",
        "## Execution Contract",
        "",
        "- Read the executor Skill listed below before executing any step.",
        "- If `.agents/memory/README.md` exists, read it and load only task-relevant memory; memory never overrides the handoff, `AGENTS.md`, or Rules.",
        "- Treat the workflow Agent as a mandatory route; dispatch each step to the specified Agent ID via the client's multi-agent tool.",
        "- Before declaring a route or tool unavailable, search delayed-loaded tools for `multi_agent_v1__spawn_agent` and the installed Computer Use plugin Skill/server.",
        "- Execute the selected steps in the listed order.",
        "- Read the referenced Skill files completely before each applicable step.",
        "- Before each step, report its name, Agent ID, read Skills/Rules, and MCP profile/tool scope.",
        "- When dispatching a step, pass the child Agent the full step contract, including capabilities, Skills, Rules, MCP scope, inputs, and exact output transport/path.",
        "- Read every rule listed for the current step before changing matching files.",
        "- Use only the MCP profiles listed for the current step.",
        "- For each `Remote read route`, use exactly the declared Skill/command or MCP profile; never switch routes.",
        "- Verify every required `inputs_from` artifact before acting. If a declared source policy or gate uses `skip_dependents`, mark only the dependent branch skipped with the exact reason and continue unrelated steps; otherwise stop.",
        "- Produce every declared output for completed or unavailable steps at its exact path or through the declared structured-result transport; verify file outputs and parse agent_result JSON; explicitly skipped steps must record the exact reason and must not fabricate output.",
        "- Do not start a step until every `requires_gates` entry has passed. A failed gate with `on_failure: skip_dependents` skips only its dependent branch and records the reason; other failures stop the workflow.",
        "- Follow each `source_policy`; `artifact-only` forbids substitution from local specs, branch names, filenames, or assumptions.",
        "- For remote reads with `on_unavailable: skip_dependents`, write the declared unavailable/status artifact, skip only dependent steps, and continue independent steps without changing the route.",
        "- In ChatGPT/Codex, use the installed Computer Use plugin first for browser or desktop UI interaction; after recorded unavailability, unsupported operations, or an actual call failure, fall back to `ego-browser`, then `playwright-cli` if Ego Browser is also unavailable, unsupported, or fails, under the same browser-preview profile. Non-GPT clients start with Ego Browser. Browser CLI fallbacks do not replace native desktop control or expand remote-write permissions.",
        "- Respect every approval requirement and ask before the marked write operation.",
        "- Keep changes inside the target project; do not push, merge, publish, or deploy unless explicitly requested.",
        "- Run relevant tests after implementation steps.",
        "- Do not claim completion until every required step is complete; report each step's status, Agent ID, Skills, Rules, tools, changed files, tests, visual URL/viewports/evidence, and skipped items with reasons.",
        "- Do not run `agentflow run`; orchestrate through the current client session.",
        "",
        "## Plan File",
        "",
        f"Handoff contract version: `{plan.get('contract_version', 'missing')}`",
        "",
        f"Machine-readable plan: `{plan_reference}`",
        "",
        "## Executor Skill",
        "",
    ]

    executor_skills = plan.get("executor_skills", [])
    if executor_skills:
        executor_sources = {source["id"]: source for source in plan.get("executor_skill_sources", [])}
        for skill in executor_skills:
            source = executor_sources.get(skill, {})
            path = source.get("execution_path", f".agents/skills/{str(skill).split('/', 1)[-1]}/SKILL.md")
            lines.append(f"- `{path}`")
    else:
        lines.append("- none")
    lines.extend([
        "",
        "## Inputs",
        "",
    ])
    inputs = plan.get("inputs", {})
    if inputs:
        for key, value in inputs.items():
            lines.append(f"- `{key}`: `{value}`")
    else:
        lines.append("- none")
    chain = plan.get("workflow_chain", [])
    if chain:
        lines.extend(["", "## Workflow Chain", "", f"`{' → '.join(chain)}`"])
    if plan.get("global_context"):
        lines.extend(["", "## Global Rules", "", _global_context_text(plan), ""])
    lines.extend([
        "",
        "## Outputs",
        "",
    ])

    output = plan.get("output", {})
    artifacts = output.get("artifacts", {}) if isinstance(output, dict) else {}
    if artifacts:
        for artifact_name, artifact_path in artifacts.items():
            lines.append(f"- `{artifact_name}`: `{artifact_path}`")
    else:
        lines.append("- Report the completed work and changed files to the user.")
    lines.extend(["", "## Steps", ""])

    for index, step in enumerate(plan.get("steps", []), start=1):
        lines.extend([
            f"### {index}. `{step['id']}`",
            "",
            f"- Agent: `{step['agent']}`",
            f"- Capabilities: {', '.join(f'`{item}`' for item in step.get('capabilities', [])) or 'none'}",
            f"- Skills: {', '.join(f'`{item}`' for item in step.get('skills', [])) or 'none'}",
            f"- MCP profiles: {', '.join(f'`{item}`' for item in step.get('mcp_profiles', [])) or 'none'}",
            f"- Parallel group: `{step['parallel_group']}`" if step.get("parallel_group") else "- Parallel group: none",
            f"- Approval: {'required' if step.get('approval_required') else 'not separately required'}",
        ])
        if step.get("agent_file"):
            lines.append(f"- Agent file: `{step['agent_file']}`")
        for source in step.get("skill_sources", []):
            skill_name = str(source["id"]).split("/", 1)[-1]
            execution_path = source.get("execution_path", f".agents/skills/{skill_name}/SKILL.md")
            path_scope = "global shared path" if Path(execution_path).is_absolute() else "materialized project path"
            lines.append(f"- Skill file: `{execution_path}` ({path_scope})")
        rules = [_portable_dependency_path(rule, plan.get("global_context", {}).get("root")) for rule in step.get("rules", [])]
        lines.append(f"- Rules (must read before matching changes): {', '.join(f'`{rule}`' for rule in rules) or 'none'}")
        outputs = step.get("outputs", [])
        lines.append(f"- Outputs (must produce before completing step): {_output_contract_text(outputs)}")
        lines.append(f"- Inputs from prior steps (must read before acting): {_input_contract_text(step.get('inputs_from', []))}")
        gates = step.get("gates", [])
        if gates:
            lines.append(
                "- Gates produced by this step: "
                + ", ".join(f"`{gate['id']}` ({gate['type']}; failure={gate['on_failure']})" for gate in gates)
            )
        requires_gates = step.get("requires_gates", [])
        if requires_gates:
            lines.append(f"- Required gates before this step: {', '.join(f'`{gate}`' for gate in requires_gates)}")
        policy = step.get("source_policy")
        if policy:
            forbidden = ", ".join(policy.get("forbidden_sources", [])) or "none"
            lines.append(
                f"- Source policy: `{policy['mode']}` from `{policy['source_step']}.{policy['source_artifact']}`; "
                f"on missing: `{policy.get('on_missing', 'stop')}`; forbidden substitutions: {forbidden}"
            )
        remote_read = step.get("remote_read")
        if remote_read:
            if remote_read.get("type") == "skill":
                lines.append(
                    f"- Remote read route: use Skill `{remote_read.get('skill')}` "
                    f"via `{remote_read.get('command')}` only (read-only); "
                    f"on unavailable: `{remote_read.get('on_unavailable', 'stop')}`"
                )
            else:
                lines.append(
                    f"- Remote read route: use MCP profile `{remote_read.get('profile')}` only; "
                    f"on unavailable: `{remote_read.get('on_unavailable', 'stop')}`"
                )
        for profile in step.get("mcp_profiles", []):
            profile_path = step.get("mcp_profile_files", {}).get(profile, f".agents/mcp/profiles/{profile}.yaml")
            lines.append(f"- MCP profile file: `{profile_path}`")
        lines.append("")

    if not plan.get("steps"):
        lines.extend(["No executable steps were selected.", ""])
    return "\n".join(lines)


def prepare_workflow_bundle(
    plan: dict[str, Any],
    task_prompt: str,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    project_root = Path(plan["project_root"])
    if output_dir is None:
        task_id, workflow_dir = _new_workflow_directory(project_root, plan["workflow"])
    else:
        workflow_dir = output_dir.expanduser()
        if not workflow_dir.is_absolute():
            workflow_dir = project_root / workflow_dir
        workflow_dir = workflow_dir.resolve()
        if workflow_dir.exists() and not workflow_dir.is_dir():
            raise ConfigurationError(f"Workflow output is not a directory: {workflow_dir}")
        workflow_dir.mkdir(parents=True, exist_ok=True)
        task_id = workflow_dir.name

    materialized_plan = _materialize_task_paths(plan, task_id)
    materialized_plan.setdefault("contract_version", 2)
    materialized_plan["handoff_dir"] = _relative_to_project(workflow_dir, project_root)
    plan_path = workflow_dir / "plan.json"
    workflow_path = workflow_dir / "workflow.md"
    manifest_path = workflow_dir / "manifest.json"
    write_json(plan_path, materialized_plan)
    _write_text(workflow_path, build_workflow_markdown(materialized_plan, task_prompt, plan_path))
    manifest = {
        "task_id": task_id,
        "workflow": materialized_plan["workflow"],
        "project_root": str(project_root),
        "workflow_file": _relative_to_project(workflow_path, project_root),
        "plan_file": _relative_to_project(plan_path, project_root),
        "status": "generated",
    }
    write_json(manifest_path, manifest)
    return {
        **manifest,
        "workflow_path": str(workflow_path),
        "plan_path": str(plan_path),
        "manifest_path": str(manifest_path),
    }


def prepare_run(plan: dict[str, Any], task_prompt: str, sandbox: str) -> dict[str, Any]:
    project_root = Path(plan["project_root"])
    task_id, run_dir = _new_run_directory(project_root, plan["workflow"])
    plan_path = run_dir / "plan.json"
    instructions_path = run_dir / "instructions.md"
    result_path = run_dir / "codex-last-message.md"
    metadata_path = run_dir / "run.json"

    materialized_plan = _materialize_task_paths(plan, task_id)
    materialized_plan.setdefault("contract_version", 2)
    materialized_plan["run_dir"] = _relative_to_project(run_dir, project_root)
    execution_prompt = build_execution_prompt(materialized_plan, task_prompt, plan_path)
    write_json(plan_path, materialized_plan)
    _write_text(instructions_path, execution_prompt)
    metadata = {
        "task_id": task_id,
        "workflow": plan["workflow"],
        "project_root": str(project_root),
        "plan": _relative_to_project(plan_path, project_root),
        "instructions": _relative_to_project(instructions_path, project_root),
        "result": _relative_to_project(result_path, project_root),
        "sandbox": sandbox,
        "status": "prepared",
    }
    write_json(metadata_path, metadata)
    metadata["run_dir"] = _relative_to_project(run_dir, project_root)
    metadata["plan_path"] = str(plan_path)
    metadata["instructions_path"] = str(instructions_path)
    metadata["result_path"] = str(result_path)
    metadata["metadata_path"] = str(metadata_path)
    metadata["prompt"] = execution_prompt
    return metadata


def execute_codex(run: dict[str, Any], *, skip_git_repo_check: bool = False) -> int:
    project_root = Path(run["project_root"])
    result_path = Path(run["result_path"])
    codex = shutil.which("codex")
    if codex is None:
        raise ConfigurationError(
            "Codex CLI was not found on PATH; install it or run with the generated plan manually"
        )

    command = [
        codex,
        "exec",
        "-C",
        str(project_root),
        "-s",
        run["sandbox"],
        "-o",
        str(result_path),
        run["prompt"],
    ]
    if skip_git_repo_check:
        command.insert(2, "--skip-git-repo-check")

    print(
        f"Starting Codex for workflow '{run['workflow']}' "
        f"(run files: {run['run_dir']})",
        flush=True,
    )
    completed = subprocess.run(command, cwd=project_root, check=False, stdin=subprocess.DEVNULL)
    metadata_path = Path(run["metadata_path"])
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata.update({
        "status": "succeeded" if completed.returncode == 0 else "failed",
        "exit_code": completed.returncode,
    })
    write_json(metadata_path, metadata)
    return completed.returncode
