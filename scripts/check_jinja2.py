#!/usr/bin/env python3
"""
Check Jinja2 availability for enterprise MCP template rendering.

Jinja2 is required when tool-bindings.json exists — it powers the SKILL.md
template engine that resolves enterprise MCP tool names.

Detects availability and guides setup, does NOT install any packages.

Usage:
    python check_jinja2.py
    python check_jinja2.py --quiet

Exit codes:
    0 — jinja2 is installed and importable
    1 — jinja2 is not available
"""

import argparse
import sys


def check_jinja2() -> dict:
    """
    Check if Jinja2 is importable.

    Returns:
        Dict with keys: available (bool), version (str|None), detail (str).
    """
    try:
        import jinja2
        return {
            "available": True,
            "version": jinja2.__version__,
            "detail": f"jinja2 {jinja2.__version__}",
        }
    except ImportError:
        return {
            "available": False,
            "version": None,
            "detail": "jinja2 module not found",
        }


def main():
    parser = argparse.ArgumentParser(
        description="Check Jinja2 availability for enterprise MCP template rendering"
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress output on success (exit code only)"
    )
    args = parser.parse_args()

    result = check_jinja2()

    if result["available"]:
        if not args.quiet:
            print(f"JINJA2: AVAILABLE ({result['detail']})")
        sys.exit(0)
    else:
        print("JINJA2: NOT INSTALLED")
        print(f"  {result['detail']}")
        print()
        print("To resolve:")
        print("  pip install jinja2")
        print()
        print("Jinja2 is required to render enterprise MCP tool bindings")
        print("(SKILL.md.template → .long-task-bindings/).")
        print()
        print("After installing, restart the session so templates are rendered.")
        sys.exit(1)


if __name__ == "__main__":
    main()
