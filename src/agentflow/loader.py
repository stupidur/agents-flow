from __future__ import annotations

import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

import yaml


class ConfigurationError(ValueError):
    """Raised when an Agent Flow configuration is missing or unsafe."""


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ConfigurationError(f"Configuration not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ConfigurationError(f"Expected a mapping in {path}")
    return data


def find_project_file(start: Path) -> Path | None:
    current = start.expanduser().resolve()
    if current.is_file():
        current = current.parent
    for directory in (current, *current.parents):
        candidate = directory / ".agents" / "project.yaml"
        if candidate.is_file():
            if load_yaml(candidate).get("scope") == "global":
                continue
            return candidate
    return None


def safe_child(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    resolved_root = root.resolve()
    if candidate != resolved_root and resolved_root not in candidate.parents:
        raise ConfigurationError(f"Path escapes system root: {relative}")
    return candidate


def condition_matches(condition: Any, flags: dict[str, Any]) -> bool:
    if condition is None:
        return True
    if not isinstance(condition, dict):
        raise ConfigurationError("Step conditions must be key/value mappings")
    return all(flags.get(key) == expected for key, expected in condition.items())


def parse_skill(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ConfigurationError(f"Skill not found: {path}")
    content = path.read_text(encoding="utf-8")
    metadata: dict[str, Any] = {}
    if content.startswith("---\n"):
        end = content.find("\n---\n", 4)
        if end < 0:
            raise ConfigurationError(f"Unclosed front matter: {path}")
        parsed = yaml.safe_load(content[4:end])
        if parsed is not None and not isinstance(parsed, dict):
            raise ConfigurationError(f"Invalid front matter: {path}")
        metadata = parsed or {}
    return {
        "id": metadata.get("id"),
        "name": metadata.get("name"),
        "description": metadata.get("description"),
        "capabilities": metadata.get("capabilities", {}),
        "path": str(path),
    }


class AgentFlow:
    def __init__(self, system_root: Path, global_root: Path | None = None):
        self.system_root = system_root.expanduser().resolve()
        requested_global_root = (global_root or Path(os.environ.get("AGENTFLOW_GLOBAL_ROOT", Path.home() / ".agents"))).expanduser()
        self.global_root_is_symlink = requested_global_root.is_symlink()
        self.global_root = requested_global_root.resolve()

    def global_config(self) -> dict[str, Any] | None:
        path = self.global_root / "project.yaml"
        if not path.is_file():
            return None
        config = load_yaml(path)
        if config.get("scope") != "global":
            raise ConfigurationError(f"Global registration must declare scope: global: {path}")
        return config

    def _resolve_source_root(self, configured_root: str) -> Path:
        source_root = Path(configured_root).expanduser()
        if not source_root.is_absolute():
            source_root = self.system_root / source_root
        return source_root.resolve()

    def load_project(self, project_path: Path) -> tuple[dict[str, Any], Path]:
        resolved_project = project_path.expanduser().resolve()
        if resolved_project == self.system_root:
            project_file = self.system_root / "projects" / "agent-system.yaml"
            return load_yaml(project_file), self.system_root
        project_file = find_project_file(resolved_project)
        if project_file is None:
            global_config = self.global_config()
            if global_config is not None:
                return global_config, resolved_project
            project_file = self.system_root / "projects" / "default.yaml"
            project_root = project_path.expanduser().resolve()
        else:
            project_root = project_file.parent.parent
        return load_yaml(project_file), project_root

    def register_project(
        self,
        project_path: Path,
        project_type: str,
        project_id: str | None = None,
        *,
        force: bool = False,
    ) -> dict[str, Any]:
        project_root = project_path.expanduser().resolve()
        if not project_root.is_dir():
            raise ConfigurationError(f"Project directory not found: {project_root}")
        if project_root == self.system_root:
            raise ConfigurationError("The Agent System uses projects/agent-system.yaml and must not be registered")

        templates = {
            "default": "default.yaml",
            "java": "java-project.example.yaml",
            "shopify": "shopify-project.example.yaml",
        }
        template_name = templates.get(project_type)
        if template_name is None:
            raise ConfigurationError(f"Unknown project type: {project_type}")

        agents_dir = project_root / ".agents"
        destination = agents_dir / "project.yaml"
        existed = destination.exists()
        if agents_dir.is_symlink() or destination.is_symlink():
            raise ConfigurationError("Refusing to register through a symlinked .agents path")
        if existed and not force:
            raise ConfigurationError(f"Project is already registered: {destination}")

        config = load_yaml(self.system_root / "projects" / template_name)
        raw_id = project_id or project_root.name
        normalized_id = re.sub(r"[^a-z0-9-]+", "-", raw_id.lower()).strip("-")
        if not normalized_id:
            raise ConfigurationError("Project id must contain a letter or number")
        config.setdefault("project", {})["id"] = normalized_id

        agents_dir.mkdir(parents=True, exist_ok=True)
        serialized = yaml.safe_dump(config, sort_keys=False, allow_unicode=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=agents_dir,
            prefix="project-",
            suffix=".yaml.tmp",
            delete=False,
        ) as handle:
            handle.write(serialized)
            temporary = Path(handle.name)
        temporary.replace(destination)
        return {
            "project_root": str(project_root),
            "project_file": str(destination),
            "project_id": normalized_id,
            "project_type": project_type,
            "replaced": existed,
        }

    def register_global(
        self,
        project_type: str,
        project_id: str | None = None,
        *,
        force: bool = False,
    ) -> dict[str, Any]:
        if self.global_root_is_symlink:
            raise ConfigurationError("Refusing to register through a symlinked global directory")
        if self.global_root == self.system_root:
            raise ConfigurationError("The global layer must not overwrite the Agent System source directory")
        templates = {
            "default": "default.yaml",
            "java": "java-project.example.yaml",
            "shopify": "shopify-project.example.yaml",
        }
        if project_type not in templates:
            raise ConfigurationError(f"Unknown project type: {project_type}")
        destination = self.global_root / "project.yaml"
        if self.global_root.exists() and not self.global_root.is_dir():
            raise ConfigurationError(f"Global directory is not a directory: {self.global_root}")
        if destination.is_symlink():
            raise ConfigurationError("Refusing to register through a symlinked global project.yaml")
        if destination.exists() and not force:
            raise ConfigurationError(f"Global layer is already registered: {destination}")
        if destination.exists() and not destination.is_file():
            raise ConfigurationError(f"Global registration is not a file: {destination}")
        config = load_yaml(self.system_root / "projects" / templates[project_type])
        normalized_id = re.sub(r"[^a-z0-9-]+", "-", (project_id or f"global-{project_type}").lower()).strip("-")
        if not normalized_id:
            raise ConfigurationError("Project id must contain a letter or number")
        config["scope"] = "global"
        config["system_root"] = str(self.system_root)
        config["project"]["id"] = normalized_id
        config["context"]["include"] = ["AGENTS.md", "project.yaml", "rules/**", "memory/**"]
        existed = destination.exists()
        self.global_root.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=self.global_root, delete=False) as handle:
            yaml.safe_dump(config, handle, sort_keys=False, allow_unicode=True)
            temporary = Path(handle.name)
        temporary.replace(destination)
        return {
            "scope": "global",
            "global_root": str(self.global_root),
            "project_file": str(destination),
            "project_id": normalized_id,
            "project_type": project_type,
            "replaced": existed,
        }

    def _load_workflow(self, workflow_id: str, project: dict[str, Any]) -> dict[str, Any]:
        allowed = project.get("allowed_workflows", [])
        if workflow_id not in allowed:
            raise ConfigurationError(f"Workflow '{workflow_id}' is not allowed by this project")
        workflow = load_yaml(safe_child(self.system_root / "workflows", f"{workflow_id}.yaml"))
        declared_id = workflow.get("workflow", {}).get("id")
        if declared_id != workflow_id:
            raise ConfigurationError(f"Workflow id mismatch in {workflow_id}.yaml")
        return workflow

    def _load_agent(self, agent_id: str) -> dict[str, Any]:
        agent = load_yaml(safe_child(self.system_root / "agents", f"{agent_id}/agent.yaml"))
        if agent.get("agent", {}).get("id") != agent_id:
            raise ConfigurationError(f"Agent id mismatch for '{agent_id}'")
        return agent

    def _load_skill(self, skill_id: str, project: dict[str, Any]) -> dict[str, Any]:
        if not re.fullmatch(r"[a-z0-9-]+/[a-z0-9-]+", skill_id):
            raise ConfigurationError(f"Invalid skill id: {skill_id}")
        namespace = skill_id.split("/", 1)[0]
        namespaces = project.get("skill_namespaces", {})
        if namespace not in namespaces.get("allow", []) or namespace in namespaces.get("deny", []):
            raise ConfigurationError(f"Skill namespace '{namespace}' is not allowed")
        registry = load_yaml(self.system_root / "skills" / "registry.yaml")
        entry = registry.get("skills", {}).get(skill_id)
        if entry is None:
            source_id = "local"
            source_root = self.system_root
            skill_path = safe_child(source_root, f"skills/{skill_id}/SKILL.md")
            references: list[str] = []
            rules: list[str] = []
            scripts: list[str] = []
            dependency_source_id = source_id
            bucket = "DAILY"
        else:
            if not isinstance(entry, dict):
                raise ConfigurationError(f"Invalid registry entry for '{skill_id}'")
            source_id = str(entry.get("source", ""))
            source = registry.get("sources", {}).get(source_id)
            if not isinstance(source, dict) or not source.get("root"):
                raise ConfigurationError(f"Unknown skill source '{source_id}'")
            source_root = self._resolve_source_root(str(source["root"]))
            skill_path = safe_child(source_root, str(entry.get("path", "")))
            dependency_source_id = str(entry.get("dependencies_source", source_id))
            dependency_source = registry.get("sources", {}).get(dependency_source_id)
            if not isinstance(dependency_source, dict) or not dependency_source.get("root"):
                raise ConfigurationError(f"Unknown dependency source '{dependency_source_id}'")
            dependency_root = self._resolve_source_root(str(dependency_source["root"]))
            references = [str(safe_child(dependency_root, path)) for path in entry.get("references", [])]
            rules = [str(safe_child(dependency_root, path)) for path in entry.get("rules", [])]
            scripts = [str(safe_child(dependency_root, path)) for path in entry.get("scripts", [])]
            bucket = str(entry.get("bucket", "LIBRARY"))
            for dependency in [*references, *rules, *scripts]:
                if not Path(dependency).is_file():
                    raise ConfigurationError(f"Skill dependency not found: {dependency}")
        skill = parse_skill(skill_path)
        declared_id = skill["id"] or skill["name"]
        if declared_id not in {skill_id, skill_id.split("/", 1)[1]}:
            raise ConfigurationError(f"Skill id mismatch for '{skill_id}'")
        skill.update(
            {
                "id": skill_id,
                "source": source_id,
                "dependency_source": dependency_source_id,
                "bucket": bucket,
                "references": references,
                "rules": rules,
                "scripts": scripts,
            }
        )
        return skill

    def _load_mcp(self, profile_id: str, project: dict[str, Any]) -> dict[str, Any]:
        profiles = project.get("mcp_profiles", {})
        allowed = set(profiles.get("default", [])) | set(profiles.get("optional", []))
        if profile_id not in allowed:
            raise ConfigurationError(f"MCP profile '{profile_id}' is not allowed by this project")
        profile = load_yaml(safe_child(self.system_root / "mcp" / "profiles", f"{profile_id}.yaml"))
        if profile.get("profile", {}).get("id") != profile_id:
            raise ConfigurationError(f"MCP profile id mismatch for '{profile_id}'")
        return profile

    @staticmethod
    def _step_agent_id(step: dict[str, Any], domain: str) -> str:
        if "agent" in step:
            return str(step["agent"])
        agent_id = step.get("agent_by_domain", {}).get(domain)
        if not agent_id:
            raise ConfigurationError(f"No agent configured for domain '{domain}' in step '{step.get('id')}'")
        return str(agent_id)

    @staticmethod
    def _invalid_required_inputs(requirements: Any, flags: dict[str, Any]) -> list[str]:
        if isinstance(requirements, list):
            return [key for key in requirements if key not in flags]
        if isinstance(requirements, dict):
            return [
                key
                for key, expected in requirements.items()
                if key not in flags
                or (expected == "nonempty" and not flags[key])
                or (expected != "nonempty" and flags[key] != expected)
            ]
        raise ConfigurationError("required_inputs must be a list or mapping")

    @staticmethod
    def _step_outputs(step_id: str, outputs: Any) -> list[dict[str, Any]]:
        if outputs is None:
            return []
        if not isinstance(outputs, list):
            raise ConfigurationError(f"outputs in step '{step_id}' must be a list")
        normalized: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in outputs:
            if not isinstance(item, dict) or not item.get("id"):
                raise ConfigurationError(f"Each output in step '{step_id}' must declare an id")
            artifact_id = str(item["id"])
            if artifact_id in seen:
                raise ConfigurationError(f"Duplicate output '{artifact_id}' in step '{step_id}'")
            seen.add(artifact_id)
            transport = str(item.get("transport", "file" if item.get("path") else "agent_result"))
            if transport not in {"file", "agent_result"}:
                raise ConfigurationError(
                    f"Output '{artifact_id}' in step '{step_id}' has unsupported transport '{transport}'"
                )
            path = item.get("path")
            if transport == "file" and not isinstance(path, str):
                raise ConfigurationError(f"File output '{artifact_id}' in step '{step_id}' requires a path")
            normalized.append({
                "id": artifact_id,
                "transport": transport,
                "path": path,
                "format": str(item.get("format", "json")),
                "schema": item.get("schema"),
                "required": bool(item.get("required", True)),
                "description": item.get("description"),
            })
        return normalized

    @staticmethod
    def _step_inputs(step_id: str, inputs: Any, flags: dict[str, Any]) -> list[dict[str, Any]]:
        if inputs is None:
            return []
        if not isinstance(inputs, list):
            raise ConfigurationError(f"inputs_from in step '{step_id}' must be a list")
        normalized: list[dict[str, Any]] = []
        for item in inputs:
            if not isinstance(item, dict) or not item.get("step") or not item.get("artifact"):
                raise ConfigurationError(f"Each input in step '{step_id}' must declare step and artifact")
            if not condition_matches(item.get("when"), flags):
                continue
            normalized.append({
                "step": str(item["step"]),
                "artifact": str(item["artifact"]),
                "required": bool(item.get("required", True)),
            })
        return normalized

    @staticmethod
    def _step_gates(step_id: str, gates: Any) -> list[dict[str, Any]]:
        if gates is None:
            return []
        if not isinstance(gates, list):
            raise ConfigurationError(f"gates in step '{step_id}' must be a list")
        normalized: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in gates:
            if not isinstance(item, dict) or not item.get("id"):
                raise ConfigurationError(f"Each gate in step '{step_id}' must declare an id")
            gate_id = str(item["id"])
            if gate_id in seen:
                raise ConfigurationError(f"Duplicate gate '{gate_id}' in step '{step_id}'")
            seen.add(gate_id)
            on_failure = str(item.get("on_failure", "stop"))
            if on_failure not in {"stop", "skip_dependents"}:
                raise ConfigurationError(
                    f"Gate '{gate_id}' in step '{step_id}' must use on_failure stop or skip_dependents"
                )
            normalized.append({
                "id": gate_id,
                "type": str(item.get("type", "validation")),
                "required": bool(item.get("required", True)),
                "checks": list(item.get("checks", [])),
                "on_failure": on_failure,
            })
        return normalized

    @staticmethod
    def _required_gates(step_id: str, gates: Any, flags: dict[str, Any]) -> list[str]:
        if gates is None:
            return []
        if not isinstance(gates, list):
            raise ConfigurationError(f"requires_gates in step '{step_id}' must be a list")
        required: list[str] = []
        for item in gates:
            if isinstance(item, str):
                gate_id = item
                condition = None
            elif isinstance(item, dict) and item.get("id"):
                gate_id = str(item["id"])
                condition = item.get("when")
            else:
                raise ConfigurationError(f"Each required gate in step '{step_id}' must declare an id")
            if condition_matches(condition, flags):
                required.append(gate_id)
        return required

    @staticmethod
    def _source_policy(step_id: str, policy: Any, flags: dict[str, Any]) -> dict[str, Any] | None:
        if policy is None:
            return None
        if not isinstance(policy, dict):
            raise ConfigurationError(f"source_policy in step '{step_id}' must be a mapping")
        if not condition_matches(policy.get("when"), flags):
            return None
        normalized = dict(policy)
        normalized.pop("when", None)
        if normalized.get("mode") not in {"artifact-only", "declared-inputs-only"}:
            raise ConfigurationError(
                f"source_policy in step '{step_id}' must use artifact-only or declared-inputs-only"
            )
        if not normalized.get("source_step") or not normalized.get("source_artifact"):
            raise ConfigurationError(f"source_policy in step '{step_id}' must declare source_step and source_artifact")
        normalized.setdefault("on_missing", "stop")
        if normalized["on_missing"] not in {"stop", "skip_dependents"}:
            raise ConfigurationError(
                f"source_policy in step '{step_id}' must use on_missing stop or skip_dependents"
            )
        return normalized

    @staticmethod
    def _validate_step_contracts(steps: list[dict[str, Any]]) -> None:
        step_ids = {str(step["id"]) for step in steps}
        artifacts = {
            str(step["id"]): {str(output["id"]) for output in step.get("outputs", [])}
            for step in steps
        }
        gates = {
            str(gate["id"])
            for step in steps
            for gate in step.get("gates", [])
        }
        for step in steps:
            step_id = str(step["id"])
            for ref in step.get("inputs_from", []):
                source_step = str(ref["step"])
                if source_step not in step_ids:
                    raise ConfigurationError(f"Step '{step_id}' references unknown input step '{source_step}'")
                if str(ref["artifact"]) not in artifacts[source_step]:
                    raise ConfigurationError(
                        f"Step '{step_id}' references unknown artifact '{ref['artifact']}' from '{source_step}'"
                    )
            for gate_id in step.get("requires_gates", []):
                if str(gate_id) not in gates:
                    raise ConfigurationError(f"Step '{step_id}' requires unknown gate '{gate_id}'")
            policy = step.get("source_policy")
            if policy:
                source_step = str(policy["source_step"])
                if source_step not in step_ids:
                    raise ConfigurationError(f"Step '{step_id}' source policy references unknown step '{source_step}'")
                if str(policy["source_artifact"]) not in artifacts[source_step]:
                    raise ConfigurationError(
                        f"Step '{step_id}' source policy references unknown artifact "
                        f"'{policy['source_artifact']}' from '{source_step}'"
                    )

    def _build_plan(
        self,
        workflow_id: str,
        project: dict[str, Any],
        project_root: Path,
        flags: dict[str, Any],
        include_conditional: bool = False,
    ) -> dict[str, Any]:
        workflow = self._load_workflow(workflow_id, project)
        workflow_metadata = workflow.get("workflow", {})
        if not include_conditional:
            required_inputs = workflow_metadata.get("required_inputs", {})
            invalid_inputs = self._invalid_required_inputs(required_inputs, flags)
            if invalid_inputs:
                raise ConfigurationError(f"Workflow '{workflow_id}' requires valid inputs: {invalid_inputs}")

        executor_skills = [
            self._load_skill(skill_id, project)
            for skill_id in workflow_metadata.get("executor_skills", [])
        ]
        executor_skill_sources = [
            {
                "id": skill["id"],
                "source": skill.get("source", "local"),
                "dependency_source": skill.get("dependency_source", skill.get("source", "local")),
                "bucket": skill.get("bucket", "DAILY"),
                "path": f".agents/skills/{str(skill['id']).split('/', 1)[-1]}/SKILL.md",
                "source_path": skill["path"],
                "references": skill.get("references", []),
                "rules": skill.get("rules", []),
                "scripts": skill.get("scripts", []),
            }
            for skill in executor_skills
        ]

        chain = workflow_metadata.get("chain", [])
        if chain:
            if not isinstance(chain, list) or not all(isinstance(item, (str, dict)) for item in chain):
                raise ConfigurationError(f"Workflow chain for '{workflow_id}' must contain workflow ids or mappings")
            chained_steps: list[dict[str, Any]] = []
            chain_ids: list[str] = []
            for item in chain:
                if isinstance(item, str):
                    child_id = item
                    child_flags = dict(flags)
                else:
                    if "workflow" not in item:
                        raise ConfigurationError(f"Workflow chain entry in '{workflow_id}' is missing workflow")
                    child_id = str(item["workflow"])
                    overrides = item.get("set", {})
                    if not isinstance(overrides, dict):
                        raise ConfigurationError(f"Workflow chain overrides for '{child_id}' must be a mapping")
                    child_flags = {**flags, **overrides}
                child_plan = self._build_plan(
                    child_id,
                    project,
                    project_root,
                    child_flags,
                    include_conditional=include_conditional,
                )
                chain_ids.append(child_id)
                for child_step in child_plan["steps"]:
                    chained_step = dict(child_step)
                    chained_step["id"] = f"{child_id}.{child_step['id']}"
                    chained_step["source_workflow"] = child_id
                    chained_step["inputs_from"] = [
                        {
                            **ref,
                            "step": ref["step"] if "." in str(ref["step"]) else f"{child_id}.{ref['step']}",
                        }
                        for ref in child_step.get("inputs_from", [])
                    ]
                    chained_step["requires_gates"] = [
                        gate_id if "." in str(gate_id) else f"{child_id}.{gate_id}"
                        for gate_id in child_step.get("requires_gates", [])
                    ]
                    chained_step["gates"] = [
                        {**gate, "id": f"{child_id}.{gate['id']}"}
                        for gate in child_step.get("gates", [])
                    ]
                    if chained_step.get("source_policy"):
                        policy = dict(chained_step["source_policy"])
                        if "." not in str(policy.get("source_step", "")):
                            policy["source_step"] = f"{child_id}.{policy['source_step']}"
                        chained_step["source_policy"] = policy
                    chained_steps.append(chained_step)
                if isinstance(item, dict) and (item.get("inputs_from") or item.get("requires_gates")):
                    target_step = str(item.get("target_step", ""))
                    if not target_step:
                        raise ConfigurationError(
                            f"Workflow chain entry for '{child_id}' with handoff dependencies requires target_step"
                        )
                    target_id = f"{child_id}.{target_step}"
                    target = next((step for step in chained_steps if step["id"] == target_id), None)
                    if target is None:
                        raise ConfigurationError(
                            f"Workflow chain entry for '{child_id}' targets unknown step '{target_step}'"
                        )
                    for ref in item.get("inputs_from", []):
                        if not isinstance(ref, dict) or not ref.get("workflow") or not ref.get("step") or not ref.get("artifact"):
                            raise ConfigurationError(
                                f"Workflow chain input for '{child_id}' must declare workflow, step, and artifact"
                            )
                        target["inputs_from"].append({
                            "step": f"{ref['workflow']}.{ref['step']}",
                            "artifact": str(ref["artifact"]),
                            "required": bool(ref.get("required", True)),
                        })
                    for gate_ref in item.get("requires_gates", []):
                        if not isinstance(gate_ref, dict) or not gate_ref.get("workflow") or not gate_ref.get("gate"):
                            raise ConfigurationError(
                                f"Workflow chain gate for '{child_id}' must declare workflow and gate"
                            )
                        target["requires_gates"].append(f"{gate_ref['workflow']}.{gate_ref['gate']}")
            self._validate_step_contracts(chained_steps)
            return {
                "contract_version": 2,
                "project": project.get("project", {}),
                "project_root": str(project_root),
                "workflow": workflow_id,
                "inputs": flags,
                "workflow_chain": chain_ids,
                "executor_skills": [skill["id"] for skill in executor_skills],
                "executor_skill_sources": executor_skill_sources,
                "steps": chained_steps,
                "output": workflow.get("output", {}),
            }

        domain = str(project.get("project", {}).get("domain", "unknown"))
        workflow_capabilities = set(workflow_metadata.get("allowed_capabilities", []))
        planned_steps: list[dict[str, Any]] = []

        for step in workflow.get("steps", []):
            if not include_conditional and not condition_matches(step.get("when"), flags):
                continue
            if not include_conditional and step.get("required_inputs"):
                invalid_inputs = self._invalid_required_inputs(step["required_inputs"], flags)
                if invalid_inputs:
                    raise ConfigurationError(f"Step '{step.get('id')}' requires valid inputs: {invalid_inputs}")
            agent_id = self._step_agent_id(step, domain)
            agent = self._load_agent(agent_id)
            skills = [self._load_skill(skill_id, project) for skill_id in step.get("skills", [])]
            required = {cap for skill in skills for cap in skill.get("capabilities", {}).get("required", [])}
            requested = required | set(step.get("capabilities", []))
            agent_allowed = set(agent.get("agent", {}).get("allowed_capabilities", []))
            effective = requested & agent_allowed & workflow_capabilities
            denied = requested - effective
            if denied:
                raise ConfigurationError(f"Step '{step.get('id')}' requests disallowed capabilities: {sorted(denied)}")

            mcp_profiles = []
            for item in step.get("mcp", []):
                entry = {"profile": item} if isinstance(item, str) else item
                if not isinstance(entry, dict) or "profile" not in entry:
                    raise ConfigurationError(f"Invalid MCP entry in step '{step.get('id')}'")
                if include_conditional or condition_matches(entry.get("when"), flags):
                    mcp_profiles.append(self._load_mcp(str(entry["profile"]), project))

            remote_read = step.get("remote_read")
            remote_route: dict[str, Any] | None = None
            if remote_read is not None:
                if not isinstance(remote_read, dict):
                    raise ConfigurationError(f"remote_read in step '{step.get('id')}' must be a mapping")
                route_type = str(remote_read.get("type", ""))
                if route_type == "skill":
                    route_skill_id = str(remote_read.get("skill", ""))
                    if route_skill_id not in {skill["id"] for skill in skills}:
                        raise ConfigurationError(
                            f"remote_read Skill '{route_skill_id}' must be listed in step '{step.get('id')}'"
                        )
                    route_command = str(remote_read.get("command", ""))
                    if not route_command:
                        raise ConfigurationError(
                            f"remote_read Skill route in step '{step.get('id')}' must declare a command"
                        )
                    remote_route = {
                        "type": "skill",
                        "skill": route_skill_id,
                        "command": route_command,
                    }
                elif route_type == "mcp":
                    route_profile_id = str(remote_read.get("profile", ""))
                    profile_ids = {profile["profile"]["id"] for profile in mcp_profiles}
                    if route_profile_id not in profile_ids:
                        raise ConfigurationError(
                            f"remote_read MCP profile '{route_profile_id}' is not active in step '{step.get('id')}'"
                        )
                    remote_route = {
                        "type": "mcp",
                        "profile": route_profile_id,
                    }
                else:
                    raise ConfigurationError(
                        f"remote_read type in step '{step.get('id')}' must be 'skill' or 'mcp'"
                    )
                if "on_unavailable" in remote_read:
                    on_unavailable = str(remote_read["on_unavailable"])
                    if on_unavailable not in {"stop", "skip_dependents"}:
                        raise ConfigurationError(
                            f"remote_read in step '{step.get('id')}' must use on_unavailable stop or skip_dependents"
                        )
                    remote_route["on_unavailable"] = on_unavailable

            skill_sources = [
                {
                    "id": skill["id"],
                    "source": skill.get("source", "local"),
                    "dependency_source": skill.get("dependency_source", skill.get("source", "local")),
                    "bucket": skill.get("bucket", "DAILY"),
                    "path": f".agents/skills/{str(skill['id']).split('/', 1)[-1]}/SKILL.md",
                    "source_path": skill["path"],
                    "references": skill.get("references", []),
                    "rules": skill.get("rules", []),
                    "scripts": skill.get("scripts", []),
                }
                for skill in skills
            ]
            rules = sorted({rule for source in skill_sources for rule in source["rules"]})

            planned_steps.append({
                "id": step.get("id"),
                "agent": agent_id,
                "model_tier": step.get("model_tier", agent.get("agent", {}).get("model_tier", "medium")),
                "parallel_group": step.get("parallel_group"),
                "skills": [skill["id"] for skill in skills],
                "skill_sources": skill_sources,
                "rules": rules,
                "outputs": self._step_outputs(str(step.get("id")), step.get("outputs")),
                "inputs_from": self._step_inputs(str(step.get("id")), step.get("inputs_from"), flags),
                "gates": self._step_gates(str(step.get("id")), step.get("gates")),
                "requires_gates": self._required_gates(str(step.get("id")), step.get("requires_gates"), flags),
                "source_policy": self._source_policy(str(step.get("id")), step.get("source_policy"), flags),
                "remote_read": remote_route,
                "capabilities": sorted(effective),
                "mcp_profiles": [profile["profile"]["id"] for profile in mcp_profiles],
                "approval_required": bool(step.get("approval", {}).get("required", False)),
            })

        self._validate_step_contracts(planned_steps)

        return {
            "contract_version": 2,
            "project": project.get("project", {}),
            "project_root": str(project_root),
            "workflow": workflow_id,
            "inputs": flags,
            "workflow_chain": [],
            "executor_skills": [skill["id"] for skill in executor_skills],
            "executor_skill_sources": executor_skill_sources,
            "steps": planned_steps,
            "output": workflow.get("output", {}),
        }

    def plan(self, workflow_id: str, project_path: Path, flags: dict[str, Any] | None = None) -> dict[str, Any]:
        project, project_root = self.load_project(project_path)
        if project_root == self.global_root:
            raise ConfigurationError("The global layer is not a task project; select a repository with --project")
        plan = self._build_plan(workflow_id, project, project_root, flags or {})
        if self.global_config() is None:
            return plan
        global_rules = [str(path) for path in sorted((self.global_root / "rules").rglob("*.md")) if path.is_file()]
        plan["global_context"] = {
            "root": str(self.global_root),
            "agents_md": str(self.global_root / "AGENTS.md"),
            "rules": global_rules,
            "memory_index": str(self.global_root / "memory/README.md"),
            "agent_files": {
                step["agent"]: str(self.global_root / "agents" / f"{step['agent']}.yaml")
                for step in plan["steps"]
            },
            "access": "read-only",
        }

        def resolve_rule(value: str) -> str:
            path = Path(value)
            try:
                relative = path.relative_to(self.system_root / "rules")
            except ValueError:
                return value
            local = project_root / ".agents" / "rules" / relative
            shared = self.global_root / "rules" / relative
            return str(local) if local.is_file() else str(shared) if shared.is_file() else value

        sources = list(plan.get("executor_skill_sources", []))
        for step in plan["steps"]:
            sources.extend(step["skill_sources"])
            local_agent = project_root / ".agents/agents" / f"{step['agent']}.yaml"
            step["agent_file"] = str(local_agent) if local_agent.is_file() else plan["global_context"]["agent_files"][step["agent"]]
            step["rules"] = sorted({*(resolve_rule(rule) for rule in step["rules"]), *global_rules})
            step["mcp_profile_files"] = {
                profile: str(project_root / ".agents/mcp/profiles" / f"{profile}.yaml")
                if (project_root / ".agents/mcp/profiles" / f"{profile}.yaml").is_file()
                else str(self.global_root / "mcp/profiles" / f"{profile}.yaml")
                for profile in step["mcp_profiles"]
            }
        for source in sources:
            source["rules"] = [resolve_rule(rule) for rule in source["rules"]]
            local = project_root / source["path"]
            shared = self.global_root / "skills" / source["id"].split("/", 1)[1] / "SKILL.md"
            if not local.is_file() and shared.is_file():
                original_dir = Path(source["source_path"]).parent
                source["execution_path"] = str(shared)
                source["path"] = str(shared)
                source["source_path"] = str(shared)
                for field in ("references", "scripts"):
                    rebased = []
                    for value in source[field]:
                        try:
                            rebased.append(str(shared.parent / Path(value).relative_to(original_dir)))
                        except ValueError:
                            rebased.append(value)
                    source[field] = rebased
        return plan

    def validate(self) -> list[str]:
        errors: list[str] = []
        project_files = sorted((self.system_root / "projects").glob("*.yaml"))
        for project_file in project_files:
            try:
                project = load_yaml(project_file)
                project_path = self.system_root
                for workflow_id in project.get("allowed_workflows", []):
                    self._build_plan(workflow_id, project, project_path, {}, include_conditional=True)
            except ConfigurationError as exc:
                errors.append(f"{project_file}: {exc}")
        return errors

    @staticmethod
    def doctor() -> dict[str, Any]:
        return {
            "python": shutil.which("python3") is not None,
            "dmux": shutil.which("dmux") is not None,
            "tmux": shutil.which("tmux") is not None,
            "agent_system_root": os.environ.get("AGENT_SYSTEM_ROOT"),
        }
