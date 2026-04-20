#!/usr/bin/env python3
"""Auto-loop script for long-task feature development using OpenCode.

Repeatedly calls `opencode run --yolo "go on"` until all active features pass,
max iterations are reached, or an error occurs.

Each invocation gets a fresh context (implicit /clear). Session logs are saved
to the --log-dir directory automatically.

AskUserQuestion detection: The OpenCode plugin writes a signal file
(.claude/ask-user-signal.json) when an interactive tool is called.
The loop detects this and pauses.

Interrupt handling:
    1st Ctrl+C — graceful: finish current iteration, then stop
    2nd Ctrl+C — forceful: kill child process immediately and exit

Usage:
    python scripts/auto_loop_opencode.py feature-list.json
    python scripts/auto_loop_opencode.py feature-list.json --max-iterations 30
    python scripts/auto_loop_opencode.py feature-list.json --cooldown 10
    python scripts/auto_loop_opencode.py feature-list.json --model anthropic/claude-sonnet-4-6
    python scripts/auto_loop_opencode.py feature-list.json --attach http://localhost:4096
    python scripts/auto_loop_opencode.py feature-list.json --log-dir logs
"""

import argparse
import json
import os
import re
import signal
import subprocess
import sys
import time


def _force_utf8_io() -> None:
    """Force stdout/stderr to UTF-8 so CJK text survives non-UTF-8 locales
    (Windows cp936, LANG=C). Python 3.7+."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


# Error patterns that indicate unrecoverable failures
ERROR_PATTERNS = [
    re.compile(r"context.window", re.IGNORECASE),
    re.compile(r"token.limit", re.IGNORECASE),
    re.compile(r"rate.limit", re.IGNORECASE),
    re.compile(r"exceeded.*max.*tokens", re.IGNORECASE),
    re.compile(r"overloaded", re.IGNORECASE),
]

# Global interrupt state
_interrupt_requested = False  # 1st Ctrl+C: graceful stop
_force_kill = False           # 2nd Ctrl+C: force kill
_active_proc: subprocess.Popen | None = None  # currently running child


def _signal_handler(signum, frame):
    """Handle Ctrl+C with two-level escalation."""
    global _interrupt_requested, _force_kill

    if not _interrupt_requested:
        # First Ctrl+C: request graceful stop
        _interrupt_requested = True
        print(
            "\n>>> Ctrl+C received — will stop after current iteration. "
            "Press Ctrl+C again to force kill. <<<",
            flush=True,
        )
    else:
        # Second Ctrl+C: force kill
        _force_kill = True
        print("\n>>> Force kill requested — terminating now. <<<", flush=True)
        if _active_proc and _active_proc.poll() is None:
            _active_proc.kill()
        sys.exit(130)


def load_feature_status(path: str) -> tuple[int, int, int]:
    """Load feature-list.json and return (total_active, passing, failing) counts."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    features = data.get("features", [])
    active = [f for f in features if not f.get("deprecated", False)]
    passing = sum(1 for f in active if f.get("status") == "passing")
    failing = len(active) - passing
    return len(active), passing, failing


def check_all_passing(path: str) -> bool:
    """Return True if all active features are passing."""
    try:
        total, passing, _ = load_feature_status(path)
        return total > 0 and passing == total
    except (json.JSONDecodeError, FileNotFoundError, KeyError):
        return False


def detect_error(output: str) -> str | None:
    """Check output for known error patterns. Return matched pattern or None."""
    for pattern in ERROR_PATTERNS:
        if pattern.search(output):
            return pattern.pattern
    return None


