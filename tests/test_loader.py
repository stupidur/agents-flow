from pathlib import Path
import tempfile
import unittest

from agentflow.cli import build_parser, parse_flags
from agentflow.bootstrap import bootstrap_project
from agentflow.loader import AgentFlow, ConfigurationError, condition_matches, find_project_file, safe_child


ROOT = Path(__file__).resolve().parents[1]


class LoaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.flow = AgentFlow(ROOT)

    def test_finds_project_entry_from_nested_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            nested = project / "src" / "feature"
            nested.mkdir(parents=True)
            (project / ".agents").mkdir()
            entry = project / ".agents" / "project.yaml"
            entry.write_text("project: {id: nested, domain: unknown}\n", encoding="utf-8")
            self.assertEqual(find_project_file(nested), entry.resolve())

    def test_plan_loads_only_unconditional_steps(self) -> None:
        plan = self.flow.plan("shopify-development", ROOT, {"source_design": "existing"})
        self.assertEqual(
            [step["id"] for step in plan["steps"]],
            ["inspect_theme", "implement_theme"],
        )
        self.assertNotIn("browser-preview", {profile for step in plan["steps"] for profile in step["mcp_profiles"]})

    def test_skill_required_capabilities_cannot_be_dropped_by_step(self) -> None:
        plan = self.flow.plan("product-spec", ROOT, {"existing_behavior_required": True})
        inspect_step = next(step for step in plan["steps"] if step["id"] == "inspect_existing_behavior")
        self.assertEqual(inspect_step["capabilities"], ["project_read", "requirement_analysis"])

    def test_remote_java_inspection_stays_read_only(self) -> None:
        plan = self.flow.plan("java-feature", ROOT, {"repository_is_remote": True})
        remote_step = plan["steps"][0]
        self.assertEqual(remote_step["id"], "inspect_remote_context")
        self.assertEqual(remote_step["capabilities"], ["code_read", "github_read"])

    def test_code_review_uses_two_project_local_reviewers_in_parallel(self) -> None:
        plan = self.flow.plan("code-review", ROOT)
        reviewers = plan["steps"][:2]
        self.assertEqual(
            [step["agent"] for step in reviewers],
            ["minimax_code_reviewer", "ds_code_reviewer"],
        )
        self.assertTrue(all(step["parallel_group"] == "independent_reviews" for step in reviewers))
        self.assertTrue(all(step["capabilities"] == ["code_read"] for step in reviewers))

    def test_figma_workflow_requires_blocking_inputs(self) -> None:
        with self.assertRaisesRegex(ConfigurationError, "source_design"):
            self.flow.plan("shopify-development", ROOT)
        with self.assertRaisesRegex(ConfigurationError, "figma_desktop_url"):
            self.flow.plan("shopify-development", ROOT, {"source_design": "figma"})
        with self.assertRaisesRegex(ConfigurationError, "supplemental_details_confirmed"):
            self.flow.plan(
                "shopify-development",
                ROOT,
                {
                    "source_design": "figma",
                    "figma_desktop_url": "https://figma.example/desktop",
                    "figma_mobile_url": "https://figma.example/mobile",
                    "supplemental_details_confirmed": False,
                },
            )

    def test_figma_skill_loads_from_local_vendored_library(self) -> None:
        plan = self.flow.plan(
            "shopify-development",
            ROOT,
            {
                "source_design": "figma",
                "figma_desktop_url": "https://figma.example/desktop",
                "figma_mobile_url": "https://figma.example/mobile",
                "supplemental_details_confirmed": True,
            },
        )
        figma_step = next(step for step in plan["steps"] if step["id"] == "inspect_figma")
        source = figma_step["skill_sources"][0]
        self.assertEqual(source["source"], "local")
        self.assertEqual(source["dependency_source"], "local")
        self.assertEqual(source["bucket"], "LIBRARY")
        self.assertTrue(source["source_path"].endswith("skills/shopify/figma-to-shopify/SKILL.md"))
        self.assertEqual(source["path"], ".agents/skills/figma-to-shopify/SKILL.md")
        self.assertEqual(len(source["references"]), 3)
        self.assertEqual(len(source["rules"]), 4)

    def test_shopify_development_loads_docs_only_when_requested(self) -> None:
        plan = self.flow.plan(
            "shopify-development",
            ROOT,
            {
                "source_design": "existing",
                "shopify_docs_required": True,
            },
        )
        docs = next(step for step in plan["steps"] if step["id"] == "inspect_shopify_platform")
        self.assertEqual(docs["skills"], ["shopify/shopify-dev"])
        self.assertEqual(docs["mcp_profiles"], ["shopify-dev-mcp"])

    def test_shopify_implementation_exposes_required_rules(self) -> None:
        plan = self.flow.plan(
            "shopify-development",
            ROOT,
            {"source_design": "existing"},
        )
        implementation = next(step for step in plan["steps"] if step["id"] == "implement_theme")
        self.assertTrue(any(path.endswith("rules/shopify/new-section-rules.md") for path in implementation["rules"]))
        self.assertTrue(any(path.endswith("rules/shopify/modify-section-rules.md") for path in implementation["rules"]))
        self.assertTrue(any(path.endswith("rules/common/git-push-restriction-rules.md") for path in implementation["rules"]))

    def test_shopify_project_onboarding_writes_agents_without_approval(self) -> None:
        plan = self.flow.plan("shopify-project-onboarding", ROOT)
        self.assertEqual(
            [step["id"] for step in plan["steps"]],
            ["discover_shopify_theme", "author_shopify_agents_context"],
        )
        author = plan["steps"][1]
        self.assertIn("shopify/initialize-shopify-project", author["skills"])
        self.assertEqual(plan["steps"][0]["mcp_profiles"], [])
        self.assertEqual(author["mcp_profiles"], [])
        self.assertEqual(plan["steps"][0]["capabilities"], ["document_write", "project_read"])
        self.assertEqual(plan["steps"][0]["outputs"][0]["transport"], "file")
        self.assertTrue(plan["steps"][0]["outputs"][0]["path"].endswith("/shopify-project-map.json"))
        self.assertFalse(author["approval_required"])
        self.assertFalse(plan["output"]["requires_human_approval"])
        self.assertEqual(plan["output"]["artifacts"]["project_memory"], ".agents/memory/**")
        self.assertEqual(plan["output"]["artifacts"]["project_gitignore"], ".gitignore")

    def test_basecamp_task_chains_product_spec_and_shopify_development(self) -> None:
        plan = self.flow.plan(
            "basecamp-task",
            ROOT,
            {
                "basecamp_task_url": "https://3.basecamp.com/example",
                "source_design": "existing",
            },
        )
        self.assertEqual(plan["workflow_chain"], ["product-spec", "shopify-development"])
        self.assertEqual(plan["contract_version"], 2)
        self.assertEqual(plan["executor_skills"], ["shared/workflow-execution"])
        self.assertEqual(plan["inputs"]["basecamp_task_url"], "https://3.basecamp.com/example")
        self.assertIn("product-spec.inspect_basecamp_context", [step["id"] for step in plan["steps"]])
        self.assertIn("shopify-development.implement_theme", [step["id"] for step in plan["steps"]])
        basecamp = next(step for step in plan["steps"] if step["id"] == "product-spec.inspect_basecamp_context")
        self.assertEqual(basecamp["outputs"][0]["id"], "basecamp_context")
        self.assertTrue(basecamp["outputs"][0]["path"].endswith("basecamp-context.json"))
        extract = next(step for step in plan["steps"] if step["id"] == "product-spec.extract")
        self.assertEqual(extract["inputs_from"][0]["step"], "product-spec.inspect_basecamp_context")
        verify = next(step for step in plan["steps"] if step["id"] == "product-spec.verify_basecamp_source")
        self.assertEqual(verify["gates"][0]["id"], "product-spec.basecamp_source_consistency")
        acceptance = next(step for step in plan["steps"] if step["id"] == "product-spec.acceptance_criteria")
        self.assertEqual(acceptance["requires_gates"], ["product-spec.basecamp_source_consistency"])
        specification_check = next(step for step in plan["steps"] if step["id"] == "product-spec.verify_specification_source")
        self.assertEqual(
            specification_check["gates"][0]["id"],
            "product-spec.specification_source_consistency",
        )
        implement = next(step for step in plan["steps"] if step["id"] == "shopify-development.implement_theme")
        self.assertIn(
            {"step": "product-spec.acceptance_criteria", "artifact": "specification", "required": True},
            implement["inputs_from"],
        )
        self.assertIn(
            {"step": "product-spec.verify_specification_source", "artifact": "specification_verification", "required": True},
            implement["inputs_from"],
        )
        self.assertIn("product-spec.specification_source_consistency", implement["requires_gates"])

    def test_basecamp_task_requires_task_url(self) -> None:
        with self.assertRaisesRegex(ConfigurationError, "basecamp_task_url"):
            self.flow.plan("basecamp-task", ROOT, {"source_design": "existing"})

    def test_product_spec_without_basecamp_does_not_require_basecamp_gate(self) -> None:
        plan = self.flow.plan("product-spec", ROOT, {"source_design": "existing"})
        acceptance = next(step for step in plan["steps"] if step["id"] == "acceptance_criteria")
        self.assertEqual(acceptance["inputs_from"], [{"step": "extract", "artifact": "requirements_evidence", "required": True}])
        self.assertEqual(acceptance["requires_gates"], [])

    def test_code_review_aggregates_both_reviewer_results(self) -> None:
        plan = self.flow.plan("code-review", ROOT)
        aggregate = plan["steps"][-1]
        self.assertEqual(aggregate["id"], "aggregate_findings")
        self.assertEqual(
            {(item["step"], item["artifact"]) for item in aggregate["inputs_from"]},
            {("minimax_review", "minimax_findings"), ("deepseek_review", "deepseek_findings")},
        )

    def test_java_context_precedes_implementation(self) -> None:
        plan = self.flow.plan("java-feature", ROOT, {"repository_is_remote": True})
        self.assertEqual(
            [step["id"] for step in plan["steps"]],
            ["inspect_remote_context", "implement", "test"],
        )
        self.assertEqual(plan["steps"][1]["inputs_from"][0]["artifact"], "remote_context")

    def test_project_onboarding_generates_agents_without_approval(self) -> None:
        plan = self.flow.plan("project-onboarding", ROOT)
        self.assertEqual([step["id"] for step in plan["steps"]], ["discover_project", "author_agents_context"])
        author = plan["steps"][1]
        self.assertEqual(plan["steps"][0]["mcp_profiles"], [])
        self.assertEqual(author["mcp_profiles"], [])
        self.assertEqual(plan["steps"][0]["outputs"][0]["transport"], "file")
        self.assertTrue(plan["steps"][0]["outputs"][0]["path"].endswith("/project-map.json"))
        self.assertFalse(author["approval_required"])
        self.assertFalse(plan["output"]["requires_human_approval"])
        self.assertEqual(plan["output"]["artifacts"]["project_memory"], ".agents/memory/**")

    def test_register_shopify_project_creates_lightweight_entry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "Example Store"
            project.mkdir()
            result = self.flow.register_project(project, "shopify")
            entry = project / ".agents" / "project.yaml"
            self.assertEqual(Path(result["project_file"]), entry.resolve())
            self.assertEqual(result["project_id"], "example-store")
            loaded, loaded_root = self.flow.load_project(project)
            self.assertEqual(loaded["project"]["domain"], "shopify")
            self.assertIn("shopify-development", loaded["allowed_workflows"])
            self.assertIn(".agents/memory/shopify.md", loaded["context"]["include"])
            self.assertIn(".agents/memory/global.md", loaded["context"]["include"])
            self.assertEqual(loaded_root, project.resolve())

    def test_bootstrap_materializes_shared_layer_and_thin_client_adapters(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "portable-store"
            project.mkdir()
            self.flow.register_project(project, "shopify")
            result = bootstrap_project(self.flow, project, [])

            self.assertEqual(result["conflicts"], [])
            self.assertIn(str((project / ".agents/memory/shopify.md").resolve()), result["memory_files"])
            self.assertTrue((project / ".agents/memory/README.md").is_file())
            self.assertTrue((project / ".agents/memory/shopify.md").is_file())
            self.assertTrue((project / ".agents/skills/ego-browser/SKILL.md").is_file())
            self.assertTrue((project / ".agents/skills/codex-computer-use/SKILL.md").is_file())
            self.assertTrue((project / ".agents/skills/workflow-execution/SKILL.md").is_file())
            self.assertTrue((project / ".agents/agents/shopify-developer.yaml").is_file())
            self.assertTrue((project / ".agents/mcp/manifest.json").is_file())
            manifest = __import__("json").loads((project / ".agents/mcp/manifest.json").read_text())
            browser_adapter = manifest["native_or_skill_adapters"]["browser-preview"]
            self.assertIn("Computer Use plugin first in ChatGPT/Codex", browser_adapter)
            self.assertIn("recorded unavailability or failure", browser_adapter)
            self.assertTrue((project / ".codex/config.toml").is_file())
            shopify_agent = (project / ".codex/agents/shopify-developer.toml").read_text()
            self.assertIn('model = "gpt-5.6-luna"', shopify_agent)
            self.assertIn('model_reasoning_effort = "high"', shopify_agent)
            self.assertTrue((project / ".claude/agents/shopify-developer.md").is_file())
            self.assertTrue((project / ".claude/skills/ego-browser/SKILL.md").is_file())
            self.assertTrue((project / ".mcp.json").is_file())
            self.assertTrue((project / "opencode.json").is_file())
            self.assertTrue((project / ".omp/config.yml").is_file())
            codex_config = (project / ".codex/config.toml").read_text()
            self.assertNotIn("[model_providers.", codex_config)
            self.assertNotIn("config_file =", codex_config)
            self.assertIn("[agents]", codex_config)
            self.assertIn("enabled = true", codex_config)
            self.assertIn("FIGMA_API_KEY=", (project / ".env.example").read_text())
            mcp = __import__("json").loads((project / ".mcp.json").read_text())["mcpServers"]
            self.assertEqual(mcp["figma-desktop-mcp"]["url"], "http://127.0.0.1:3845/mcp")
            self.assertEqual(
                mcp["figma-developer-mcp"]["env"]["FIGMA_API_KEY"],
                "${FIGMA_API_KEY}",
            )

    def test_bootstrap_can_target_only_opencode(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            self.flow.register_project(project, "java")
            result = bootstrap_project(self.flow, project, ["opencode"])

            self.assertEqual(result["clients"], ["opencode"])
            self.assertTrue((project / "opencode.json").is_file())
            self.assertFalse((project / ".codex").exists())
            self.assertFalse((project / ".claude").exists())

    def test_register_preserves_existing_project_entry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            self.flow.register_project(project, "default", "first")
            with self.assertRaisesRegex(ConfigurationError, "already registered"):
                self.flow.register_project(project, "shopify", "second")

    def test_registered_project_context_selects_type_specific_memory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            for project_type, memory_name in (("default", "global"), ("java", "java"), ("shopify", "shopify")):
                project = Path(directory) / project_type
                project.mkdir()
                self.flow.register_project(project, project_type)
                config, _ = self.flow.load_project(project)
                includes = config["context"]["include"]
                self.assertIn(f".agents/memory/{memory_name}.md", includes)
                self.assertIn(".agents/memory/workflows.md", includes)

    def test_register_rejects_agent_system_root(self) -> None:
        with self.assertRaisesRegex(ConfigurationError, "must not be registered"):
            self.flow.register_project(ROOT, "shopify")

    def test_product_spec_conditionally_loads_basecamp_and_figma(self) -> None:
        plan = self.flow.plan(
            "product-spec",
            ROOT,
            {"requirements_source": "basecamp", "source_design": "figma"},
        )
        steps = {step["id"]: step for step in plan["steps"]}
        self.assertEqual(
            steps["inspect_basecamp_context"]["skills"],
            ["shared/basecamp-requirements-readonly"],
        )
        self.assertEqual(steps["inspect_basecamp_context"]["mcp_profiles"], [])
        self.assertEqual(
            steps["inspect_basecamp_context"]["remote_read"],
            {
                "type": "skill",
                "skill": "shared/basecamp-requirements-readonly",
                "command": "basecamp",
                "on_unavailable": "skip_dependents",
            },
        )
        self.assertEqual(
            steps["extract"]["source_policy"]["on_missing"],
            "skip_dependents",
        )
        self.assertEqual(
            steps["verify_basecamp_source"]["gates"][0]["on_failure"],
            "skip_dependents",
        )
        self.assertEqual(steps["inspect_design_context"]["mcp_profiles"], ["figma-readonly"])

    def test_shopify_skills_are_directly_discoverable(self) -> None:
        for skill_name in [
            "figma-to-shopify",
            "initialize-shopify-project",
            "shopify-dev",
            "theme-investigation",
            "theme-implementation",
        ]:
            self.assertTrue((ROOT / "skills" / "shopify" / skill_name / "SKILL.md").is_file())

    def test_vibe_content_is_vendored_under_local_namespaces(self) -> None:
        project = {
            "project": {"id": "agent-system", "domain": "agent-system"},
            "allowed_workflows": [],
            "skill_namespaces": {"allow": ["daily-common", "shared"], "deny": []},
        }
        meeting = self.flow._load_skill("daily-common/meeting-minutes", project)
        coding = self.flow._load_skill("shared/coding-standards", project)
        self.assertEqual(meeting["source"], "local")
        self.assertEqual(meeting["dependency_source"], "local")
        self.assertEqual(len(meeting["references"]), 4)
        self.assertEqual(len(meeting["scripts"]), 1)
        self.assertEqual(coding["source"], "local")

    def test_plan_enables_conditional_step_and_mcp(self) -> None:
        plan = self.flow.plan(
            "shopify-development",
            ROOT,
            {"source_design": "existing", "visual_validation_required": True, "repository_is_remote": True},
        )
        visual = plan["steps"][-1]
        self.assertEqual(visual["id"], "visual_validation")
        self.assertIn("shared/codex-computer-use", visual["skills"])
        self.assertEqual(visual["mcp_profiles"], ["project-files-workspace-write", "browser-preview"])

        remote = next(step for step in plan["steps"] if step["id"] == "inspect_repository_context")
        self.assertEqual(remote["mcp_profiles"], [])
        self.assertEqual(
            remote["remote_read"],
            {"type": "skill", "skill": "shared/github-context-readonly", "command": "gh"},
        )

    def test_workflow_handoff_routes_gpt_ui_through_computer_use_first(self) -> None:
        plan = self.flow.plan(
            "shopify-development",
            ROOT,
            {"source_design": "existing", "visual_validation_required": True},
        )
        from agentflow.runtime import build_execution_prompt

        prompt = build_execution_prompt(plan, "Verify the local storefront", Path("plan.json"))
        self.assertIn("installed Computer Use plugin first", prompt)
        self.assertIn("falling back to the built-in Browser, Chrome control, or `ego-browser`", prompt)
        self.assertNotIn("`node_repl` + `@oai/sky`", prompt)

    def test_java_remote_context_uses_explicit_mcp_route(self) -> None:
        plan = self.flow.plan("java-feature", ROOT, {"repository_is_remote": True})
        remote = next(step for step in plan["steps"] if step["id"] == "inspect_remote_context")
        self.assertEqual(remote["remote_read"], {"type": "mcp", "profile": "github-readonly"})

    def test_disallowed_workflow_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / ".agents").mkdir()
            (project / ".agents" / "project.yaml").write_text(
                "project: {id: x, domain: java}\nallowed_workflows: []\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(ConfigurationError, "not allowed"):
                self.flow.plan("java-feature", project)

    def test_path_escape_is_rejected(self) -> None:
        with self.assertRaisesRegex(ConfigurationError, "escapes"):
            safe_child(ROOT, "../secret")

    def test_conditions_require_exact_values(self) -> None:
        self.assertTrue(condition_matches({"enabled": True}, {"enabled": True}))
        self.assertFalse(condition_matches({"enabled": True}, {"enabled": False}))

    def test_cli_flags_use_yaml_types(self) -> None:
        self.assertEqual(parse_flags(["enabled=true", "count=2"]), {"enabled": True, "count": 2})

    def test_register_and_bootstrap_default_to_current_directory(self) -> None:
        register = build_parser().parse_args(["register", "--type", "shopify"])
        bootstrap = build_parser().parse_args(["bootstrap"])
        self.assertEqual(register.project, Path.cwd())
        self.assertEqual(bootstrap.project, Path.cwd())

    def test_repository_configuration_validates(self) -> None:
        self.assertEqual(self.flow.validate(), [])

    def test_validation_checks_conditional_steps(self) -> None:
        project = {
            "project": {"id": "restricted", "domain": "shopify"},
            "allowed_workflows": ["shopify-development"],
            "skill_namespaces": {"allow": ["shared", "shopify"], "deny": []},
            "mcp_profiles": {
                "default": ["project-files"],
                "optional": [
                    "project-files-workspace-write",
                    "figma-readonly",
                    "github-readonly",
                    "shopify-dev-mcp",
                ],
            },
        }
        with self.assertRaisesRegex(ConfigurationError, "browser-preview"):
            self.flow._build_plan("shopify-development", project, ROOT, {}, include_conditional=True)


if __name__ == "__main__":
    unittest.main()
