#!/usr/bin/env python3
"""Auto-loop script for long-task feature development.

Repeatedly calls `claude -p "go on" --dangerously-skip-permissions` (or opencode)
until all active features pass, max iterations are reached, or an error occurs.

Each invocation gets a fresh context (implicit /clear). Session logs are saved
to the --log-dir directory automatically.

AskUserQuestion detection: When the model calls AskUserQuestion in -p mode,
it appears in the JSON output's `permission_denials` array. The loop pauses
and displays the question so the user can handle it manually.

Interrupt handling:
    1st Ctrl+C — graceful: finish current iteration, then stop
    2nd Ctrl+C — forceful: kill child process immediately and exit

Usage:
    python scripts/auto_loop.py feature-list.json
    python scripts/auto_loop.py feature-list.json --max-iterations 30
    python scripts/auto_loop.py feature-list.json --cooldown 10
    python scripts/auto_loop.py feature-list.json --tool opencode
    python scripts/auto_loop.py feature-list.json --log-dir logs
"""

import argparse
import json
import os
import re
import signal
import subprocess
import sys
import time

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


def load_current_state(path: str) -> dict:
    """Return {"current": {feature_id, phase}|None, "legacy_sub_status": N}.

    `legacy_sub_status > 0` signals the project predates the current-lock
    refactor and needs `scripts/migrate_sub_status.py`.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"current": None, "legacy_sub_status": 0}
    features = data.get("features", [])
    legacy = sum(1 for f in features
                 if isinstance(f, dict) and "sub_status" in f
                 and not f.get("deprecated"))
    return {"current": data.get("current"), "legacy_sub_status": legacy}


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


def detect_ask_user(result_json: dict) -> dict | None:
    """Check JSON result for AskUserQuestion in permission_denials.

    Returns the first AskUserQuestion tool_input dict, or None.
    """
    denials = result_json.get("permission_denials", [])
    for denial in denials:
        if denial.get("tool_name") == "AskUserQuestion":
            return denial.get("tool_input", {})
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


def get_git_head(project_dir: str) -> str | None:
    """Return current HEAD SHA (short), or None on error."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            cwd=project_dir,
            timeout=10,
        )
        return result.stdout.strip() or None
    except Exception:
        return None


