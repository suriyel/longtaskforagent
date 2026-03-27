"""Tests for scripts/apply_tool_bindings.py — Jinja2 template rendering."""
import json
import sys
import tempfile
from pathlib import Path

import pytest

# Allow importing from scripts/
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from apply_tool_bindings import (
    DEFAULT_CONTEXT,
    build_context,
    find_plugin_root,
    find_templates,
    render_template,
)


# ---------------------------------------------------------------------------
# build_context
# ---------------------------------------------------------------------------

class TestBuildContext:
    def test_defaults_when_no_bindings(self):
        ctx = build_context(None)
        assert ctx["cap_ui_platform"] == "Chrome DevTools MCP"
        assert ctx["cap_ui_navigate"] == "navigate_page"
        assert ctx["cap_ui_eval"] == "evaluate_script"
        assert ctx["cap_ui_console"] == "list_console_messages"
        assert ctx["enterprise_mcp"] is False
        assert ctx["has_mcp_ui"] is False
        assert ctx["has_mcp_ci"] is False

    def test_enterprise_ui_tool_names(self):
        bindings = {
            "mcp_servers": {"acme_browser": {}},
            "capability_bindings": {
                "ui_tools": {
                    "type": "mcp",
                    "tool_mapping": {
                        "navigate_page": "acme_browser__navigate",
                        "click": "acme_browser__click",
                        "evaluate_script": "acme_browser__eval",
                        "list_console_messages": "acme_browser__console",
                    },
                }
            },
        }
        ctx = build_context(bindings)
        assert ctx["cap_ui_navigate"] == "acme_browser__navigate"
        assert ctx["cap_ui_click"] == "acme_browser__click"
        assert ctx["cap_ui_eval"] == "acme_browser__eval"
        assert ctx["cap_ui_console"] == "acme_browser__console"
        assert ctx["enterprise_mcp"] is True
        assert ctx["has_mcp_ui"] is True

    def test_enterprise_ci_capabilities(self):
        bindings = {
            "mcp_servers": {"ci_server": {}},
            "capability_bindings": {
                "test": {
                    "type": "mcp",
                    "tool": "ci_server__run_tests",
                },
                "coverage": {
                    "type": "mcp",
                    "tool": "ci_server__coverage",
                },
                "mutation": {
                    "type": "mcp",
                    "tool": "ci_server__mutation",
                },
            },
        }
        ctx = build_context(bindings)
        assert ctx["cap_ci_test"] == "ci_server__run_tests"
        assert ctx["cap_ci_coverage"] == "ci_server__coverage"
        assert ctx["cap_ci_mutation"] == "ci_server__mutation"
        assert ctx["has_mcp_ci"] is True
        assert ctx["enterprise_mcp"] is True

    def test_ci_only_without_ui(self):
        """CI MCP without UI tools."""
        bindings = {
            "mcp_servers": {},
            "capability_bindings": {
                "coverage": {
                    "type": "mcp",
                    "tool": "ci__cov",
                },
            },
        }
        ctx = build_context(bindings)
        assert ctx["has_mcp_ci"] is True
        assert ctx["has_mcp_ui"] is False
        assert ctx["cap_ci_coverage"] == "ci__cov"
        # UI keeps defaults
        assert ctx["cap_ui_navigate"] == "navigate_page"

    def test_unmapped_ui_tools_keep_defaults(self):
        bindings = {
            "mcp_servers": {},
            "capability_bindings": {
                "ui_tools": {
                    "type": "mcp",
                    "tool_mapping": {
                        "navigate_page": "acme__nav",
                    },
                }
            },
        }
        ctx = build_context(bindings)
        assert ctx["cap_ui_navigate"] == "acme__nav"
        assert ctx["cap_ui_hover"] == "hover"  # default kept
        assert ctx["cap_ui_drag"] == "drag"    # default kept

    def test_platform_name_derived_from_server(self):
        bindings = {
            "mcp_servers": {"acme_browser": {}},
            "capability_bindings": {
                "ui_tools": {
                    "type": "mcp",
                    "tool_mapping": {"navigate_page": "acme_browser__navigate"},
                }
            },
        }
        ctx = build_context(bindings)
        assert "acme_browser" in ctx["cap_ui_platform"]

    def test_empty_bindings_returns_defaults(self):
        bindings = {"mcp_servers": {}, "capability_bindings": {}}
        ctx = build_context(bindings)
        assert ctx["enterprise_mcp"] is False
        assert ctx["has_mcp_ci"] is False
        assert ctx["has_mcp_ui"] is False

    def test_ci_capability_without_tool_ignored(self):
        """CI capability without 'tool' field is not recognized."""
        bindings = {
            "mcp_servers": {},
            "capability_bindings": {
                "coverage": {
                    "type": "mcp",
                    # No "tool" field
                },
            },
        }
        ctx = build_context(bindings)
        assert ctx["has_mcp_ci"] is False
        assert ctx["cap_ci_coverage"] == ""


# ---------------------------------------------------------------------------
# render_template (Jinja2)
# ---------------------------------------------------------------------------

