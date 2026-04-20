/**
 * Long-Task Agent plugin for OpenCode.ai
 *
 * On session startup, mirrors the claude-code SessionStart hook behavior:
 *   1. Copies init_project.py + phase_route.py + count_pending.py + validate_features.py
 *      into <project>/scripts/ so pre-init sessions can run `python scripts/phase_route.py`.
 *   2. When project root is NOT a git repo, scans for sub-directory git repos and
 *      generates repos-manifest.json (entry point for long-task-multi-repo skill).
 *   3. Writes .long-task-plugin-root hint so init_project.py can locate helpers.
 *
 * Also exposes a tool.execute.before lifecycle hook that writes ask-user-signal.json
 * when an interactive tool is called, so auto_loop_opencode.py can pause the loop.
 *
 * All hook logic is best-effort — failures are swallowed and never abort the session.
 * Skills are discovered via OpenCode's native skill tool from the symlinked directory.
 */

import path from 'path';
import fs from 'fs';
import { execFileSync } from 'child_process';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const pluginRoot = path.resolve(__dirname, '../..');

// Plugin root path written into <project>/scripts/.long-task-plugin-root.
// init_project.py reads this on Windows where Git Bash POSIX paths (/c/...) are
// unusable by Python; normalize to forward slashes for cross-platform consistency.
const pluginRootHint = pluginRoot.replace(/\\/g, '/');

const ROUTER_SCRIPTS = ['phase_route.py', 'count_pending.py', 'validate_features.py'];

function copyInitScript(directory) {
  const src = path.join(pluginRoot, 'skills', 'long-task-init', 'scripts', 'init_project.py');
  if (!fs.existsSync(src)) return;
  const scriptsDir = path.join(directory, 'scripts');
  fs.mkdirSync(scriptsDir, { recursive: true });
  fs.copyFileSync(src, path.join(scriptsDir, 'init_project.py'));
  fs.writeFileSync(path.join(scriptsDir, '.long-task-plugin-root'), pluginRootHint, 'utf8');
}

// phase_route.py imports count_pending + validate_features via sys.path insert,
// so all three must land together. Required in pre-init sessions before
// long-task-init populates scripts/.
function copyRouterScripts(directory) {
  const scriptsDir = path.join(directory, 'scripts');
  for (const name of ROUTER_SCRIPTS) {
    const src = path.join(pluginRoot, 'scripts', name);
    if (!fs.existsSync(src)) continue;
    fs.mkdirSync(scriptsDir, { recursive: true });
    fs.copyFileSync(src, path.join(scriptsDir, name));
  }
}

// Depth-limited walk mirroring `find . -maxdepth 4 -name ".git" -type d`.
// Returns absolute paths of matched .git directories.
function findGitDirs(root, maxDepth) {
  const results = [];
  const walk = (dir, depth) => {
    if (depth > maxDepth) return;
    let entries;
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true });
    } catch {
      return;
    }
    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      const full = path.join(dir, entry.name);
      if (entry.name === '.git') {
        results.push(full);
        continue; // don't recurse into .git internals
      }
      walk(full, depth + 1);
    }
  };
  walk(root, 1); // depth 1 = direct children of root, matching find's behavior
  return results.sort();
}

function gitRevParse(cwd, arg) {
  try {
    return execFileSync('git', ['-C', cwd, 'rev-parse', arg], {
      stdio: ['ignore', 'pipe', 'ignore'],
      encoding: 'utf8',
    }).trim();
  } catch {
    return null;
  }
}

// Generates repos-manifest.json at project root if (and only if):
//   - project root is NOT a git repo
//   - at least one validated sub-directory git repo exists
//   - repos-manifest.json does not already exist (preserve downstream enrichment
//     from long-task-multi-repo skill)
//
// Also copies init_project.py + hint into each validated sub-repo's scripts/
// so each repo can run the single-repo pipeline independently.
function detectMultiRepo(directory) {
  if (fs.existsSync(path.join(directory, '.git'))) {
    // Single-repo mode: clean up any stale manifest
    const stale = path.join(directory, 'repos-manifest.json');
    if (fs.existsSync(stale)) {
      try { fs.unlinkSync(stale); } catch { /* swallow */ }
    }
    return;
  }

  const gitDirs = findGitDirs(directory, 4);
  const projectRoot = fs.realpathSync(directory);
  const validated = [];

  for (const gitDir of gitDirs) {
    let candidate;
    try {
      candidate = fs.realpathSync(path.dirname(gitDir));
    } catch {
      continue;
    }
    // Check 1: real git working tree?
    if (gitRevParse(candidate, '--is-inside-work-tree') !== 'true') continue;
    // Check 2: is this the repo root (not a worktree/submodule link)?
    // git-dir returns ".git" ONLY at repo root; subdirs return "../.git" or absolute;
    // worktrees return a linked path.
    if (gitRevParse(candidate, '--git-dir') !== '.git') continue;
    validated.push(candidate);
  }

  if (validated.length === 0) return;

  const manifestPath = path.join(directory, 'repos-manifest.json');
  if (!fs.existsSync(manifestPath)) {
    const repos = validated.map(abs => {
      const rel = path.relative(projectRoot, abs).replace(/\\/g, '/');
      return { name: path.basename(rel), path: rel };
    });
    const manifest = {
      detected: new Date().toISOString().replace(/\.\d{3}Z$/, 'Z'),
      project_root_is_git: false,
      repos,
    };
    fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + '\n', 'utf8');
  }

  // Copy init_project.py + hint into each validated sub-repo
  const initSrc = path.join(pluginRoot, 'skills', 'long-task-init', 'scripts', 'init_project.py');
  if (!fs.existsSync(initSrc)) return;
  for (const abs of validated) {
    const repoScriptsDir = path.join(abs, 'scripts');
    try {
      fs.mkdirSync(repoScriptsDir, { recursive: true });
      fs.copyFileSync(initSrc, path.join(repoScriptsDir, 'init_project.py'));
      fs.writeFileSync(path.join(repoScriptsDir, '.long-task-plugin-root'), pluginRootHint, 'utf8');
    } catch {
      // swallow — best-effort per repo
    }
  }
}

/**
 * OpenCode plugin entry point.
 * Runs SessionStart-equivalent setup synchronously (to match claude-code's
 * `async: false` hook), then registers the tool.execute.before lifecycle hook.
 */
export const LongTaskPlugin = async ({ client, directory }) => {
  try { copyInitScript(directory); }    catch { /* non-fatal */ }
  try { copyRouterScripts(directory); } catch { /* non-fatal */ }
  try { detectMultiRepo(directory); }   catch { /* non-fatal */ }

  return {
    // When an interactive tool is called, write a signal file so
    // auto_loop_opencode.py can detect it and pause the loop.
    'tool.execute.before': async (input, output) => {
      const interactiveTools = ['ask_user', 'ask_question', 'user_input'];
      const isInteractiveBash = input.tool === 'bash' &&
        output.args?.command &&
        /\bread\s+(-[rspn]\s+)*-?p\b/.test(output.args.command);

      if (interactiveTools.includes(input.tool) || isInteractiveBash) {
        const signalDir = path.join(directory, '.claude');
        if (!fs.existsSync(signalDir)) {
          fs.mkdirSync(signalDir, { recursive: true });
        }
        fs.writeFileSync(
          path.join(signalDir, 'ask-user-signal.json'),
          JSON.stringify({
            tool: input.tool,
            question: output.args?.question || output.args?.text || 'User input required',
            timestamp: new Date().toISOString(),
          }, null, 2),
          'utf8'
        );
      }
    },
  };
};
