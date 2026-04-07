#!/usr/bin/env python3
"""
Check MCP provider availability for enterprise tool support.

Reads tool-bindings.json to determine which MCP servers are required,
then checks if they are registered in the Claude Code / OpenCode config.
Outputs installation guidance when servers are missing.

Detects availability and guides setup, does NOT write any configuration files.

Usage:
    python check_mcp_providers.py tool-bindings.json
    python check_mcp_providers.py tool-bindings.json --feature 3

Exit codes:
    0 — all required MCP servers are registered
    1 — one or more required MCP servers are not registered
"""

import argparse
import json
import os
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Config file discovery
# ---------------------------------------------------------------------------

def find_claude_config() -> tuple[Path | None, str]:
    """
    Locate Claude Code config file.

    Returns:
        (path, label) — path may be None if not found
    """
    home = Path.home()

    # Claude Code stores mcpServers in ~/.claude.json (top-level key)
    candidate = home / ".claude.json"
    if candidate.exists():
        return candidate, "~/.claude.json"

    # Fallback: ~/.claude/settings.json (some versions)
    candidate2 = home / ".claude" / "settings.json"
    if candidate2.exists():
        return candidate2, "~/.claude/settings.json"

    return None, "~/.claude.json (not found)"


def find_opencode_config() -> tuple[Path | None, str]:
    """
    Locate OpenCode config file (checks workspace-local and global locations).

    Returns:
        (path, label)
    """
    # Workspace-local (checked from CWD)
    local = Path(".vscode") / "settings.json"
    if local.exists():
        return local, ".vscode/settings.json"

    # Global OpenCode config
    home = Path.home()
    global_cfg = home / ".opencode" / "config.json"
    if global_cfg.exists():
        return global_cfg, "~/.opencode/config.json"

    return None, ".vscode/settings.json (not found)"


# ---------------------------------------------------------------------------
# MCP server registry readers
# ---------------------------------------------------------------------------

def read_registered_servers(config_path: Path) -> set[str]:
    """
    Read registered MCP server names from a config file.

    Supports:
    - ~/.claude.json        → top-level "mcpServers" key
    - ~/.claude/settings.json → "mcpServers" key
    - .vscode/settings.json → "opencode.mcpServers" key

    Returns:
        Set of registered server names (empty if file unreadable)
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return set()

    registered = set()

    # Claude Code format
    if "mcpServers" in data:
        registered |= set(data["mcpServers"].keys())

    # OpenCode format: opencode.mcpServers
    if "opencode.mcpServers" in data:
        registered |= set(data["opencode.mcpServers"].keys())

    return registered


# ---------------------------------------------------------------------------
# Bindings reader
# ---------------------------------------------------------------------------

def load_bindings(path: str) -> dict:
    """Load and parse tool-bindings.json."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_required_servers(bindings: dict) -> list[dict]:
    """
    Extract required MCP server declarations from tool-bindings.json.

    Returns list of dicts with keys: name, command, args, (optional) env.
    """
    servers = []
    for name, cfg in bindings.get("mcp_servers", {}).items():
        servers.append({
            "name": name,
            "command": cfg.get("command", ""),
            "args": cfg.get("args", []),
            "env": cfg.get("env", {}),
            "availability_probe": cfg.get("availability_probe"),
        })
    return servers


# ---------------------------------------------------------------------------
# Check logic
# ---------------------------------------------------------------------------

def check_providers(
    bindings_path: str,
) -> tuple[list[dict], list[dict], str]:
    """
    Check which required MCP servers are registered.

    Returns:
        (registered_servers, missing_servers, config_label)
    """
    bindings = load_bindings(bindings_path)
    required = get_required_servers(bindings)

    if not required:
        return [], [], "(no servers declared)"

    # Try Claude Code config first, then OpenCode
    claude_path, claude_label = find_claude_config()
    registered = set()
    config_label = claude_label

    if claude_path:
        registered = read_registered_servers(claude_path)

    # Also check OpenCode if Claude config didn't have entries
    if not registered:
        oc_path, oc_label = find_opencode_config()
        if oc_path:
            oc_registered = read_registered_servers(oc_path)
            if oc_registered:
                registered = oc_registered
                config_label = oc_label

    ok = []
    missing = []
    for srv in required:
        if srv["name"] in registered:
            ok.append(srv)
        else:
            missing.append(srv)

    return ok, missing, config_label


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def format_install_guidance(missing: list[dict]) -> str:
    """Format installation instructions for missing MCP servers."""
    lines = [
        "MCP Provider: NOT CONFIGURED",
        "",
        "The following MCP servers declared in tool-bindings.json are not registered:",
        "",
    ]
    for srv in missing:
        lines.append(f"  ✗ {srv['name']}")

    lines += [
        "",
        "To enable enterprise tool support, add the following to your",
        "Claude Code MCP settings:",
        "",
        "For Claude Code (~/.claude.json):",
        "  Open ~/.claude.json → mcpServers section → add:",
        "  {",
    ]
    for srv in missing:
        lines.append(f'    "{srv["name"]}": {{')
        lines.append(f'      "command": "{srv["command"]}",')
        args_json = json.dumps(srv["args"])
        lines.append(f'      "args": {args_json}')
        lines.append("    },")
    lines += [
        "  }",
        "",
        "  Or run:",
    ]
    for srv in missing:
        args_str = " ".join(srv["args"])
        lines.append(
            f'    claude mcp add {srv["name"]} -- {srv["command"]} {args_str}'
        )

    lines += [
        "",
        "For OpenCode:",
        "  Add to .vscode/settings.json under \"opencode.mcpServers\"",
        "",
        "After adding, restart your Claude Code / OpenCode session to activate.",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Check MCP provider availability for enterprise tool support"
    )
    parser.add_argument("bindings", help="Path to tool-bindings.json")
    parser.add_argument(
        "--feature", type=int, default=None,
        help="(reserved) Only check for this specific feature ID"
    )
    args = parser.parse_args()

    try:
        ok, missing, config_label = check_providers(args.bindings)
    except FileNotFoundError as e:
        print(f"ERROR: Cannot read {e.filename}: file not found", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Cannot parse {args.bindings}: {e}", file=sys.stderr)
        sys.exit(1)

    if not ok and not missing:
        print("No MCP servers declared in tool-bindings.json — check skipped.")
        sys.exit(0)

    if not missing:
        print("MCP Provider: AVAILABLE")
        for srv in ok:
            print(f"  ✓ {srv['name']:<20} — registered in {config_label}")
        sys.exit(0)

    if ok:
        print("MCP Provider: PARTIALLY CONFIGURED")
        for srv in ok:
            print(f"  ✓ {srv['name']:<20} — registered in {config_label}")
        for srv in missing:
            print(f"  ✗ {srv['name']:<20} — NOT registered")
        print()

    print(format_install_guidance(missing))
    sys.exit(1)


if __name__ == "__main__":
    main()