class TestRenderTemplate:
    @pytest.fixture()
    def tmpdir(self, tmp_path):
        return tmp_path

    def _write_template(self, tmpdir, name, content):
        path = tmpdir / name
        path.write_text(content, encoding="utf-8")
        return path

    def test_default_context_replaces_ui_vars(self, tmpdir):
        tmpl = self._write_template(
            tmpdir, "test.md.template",
            "Use `{{ cap_ui_navigate }}` and `{{ cap_ui_eval }}`."
        )
        ctx = build_context(None)
        result = render_template(tmpl, ctx)
        assert "navigate_page" in result
        assert "evaluate_script" in result
        assert "{{ " not in result

    def test_enterprise_context_replaces_vars(self, tmpdir):
        tmpl = self._write_template(
            tmpdir, "test.md.template",
            "Use `{{ cap_ui_navigate }}` tool."
        )
        bindings = {
            "mcp_servers": {"acme": {}},
            "capability_bindings": {
                "ui_tools": {
                    "type": "mcp",
                    "tool_mapping": {"navigate_page": "acme__nav"},
                }
            },
        }
        ctx = build_context(bindings)
        result = render_template(tmpl, ctx)
        assert "acme__nav" in result
        assert "{{ " not in result

    def test_ci_section_hidden_without_bindings(self, tmpdir):
        tmpl = self._write_template(
            tmpdir, "test.md.template",
            "Before\n{% if has_mcp_ci %}\nMCP CI Section\n{% endif %}\nAfter"
        )
        ctx = build_context(None)
        result = render_template(tmpl, ctx)
        assert "MCP CI Section" not in result
        assert "Before" in result
        assert "After" in result

    def test_ci_section_shown_with_bindings(self, tmpdir):
        tmpl = self._write_template(
            tmpdir, "test.md.template",
            "Before\n{% if has_mcp_ci %}\nCoverage: `{{ cap_ci_coverage }}`\n{% endif %}\nAfter"
        )
        bindings = {
            "mcp_servers": {},
            "capability_bindings": {
                "coverage": {"type": "mcp", "tool": "ci__cov"},
            },
        }
        ctx = build_context(bindings)
        result = render_template(tmpl, ctx)
        assert "Coverage: `ci__cov`" in result

    def test_if_else_enterprise_mcp(self, tmpdir):
        tmpl = self._write_template(
            tmpdir, "test.md.template",
            "{% if enterprise_mcp %}\nEnterprise\n{% else %}\nDefault\n{% endif %}"
        )
        ctx_default = build_context(None)
        result_default = render_template(tmpl, ctx_default)
        assert "Default" in result_default
        assert "Enterprise" not in result_default

        bindings = {
            "mcp_servers": {"acme": {}},
            "capability_bindings": {
                "ui_tools": {"type": "mcp", "tool_mapping": {"click": "acme__click"}},
            },
        }
        ctx_enterprise = build_context(bindings)
        result_enterprise = render_template(tmpl, ctx_enterprise)
        assert "Enterprise" in result_enterprise
        assert "Default" not in result_enterprise

    def test_no_jinja_residue_after_render(self, tmpdir):
        tmpl = self._write_template(
            tmpdir, "test.md.template",
            "{{ cap_ui_platform }} {{ cap_ui_navigate }} {{ cap_ci_test }}"
            "{% if has_mcp_ci %}CI{% endif %}"
        )
        ctx = build_context(None)
        result = render_template(tmpl, ctx)
        assert "{{ " not in result
        assert "{% " not in result


# ---------------------------------------------------------------------------
# find_plugin_root / find_templates (smoke test)
# ---------------------------------------------------------------------------

class TestFindTemplates:
    def test_plugin_root_exists(self):
        root = find_plugin_root()
        assert root.exists()
        assert (root / "scripts").exists()

    def test_templates_found(self):
        root = find_plugin_root()
        templates = find_templates(root)
        assert len(templates) >= 5

    def test_template_output_paths_are_md_files(self):
        root = find_plugin_root()
        for tmpl_path, rel_out in find_templates(root):
            assert tmpl_path.suffix == ".template"
            assert rel_out.suffix == ".md"


# ---------------------------------------------------------------------------
# Integration: render actual project templates
# ---------------------------------------------------------------------------

class TestRenderActualTemplates:
    """Render all project templates with default and enterprise contexts."""

    def _get_templates(self):
        root = find_plugin_root()
        return find_templates(root)

    def _enterprise_bindings(self):
        bindings_path = find_plugin_root() / "docs" / "templates" / "tool-bindings-template.json"
        if bindings_path.exists():
            return json.loads(bindings_path.read_text(encoding="utf-8"))
        pytest.skip("tool-bindings-template.json not found")

    def test_all_templates_render_with_defaults(self):
        ctx = build_context(None)
        for tmpl_path, _ in self._get_templates():
            result = render_template(tmpl_path, ctx)
            assert "{{ " not in result, f"Jinja2 residue in {tmpl_path.name}"
            assert "{% " not in result, f"Jinja2 residue in {tmpl_path.name}"

    def test_all_templates_render_with_enterprise(self):
        bindings = self._enterprise_bindings()
        ctx = build_context(bindings)
        for tmpl_path, _ in self._get_templates():
            result = render_template(tmpl_path, ctx)
            assert "{{ " not in result, f"Jinja2 residue in {tmpl_path.name}"
            assert "{% " not in result, f"Jinja2 residue in {tmpl_path.name}"

    def test_quality_template_no_mcp_section_by_default(self):
        """Default quality SKILL.md should NOT have MCP Tool Commands section."""
        ctx = build_context(None)
        root = find_plugin_root()
        quality_tmpl = root / "skills" / "long-task-quality" / "SKILL.md.template"
        result = render_template(quality_tmpl, ctx)
        assert "MCP Tool Commands" not in result
        assert "get_tool_commands.py" not in result

    def test_quality_template_has_mcp_section_with_enterprise(self):
        """Enterprise quality SKILL.md should show MCP tool names."""
        bindings = self._enterprise_bindings()
        ctx = build_context(bindings)
        root = find_plugin_root()
        quality_tmpl = root / "skills" / "long-task-quality" / "SKILL.md.template"
        result = render_template(quality_tmpl, ctx)
        assert "MCP Tool Commands" in result
        assert "your_ci_server__coverage" in result
        assert "your_ci_server__mutation" in result

    # e2e-scenario-prompt.md.template was removed (MCP mapping logic simplified)
