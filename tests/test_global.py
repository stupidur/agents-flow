from contextlib import redirect_stdout, redirect_stderr
import io
import json
import os
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from agentflow.bootstrap import bootstrap_project
from agentflow.cli import build_parser, main
from agentflow.loader import AgentFlow, ConfigurationError, find_project_file, load_yaml
from agentflow.runtime import build_execution_prompt, prepare_workflow_bundle


ROOT = Path(__file__).resolve().parents[1]


class GlobalLayerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name).resolve()
        self.shared = self.home / ".agents"
        self.project = self.home / "store"
        self.project.mkdir()
        self.flow = AgentFlow(ROOT, self.shared)

    def install(self, clients: list[str] | None = None) -> dict:
        self.flow.register_global("shopify")
        return bootstrap_project(self.flow, self.project, clients or ["codex"], global_scope=True)

    def test_register_and_bootstrap_global_do_not_write_to_project_or_client_home(self) -> None:
        client_config = self.home / ".codex/config.toml"
        client_config.parent.mkdir()
        client_config.write_text("# Existing private client configuration\n")
        self.install(["codex", "claude"])
        config = load_yaml(self.shared / "project.yaml")
        self.assertEqual(config["scope"], "global")
        self.assertEqual(config["system_root"], str(ROOT))
        for relative in (
            "rules/common/browser-testing-rules.md",
            "skills/playwright-cli/SKILL.md",
            "agents/shopify-developer.yaml",
            "mcp/profiles/browser-preview.yaml",
            "memory/shopify.md",
            "AGENTS.md",
            "clients/.codex/config.toml",
            "clients/.codex/agents/shopify-developer.toml",
        ):
            self.assertTrue((self.shared / relative).is_file(), relative)
        self.assertFalse((self.shared / ".agents").exists())
        self.assertEqual(list(self.project.iterdir()), [])
        self.assertEqual(client_config.read_text(), "# Existing private client configuration\n")
        shim = (self.shared / "clients/.claude/skills/playwright-cli/SKILL.md").read_text()
        self.assertIn(str(self.shared / "skills/playwright-cli/SKILL.md"), shim)

    def test_global_registration_is_not_discovered_as_a_parent_project(self) -> None:
        self.flow.register_global("shopify")
        self.assertIsNone(find_project_file(self.project))
        config, root = self.flow.load_project(self.project)
        self.assertEqual(root, self.project)
        self.assertEqual(config["project"]["domain"], "shopify")
        with self.assertRaisesRegex(ConfigurationError, "not a task project"):
            self.flow.plan("shopify-development", self.shared, {"source_design": "existing"})

    def test_global_bootstrap_preserves_conflicts_and_is_idempotent(self) -> None:
        self.install()
        repeated = bootstrap_project(self.flow, self.project, ["codex"], global_scope=True)
        self.assertEqual(repeated["conflicts"], [])
        rule = self.shared / "rules/common/browser-testing-rules.md"
        rule.write_text("# User's global rule\n")
        result = bootstrap_project(self.flow, self.project, ["codex"], global_scope=True)
        self.assertIn(str(rule), result["conflicts"])
        self.assertEqual(rule.read_text(), "# User's global rule\n")
        with self.assertRaisesRegex(ConfigurationError, "already registered"):
            self.flow.register_global("java")

    def test_global_plan_inherits_rules_and_shared_paths_without_changing_project_root(self) -> None:
        self.install()
        custom_rule = self.shared / "rules/team-policy.md"
        custom_rule.write_text("# Preserve the team's constraints\n")
        plan = self.flow.plan("shopify-project-onboarding", self.project)
        self.assertEqual(plan["project_root"], str(self.project))
        self.assertEqual(plan["global_context"]["access"], "read-only")
        author = plan["steps"][1]
        self.assertIn(str(custom_rule), author["rules"])
        author_skill = next(source for source in author["skill_sources"] if source["id"] == "shared/agents-context-authoring")
        self.assertEqual(author_skill["execution_path"], str(self.shared / "skills/agents-context-authoring/SKILL.md"))
        bundle = prepare_workflow_bundle(plan, "Generate the project's AGENTS.md")
        markdown = Path(bundle["workflow_path"]).read_text()
        self.assertIn(str(custom_rule), markdown)
        self.assertIn(str(self.shared / "AGENTS.md"), markdown)
        self.assertIn("When creating or updating project AGENTS.md", markdown)
        self.assertIn(str(self.shared / "skills/workflow-execution/SKILL.md"), markdown)
        prompt = build_execution_prompt(plan, "Initialize project context", Path(bundle["plan_path"]))
        self.assertIn(str(custom_rule), prompt)
        self.assertIn("read-only task context", prompt)
        self.assertTrue(Path(bundle["workflow_path"]).is_relative_to(self.project))

    def test_project_registration_keeps_local_permissions_and_both_rule_layers(self) -> None:
        self.install()
        self.flow.register_project(self.project, "default")
        bootstrap_project(self.flow, self.project, ["codex"])
        with self.assertRaisesRegex(ConfigurationError, "not allowed"):
            self.flow.plan("shopify-development", self.project, {"source_design": "existing"})
        plan = self.flow.plan("project-onboarding", self.project)
        self.assertEqual(plan["project"]["domain"], "unknown")
        self.assertIn(str(self.shared / "rules/agent-system.md"), plan["steps"][1]["rules"])
        source = plan["steps"][1]["skill_sources"][0]
        self.assertNotIn("execution_path", source)

    def test_development_plan_uses_global_mcp_profiles_and_skill_dependencies(self) -> None:
        self.install()
        plan = self.flow.plan("shopify-development", self.project, {"source_design": "existing", "visual_validation_required": True})
        visual = plan["steps"][-1]
        self.assertEqual(visual["mcp_profile_files"]["browser-preview"], str(self.shared / "mcp/profiles/browser-preview.yaml"))
        self.assertIn("shared/playwright-cli", visual["skills"])
        bundle = prepare_workflow_bundle(plan, "Validate the theme")
        self.assertIn(str(self.shared / "mcp/profiles/browser-preview.yaml"), Path(bundle["workflow_path"]).read_text())

    def test_bootstrap_requires_global_registration_and_rejects_symlink_writes(self) -> None:
        with self.assertRaisesRegex(ConfigurationError, "register --global"):
            bootstrap_project(self.flow, self.project, ["codex"], global_scope=True)
        self.flow.register_global("shopify")
        outside = self.home / "outside"
        outside.mkdir()
        (self.shared / "rules").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ConfigurationError, "symlink"):
            bootstrap_project(self.flow, self.project, ["codex"], global_scope=True)
        self.assertEqual(list(outside.iterdir()), [])

    def test_global_registration_rejects_source_root_and_symlinked_directory(self) -> None:
        with self.assertRaisesRegex(ConfigurationError, "source directory"):
            AgentFlow(ROOT, ROOT).register_global("shopify")
        destination = self.home / "linked-global"
        destination.symlink_to(self.project, target_is_directory=True)
        with self.assertRaisesRegex(ConfigurationError, "symlinked global directory"):
            AgentFlow(ROOT, destination).register_global("shopify")
        self.assertEqual(list(self.project.iterdir()), [])

    def test_cli_global_mode_and_system_root_discovery(self) -> None:
        for command in (
            ["--system-root", str(ROOT), "register", "--type", "shopify", "--global", "--global-root", str(self.shared)],
            ["--global-root", str(self.shared), "bootstrap", "--global", "--client", "codex"],
            ["--global-root", str(self.shared), "plan", "shopify-project-onboarding", "--project", str(self.project)],
        ):
            with patch.dict(os.environ), redirect_stdout(io.StringIO()) as output:
                os.environ.pop("AGENT_SYSTEM_ROOT", None)
                self.assertEqual(main(command), 0)
                result = json.loads(output.getvalue())
        self.assertEqual(result["project_root"], str(self.project))

    def test_parser_defaults_to_current_project_and_rejects_mixed_scopes(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["register", "--type", "shopify"])
        self.assertEqual(args.project, Path.cwd())
        self.assertFalse(args.global_scope)
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            parser.parse_args(["bootstrap", "--global", "--project", str(self.project)])

    def test_shopify_initializer_reuses_global_rules_without_installing_local_copies(self) -> None:
        self.install()
        rule = self.shared / "rules/shopify/new-section-rules.md"
        rule.write_text("# A customized global section policy\n")
        script = ROOT / "skills/shopify/initialize-shopify-project/scripts/init_shopify_project.py"
        result = subprocess.run(
            [sys.executable, str(script), "--target", str(self.project), "--global-root", str(self.shared), "--json"],
            capture_output=True, text=True, check=True,
        )
        report = json.loads(result.stdout)
        inherited = [item["path"] for item in report["files"] if item["action"] == "inherited"]
        self.assertIn(str(rule), inherited)
        self.assertFalse((self.project / ".agents/rules").exists())
        self.assertFalse((self.project / ".codex").exists())
        self.assertTrue((self.project / ".gitignore").is_file())
        self.assertEqual(rule.read_text(), "# A customized global section policy\n")


if __name__ == "__main__":
    unittest.main()
