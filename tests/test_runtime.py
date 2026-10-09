from pathlib import Path
import json
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from agentflow.runtime import (
    build_execution_prompt,
    default_sandbox,
    execute_codex,
    prepare_run,
    prepare_workflow_bundle,
)


class RuntimeTests(unittest.TestCase):
    def test_default_sandbox_matches_workflow_capabilities(self) -> None:
        self.assertEqual(default_sandbox({"steps": [{"capabilities": ["code_read"]}]}), "read-only")
        self.assertEqual(default_sandbox({"steps": [{"capabilities": ["code_write"]}]}), "workspace-write")
        self.assertEqual(default_sandbox({"steps": [{"capabilities": ["document_write"]}]}), "workspace-write")

    def test_prepare_run_persists_plan_and_execution_instructions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            plan = {
                "project": {"id": "demo", "domain": "java"},
                "project_root": str(project),
                "workflow": "java-feature",
                "steps": [
                    {
                        "id": "implement",
                        "agent": "java-developer",
                        "skills": ["java/feature-implementation"],
                        "mcp_profiles": ["project-files-workspace-write"],
                        "capabilities": ["code_read", "code_write"],
                        "approval_required": False,
                    }
                ],
                "output": {"schema": "implementation-result-v1"},
            }

            result = prepare_run(plan, "Implement the feature", "workspace-write")

            run_dir = project / result["run_dir"]
            plan_path = run_dir / "plan.json"
            instructions_path = run_dir / "instructions.md"
            metadata_path = run_dir / "run.json"
            self.assertTrue(plan_path.is_file())
            self.assertTrue(instructions_path.is_file())
            self.assertTrue(metadata_path.is_file())
            self.assertEqual(json.loads(plan_path.read_text())['workflow'], "java-feature")
            instructions = instructions_path.read_text()
            self.assertIn("java-feature", instructions)
            self.assertIn("Implement the feature", instructions)
            self.assertIn("project-files-workspace-write", instructions)

    def test_prepare_workflow_bundle_creates_manual_handoff_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            plan = {
                "project_root": str(project),
                "workflow": "java-feature",
                "inputs": {"repository_is_remote": True},
                "executor_skills": ["shared/workflow-execution"],
                "steps": [
                    {
                        "id": "implement",
                        "agent": "java-developer",
                        "skills": ["java/feature-implementation"],
                        "skill_sources": [{"id": "java/feature-implementation", "path": "/system/skill.md"}],
                        "rules": ["/system/rules/shopify/new-section-rules.md"],
                        "mcp_profiles": ["project-files-workspace-write"],
                        "capabilities": ["code_write"],
                        "approval_required": False,
                    }
                ],
            }

            result = prepare_workflow_bundle(plan, "Implement the feature")

            workflow_path = Path(result["workflow_path"])
            plan_path = Path(result["plan_path"])
            manifest_path = Path(result["manifest_path"])
            self.assertTrue(workflow_path.is_file())
            self.assertTrue(plan_path.is_file())
            self.assertTrue(manifest_path.is_file())
            workflow = workflow_path.read_text()
            self.assertIn("do not invoke `agentflow run`", workflow)
            self.assertIn("Implement the feature", workflow)
            self.assertIn("java-developer", workflow)
            self.assertIn("workflow-execution", workflow)
            self.assertIn(".agents/memory/README.md", workflow)
            self.assertIn("repository_is_remote", workflow)
            self.assertIn("multi-agent tool", workflow)
            self.assertIn("full step contract", workflow)
            self.assertIn("installed Computer Use plugin first", workflow)
            self.assertIn("fall back to `ego-browser`, then `playwright-cli`", workflow)
            self.assertIn(".agents/rules/shopify/new-section-rules.md", workflow)
            self.assertIn("Report the completed work", workflow)
            self.assertEqual(json.loads(manifest_path.read_text())["status"], "generated")

    def test_workflow_bundle_reports_single_remote_read_route(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            plan = {
                "project_root": str(project),
                "workflow": "basecamp-task",
                "steps": [
                    {
                        "id": "inspect_basecamp_context",
                        "agent": "requirement-analyst",
                        "skills": ["shared/basecamp-requirements-readonly"],
                        "skill_sources": [],
                        "rules": [],
                        "mcp_profiles": [],
                        "remote_read": {
                            "type": "skill",
                            "skill": "shared/basecamp-requirements-readonly",
                            "command": "basecamp",
                            "on_unavailable": "skip_dependents",
                        },
                        "capabilities": ["basecamp_read"],
                        "approval_required": False,
                    }
                ],
            }

            result = prepare_workflow_bundle(plan, "Inspect the Basecamp task")
            workflow = Path(result["workflow_path"]).read_text()
            self.assertIn("use Skill `shared/basecamp-requirements-readonly`", workflow)
            self.assertIn("via `basecamp` only", workflow)
            self.assertIn("on unavailable: `skip_dependents`", workflow)
            self.assertNotIn("primary MCP", workflow)
            self.assertNotIn("fallback Skill", workflow)

    def test_workflow_bundle_materializes_artifact_paths_and_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            plan = {
                "project_root": str(project),
                "workflow": "product-spec",
                "steps": [
                    {
                        "id": "inspect",
                        "agent": "requirement-analyst",
                        "skills": ["shared/requirement-extraction"],
                        "skill_sources": [{"id": "shared/requirement-extraction", "execution_path": ".agents/skills/requirement-extraction/SKILL.md"}],
                        "rules": [],
                        "mcp_profiles": [],
                        "outputs": [{"id": "context", "path": ".agentflow/workflows/<task-id>/context.json", "required": True}],
                        "inputs_from": [],
                        "gates": [],
                        "requires_gates": [],
                        "capabilities": ["requirement_analysis"],
                        "approval_required": False,
                    },
                ],
            }

            result = prepare_workflow_bundle(plan, "Inspect requirements")
            generated_plan = json.loads(Path(result["plan_path"]).read_text())
            self.assertEqual(generated_plan["contract_version"], 2)
            generated_output = generated_plan["steps"][0]["outputs"][0]["path"]
            self.assertNotIn("<task-id>", generated_output)
            self.assertTrue(generated_output.endswith("/context.json"))
            workflow = Path(result["workflow_path"]).read_text()
            self.assertIn("Outputs (must produce before completing step)", workflow)
            self.assertIn("materialized project path", workflow)

    def test_execution_prompt_requires_plan_before_changes(self) -> None:
        plan = {
            "project_root": "/tmp/project",
            "workflow": "code-review",
            "steps": [],
        }
        prompt = build_execution_prompt(plan, "Review the current diff", Path("/tmp/project/.agentflow/plan.json"))
        self.assertIn("Read the plan file before changing anything", prompt)
        self.assertIn("Review the current diff", prompt)

    @patch("agentflow.runtime.shutil.which", return_value="/usr/local/bin/codex")
    @patch("agentflow.runtime.subprocess.run")
    def test_execute_codex_closes_stdin_when_prompt_is_supplied(self, run_process, _which) -> None:
        run_process.return_value.returncode = 0
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            plan = {
                "project_root": str(project),
                "workflow": "code-review",
                "steps": [],
            }
            run = prepare_run(plan, "Review the diff", "read-only")

            self.assertEqual(execute_codex(run, skip_git_repo_check=True), 0)
            _, kwargs = run_process.call_args
            self.assertIs(kwargs["stdin"], subprocess.DEVNULL)
            command = run_process.call_args.args[0]
            self.assertIn("exec", command)
            self.assertIn("--skip-git-repo-check", command)


if __name__ == "__main__":
    unittest.main()