def detect_ask_user_signal(project_dir: str) -> dict | None:
    """Check for OpenCode ask-user signal file.

    The OpenCode plugin writes .claude/ask-user-signal.json when an
    interactive tool is called. Returns signal content or None.
    """
    signal_file = os.path.join(project_dir, ".claude", "ask-user-signal.json")
    if os.path.isfile(signal_file):
        try:
            with open(signal_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            os.remove(signal_file)
            return data
        except Exception:
            try:
                os.remove(signal_file)
            except OSError:
                pass
            return {"question": "User input required (signal file)"}
    return None


def check_git_dirty(project_dir: str) -> str | None:
    """Check for uncommitted changes. Returns status string or None if clean."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=project_dir,
            timeout=10,
        )
        status = result.stdout.strip()
        if status:
            return status
    except Exception:
        pass
    return None


def write_log(log_dir: str, iteration: int, result_text: str,
              feature_list_path: str) -> str:
    """Write session log file. Returns log file path."""
    os.makedirs(log_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    log_file = os.path.join(log_dir, f"session-{timestamp}-iter-{iteration}.md")

    with open(log_file, "w", encoding="utf-8") as lf:
        lf.write(f"# Session Log — Iteration {iteration}\n\n")
        lf.write(f"**Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        lf.write("---\n\n")
        lf.write(result_text)
        lf.write("\n")

        # Feature status
        try:
            total, passing, failing = load_feature_status(feature_list_path)
            lf.write(f"\n---\n\n**Status**: {passing}/{total} passing, {failing} failing\n")
        except Exception:
            pass

    return log_file


def run_iteration(
    iteration: int,
    project_dir: str,
    prompt: str,
    log_dir: str,
    feature_list_path: str,
    model: str | None = None,
    attach: str | None = None,
) -> tuple[int, str, str]:
    """Run one opencode iteration. Returns (exit_code, captured_output, log_file)."""
    global _active_proc

    cmd = ["opencode", "run", "--yolo"]
    if model:
        cmd.extend(["--model", model])
    if attach:
        cmd.extend(["--attach", attach])
    cmd.append(prompt)

    header = f"\n{'='*60}\n  Iteration {iteration}\n{'='*60}\n"
    print(header, flush=True)

    captured = []
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=project_dir,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        _active_proc = proc

        for line in proc.stdout:
            print(line, end="", flush=True)
            captured.append(line)

        proc.wait()
        _active_proc = None

        result_text = "".join(captured)
        log_file = write_log(log_dir, iteration, result_text, feature_list_path)
        return proc.returncode, result_text, log_file

    except FileNotFoundError:
        _active_proc = None
        print("ERROR: 'opencode' command not found. Is OpenCode installed?", flush=True)
        return -1, "", ""
    except KeyboardInterrupt:
        # Should not normally reach here (signal handler takes over),
        # but keep as safety net.
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        _active_proc = None
        return -2, "".join(captured), ""


def interruptible_sleep(seconds: int) -> bool:
    """Sleep in 1-second increments, checking for interrupt. Returns True if interrupted."""
    for _ in range(seconds):
        if _interrupt_requested:
            return True
        time.sleep(1)
    return _interrupt_requested


def main() -> int:
    _force_utf8_io()
    # Install signal handler before anything else
    signal.signal(signal.SIGINT, _signal_handler)

    parser = argparse.ArgumentParser(
        description="Auto-loop OpenCode for long-task feature development. "
                    "Each invocation gets a fresh context (implicit /clear)."
    )
    parser.add_argument("feature_list", help="Path to feature-list.json")
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=50,
        help="Maximum number of iterations (default: 50)",
    )
    parser.add_argument(
        "--cooldown",
        type=int,
        default=5,
        help="Seconds to wait between iterations (default: 5)",
    )
    parser.add_argument(
        "--prompt",
        default="go on",
        help="Prompt to send each iteration (default: go on)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model to use (format: provider/model, e.g. anthropic/claude-sonnet-4-6)",
    )
    parser.add_argument(
        "--attach",
        default=None,
        help="Attach to a running opencode serve instance (e.g. http://localhost:4096)",
    )
    parser.add_argument(
        "--log-dir",
        default="logs",
        help="Directory for session logs (default: logs)",
    )
    args = parser.parse_args()

    feature_list_path = os.path.abspath(args.feature_list)
    if not os.path.isfile(feature_list_path):
        print(f"ERROR: feature-list.json not found: {feature_list_path}")
        return 1

    project_dir = os.path.dirname(feature_list_path)
    log_dir = os.path.join(project_dir, args.log_dir)

    # Show initial status
    try:
        total, passing, failing = load_feature_status(feature_list_path)
        print(f"Project dir: {project_dir}")
        print(f"Features: {total} total, {passing} passing, {failing} failing")
        print(f"Max iterations: {args.max_iterations}, Cooldown: {args.cooldown}s")
        print(f"Log dir: {log_dir}")
        if args.model:
            print(f"Model: {args.model}")
        if args.attach:
            print(f"Attach: {args.attach}")
        print(f"Tip: Ctrl+C once = stop after iteration, twice = force kill")
    except Exception as e:
        print(f"ERROR: Cannot read feature-list.json: {e}")
        return 1

    if check_all_passing(feature_list_path):
        print("All features already passing. Nothing to do.")
        return 0

    # Git dirty state check
    dirty = check_git_dirty(project_dir)
    if dirty:
        print(f"\nWARNING: Dirty git state detected:")
        for line in dirty.split("\n")[:5]:
            print(f"  {line}")
        print()

    for i in range(1, args.max_iterations + 1):
        # Check for pending graceful stop before starting next iteration
        if _interrupt_requested:
            print(f"\nSTOPPED: Graceful interrupt before iteration {i}.")
            return 130

        exit_code, output, log_file = run_iteration(
            i, project_dir, args.prompt, log_dir, feature_list_path,
            args.model, args.attach,
        )

        if log_file:
            print(f"\n  Log: {log_file}", flush=True)

        # Check for keyboard interrupt
        if exit_code == -2:
            return 130

        # Check for command not found
        if exit_code == -1:
            return 1

        # Check for ask-user signal file from OpenCode plugin
        ask_signal = detect_ask_user_signal(project_dir)
        if ask_signal:
            print(f"\n{'='*60}")
            print(f"  USER INPUT REQUIRED — Loop paused")
            print(f"{'='*60}")
            q = ask_signal.get("question", ask_signal.get("text", str(ask_signal)))
            print(f"  {q}")
            print(f"\nPlease handle the request, then restart the loop:")
            print(f"  python scripts/auto_loop_opencode.py {args.feature_list}")
            return 4

        # Check for error patterns in output
        error_match = detect_error(output)
        if error_match:
            print(f"\nSTOPPED: Detected error pattern: {error_match}")
            return 3

        # Check for non-zero exit
        if exit_code != 0:
            print(f"\nSTOPPED: opencode exited with code {exit_code}")
            return 2

        # Check if all features now pass
        try:
            total, passing, failing = load_feature_status(feature_list_path)
            print(f"\n--- Status: {passing}/{total} passing, {failing} failing ---")
        except Exception:
            pass

        if check_all_passing(feature_list_path):
            print(f"\nSUCCESS: All features passing after {i} iteration(s)!")
            return 0

        # Check for graceful stop after iteration completed
        if _interrupt_requested:
            print(f"\nSTOPPED: Graceful interrupt after iteration {i}.")
            return 130

        # Cooldown before next iteration (interruptible)
        if i < args.max_iterations:
            print(f"Cooling down {args.cooldown}s before next iteration...")
            if interruptible_sleep(args.cooldown):
                print(f"\nSTOPPED: Interrupted during cooldown after iteration {i}.")
                return 130

    print(f"\nSTOPPED: Reached max iterations ({args.max_iterations})")
    return 1


if __name__ == "__main__":
    sys.exit(main())