def get_git_commits_since(project_dir: str, since_sha: str) -> str:
    """Return oneline git log from since_sha..HEAD, or empty string."""
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", f"{since_sha}..HEAD"],
            capture_output=True,
            text=True,
            cwd=project_dir,
            timeout=10,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def write_log(log_dir: str, iteration: int, result_text: str,
              result_json: dict | None, feature_list_path: str,
              git_commits: str | None = None) -> str:
    """Write session log file. Returns log file path."""
    os.makedirs(log_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    log_file = os.path.join(log_dir, f"session-{timestamp}-iter-{iteration}.md")

    with open(log_file, "w", encoding="utf-8") as lf:
        lf.write(f"# Session Log — Iteration {iteration}\n\n")
        lf.write(f"**Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Cost info from JSON result
        if result_json:
            cost = result_json.get("total_cost_usd")
            duration = result_json.get("duration_ms")
            turns = result_json.get("num_turns")
            if cost is not None:
                lf.write(f"**Cost**: ${cost:.4f}")
                if duration:
                    lf.write(f" | **Duration**: {duration / 1000:.1f}s")
                if turns:
                    lf.write(f" | **Turns**: {turns}")
                lf.write("\n\n")

        lf.write("---\n\n")

        # Main content
        lf.write(result_text)
        lf.write("\n")

        # Feature status + current lock
        try:
            total, passing, failing = load_feature_status(feature_list_path)
            lf.write(f"\n---\n\n**Status**: {passing}/{total} passing, {failing} failing")
            state = load_current_state(feature_list_path)
            cur = state["current"]
            if cur and isinstance(cur, dict):
                lf.write(f" | current=#{cur.get('feature_id')}({cur.get('phase')})")
            else:
                lf.write(" | current=none")
            if state["legacy_sub_status"]:
                lf.write(f" | legacy_sub_status={state['legacy_sub_status']}")
            lf.write("\n")
        except Exception:
            pass

        # Git commits made during this iteration
        if git_commits:
            lf.write(f"\n## Git Commits\n\n```\n{git_commits}\n```\n")

    return log_file


def run_iteration_claude(iteration: int, project_dir: str, prompt: str,
                         log_dir: str) -> tuple[int, str, dict | None, str]:
    """Run one claude -p iteration with --output-format json.

    Returns (exit_code, result_text, result_json, log_file).
    """
    global _active_proc

    cmd = [
        "claude",
        "-p",
        prompt,
        "--dangerously-skip-permissions",
        "--output-format", "json",
    ]

    header = f"\n{'='*60}\n  Iteration {iteration}\n{'='*60}\n"
    print(header, flush=True)

    head_before = get_git_head(project_dir)

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=project_dir,
            encoding="utf-8",
            errors="replace",
        )
        _active_proc = proc

        stdout, stderr = proc.communicate()
        _active_proc = None

        # Parse JSON result
        result_json = None
        result_text = ""
        try:
            result_json = json.loads(stdout)
            result_text = result_json.get("result", "")
        except json.JSONDecodeError:
            result_text = stdout

        # Print result text to terminal
        print(result_text, flush=True)

        # Print any stderr
        if stderr.strip():
            print(stderr, file=sys.stderr, flush=True)

        # Capture git commits made during this iteration
        git_commits = get_git_commits_since(project_dir, head_before) if head_before else None

        # Write log
        log_file = write_log(log_dir, iteration, result_text,
                             result_json, os.path.join(project_dir, "feature-list.json"),
                             git_commits=git_commits)

        return proc.returncode, result_text, result_json, log_file

    except FileNotFoundError:
        _active_proc = None
        print("ERROR: 'claude' command not found. Is Claude Code installed?", flush=True)
        return -1, "", None, ""
    except KeyboardInterrupt:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        _active_proc = None
        return -2, "", None, ""


def run_iteration_opencode(iteration: int, project_dir: str, prompt: str,
                           log_dir: str) -> tuple[int, str, dict | None, str]:
    """Run one opencode -p iteration.

    Returns (exit_code, result_text, result_json, log_file).
    """
    global _active_proc

    cmd = ["opencode", "-p", prompt]

    header = f"\n{'='*60}\n  Iteration {iteration}\n{'='*60}\n"
    print(header, flush=True)

    head_before = get_git_head(project_dir)

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
        git_commits = get_git_commits_since(project_dir, head_before) if head_before else None
        log_file = write_log(log_dir, iteration, result_text,
                             None, os.path.join(project_dir, "feature-list.json"),
                             git_commits=git_commits)

        return proc.returncode, result_text, None, log_file

    except FileNotFoundError:
        _active_proc = None
        print("ERROR: 'opencode' command not found. Is OpenCode installed?", flush=True)
        return -1, "", None, ""
    except KeyboardInterrupt:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        _active_proc = None
        return -2, "", None, ""


def interruptible_sleep(seconds: int) -> bool:
    """Sleep in 1-second increments, checking for interrupt. Returns True if interrupted."""
    for _ in range(seconds):
        if _interrupt_requested:
            return True
        time.sleep(1)
    return _interrupt_requested


def format_ask_question(ask_input: dict) -> str:
    """Format AskUserQuestion input for display."""
    lines = []
    questions = ask_input.get("questions", [])
    if not questions:
        # Fallback: might be a flat dict with 'question' key
        q = ask_input.get("question", ask_input.get("text", str(ask_input)))
        return f"  {q}"

    for q in questions:
        header = q.get("header", "")
        question = q.get("question", "")
        if header:
            lines.append(f"  [{header}] {question}")
        else:
            lines.append(f"  {question}")
        options = q.get("options", [])
        for opt in options:
            label = opt.get("label", "")
            desc = opt.get("description", "")
            lines.append(f"    - {label}: {desc}")
    return "\n".join(lines)


def main() -> int:
    # Install signal handler before anything else
    signal.signal(signal.SIGINT, _signal_handler)

    parser = argparse.ArgumentParser(
        description="Auto-loop for long-task feature development. "
                    "Each iteration runs in a fresh context (implicit /clear)."
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
        "--tool",
        default="claude",
        choices=["claude", "opencode"],
        help="CLI tool to use (default: claude)",
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
    total_cost = 0.0

    # Show initial status
    try:
        total, passing, failing = load_feature_status(feature_list_path)
        print(f"Project dir: {project_dir}")
        print(f"Tool: {args.tool}")
        print(f"Features: {total} total, {passing} passing, {failing} failing")
        state = load_current_state(feature_list_path)
        cur = state["current"]
        if cur and isinstance(cur, dict):
            print(f"Current lock: feature #{cur.get('feature_id')} "
                  f"({cur.get('phase')})")
        else:
            print("Current lock: none (next session will pick a new feature)")
        if state["legacy_sub_status"]:
            print(f"NOTE: {state['legacy_sub_status']} feature(s) still carry "
                  f"legacy sub_status — router will run "
                  f"migrate_sub_status.py on first iteration")
        print(f"Max iterations: {args.max_iterations}, Cooldown: {args.cooldown}s")
        print(f"Log dir: {log_dir}")
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
            print(f"Total cost: ${total_cost:.4f}")
            return 130

        # Run iteration
        if args.tool == "claude":
            exit_code, output, result_json, log_file = run_iteration_claude(
                i, project_dir, args.prompt, log_dir
            )
        else:
            exit_code, output, result_json, log_file = run_iteration_opencode(
                i, project_dir, args.prompt, log_dir
            )

        # Track cost
        if result_json:
            iter_cost = result_json.get("total_cost_usd", 0) or 0
            total_cost += iter_cost

        if log_file:
            print(f"\n  Log: {log_file}", flush=True)

        # Check for keyboard interrupt
        if exit_code == -2:
            print(f"Total cost: ${total_cost:.4f}")
            return 130

        # Check for command not found
        if exit_code == -1:
            return 1

        # Check for AskUserQuestion (Claude Code: permission_denials)
        if result_json:
            ask_input = detect_ask_user(result_json)
            if ask_input:
                print(f"\n{'='*60}")
                print(f"  USER INPUT REQUIRED — Loop paused")
                print(f"{'='*60}")
                print(format_ask_question(ask_input))
                print(f"\nPlease handle the request, then restart the loop:")
                print(f"  python scripts/auto_loop.py {args.feature_list}")
                print(f"Total cost: ${total_cost:.4f}")
                return 4

        # Check for AskUserQuestion (OpenCode: signal file)
        if args.tool == "opencode":
            ask_signal = detect_ask_user_signal(project_dir)
            if ask_signal:
                print(f"\n{'='*60}")
                print(f"  USER INPUT REQUIRED — Loop paused")
                print(f"{'='*60}")
                q = ask_signal.get("question", ask_signal.get("text", str(ask_signal)))
                print(f"  {q}")
                print(f"\nPlease handle the request, then restart the loop:")
                print(f"  python scripts/auto_loop.py {args.feature_list} --tool opencode")
                print(f"Total cost: ${total_cost:.4f}")
                return 4

        # Check for error patterns in output
        error_match = detect_error(output)
        if error_match:
            print(f"\nSTOPPED: Detected error pattern: {error_match}")
            print(f"Total cost: ${total_cost:.4f}")
            return 3

        # Check for non-zero exit
        if exit_code != 0:
            print(f"\nSTOPPED: {args.tool} exited with code {exit_code}")
            print(f"Total cost: ${total_cost:.4f}")
            return 2

        # Check if all features now pass
        try:
            total, passing, failing = load_feature_status(feature_list_path)
            print(f"\n--- Status: {passing}/{total} passing, {failing} failing | "
                  f"Cost so far: ${total_cost:.4f} ---")
        except Exception:
            pass

        if check_all_passing(feature_list_path):
            print(f"\nSUCCESS: All features passing after {i} iteration(s)!")
            print(f"Total cost: ${total_cost:.4f}")
            return 0

        # Check for graceful stop after iteration completed
        if _interrupt_requested:
            print(f"\nSTOPPED: Graceful interrupt after iteration {i}.")
            print(f"Total cost: ${total_cost:.4f}")
            return 130

        # Cooldown before next iteration (interruptible)
        if i < args.max_iterations:
            print(f"Cooling down {args.cooldown}s before next iteration...")
            if interruptible_sleep(args.cooldown):
                print(f"\nSTOPPED: Interrupted during cooldown after iteration {i}.")
                print(f"Total cost: ${total_cost:.4f}")
                return 130

    print(f"\nSTOPPED: Reached max iterations ({args.max_iterations})")
    print(f"Total cost: ${total_cost:.4f}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
