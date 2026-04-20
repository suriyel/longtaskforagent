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

// stderr logging — mirrors hooks/session-start bash log() style so users can
// distinguish "OpenCode host still initializing (models.dev / npm reify)" from
// "this plugin is doing work" during first-run hangs.
const LOG_PREFIX = '[long-task-plugin]';
const DEBUG = process.env.LONG_TASK_DEBUG === '1';
function log(msg)   { console.error(`${LOG_PREFIX} ${msg}`); }
function debug(msg) { if (DEBUG) console.error(`${LOG_PREFIX} [debug] ${msg}`); }

function copyInitScript(directory) {
  const src = path.join(pluginRoot, 'skills', 'long-task-init', 'scripts', 'init_project.py');
  if (!fs.existsSync(src)) {
    debug(`init_project.py source missing at ${src}, skipping copy`);
    return;
  }
  const scriptsDir = path.join(directory, 'scripts');
  fs.mkdirSync(scriptsDir, { recursive: true });
  fs.copyFileSync(src, path.join(scriptsDir, 'init_project.py'));
  fs.writeFileSync(path.join(scriptsDir, '.long-task-plugin-root'), pluginRootHint, 'utf8');
  debug(`copied init_project.py → ${scriptsDir}`);
}

// phase_route.py imports count_pending + validate_features via sys.path insert,
// so all three must land together. Required in pre-init sessions before
// long-task-init populates scripts/.
function copyRouterScripts(directory) {
  const scriptsDir = path.join(directory, 'scripts');
  let copied = 0;
  for (const name of ROUTER_SCRIPTS) {
    const src = path.join(pluginRoot, 'skills', 'using-long-task', 'scripts', name);
    if (!fs.existsSync(src)) {
      debug(`router script missing: ${src}`);
      continue;
    }
    fs.mkdirSync(scriptsDir, { recursive: true });
    fs.copyFileSync(src, path.join(scriptsDir, name));
    copied++;
  }
  debug(`copied ${copied}/${ROUTER_SCRIPTS.length} router scripts → ${scriptsDir}`);
}

// Depth-limited walk mirroring `find . -maxdepth 4 -name ".git" -type d`.
// Returns absolute paths of matched .git directories.
function findGitDirs(root, maxDepth) {
  const t0 = Date.now();
  const results = [];
  const walk = (dir, depth) => {
    if (depth > maxDepth) return;
    let entries;
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true });
    } catch (err) {
      debug(`readdir failed for ${dir}: ${err.message}`);
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
  debug(`findGitDirs(maxDepth=${maxDepth}) found ${results.length} in ${Date.now() - t0}ms`);
  return results.sort();
}

function gitRevParse(cwd, arg) {
  const t0 = Date.now();
  try {
    const out = execFileSync('git', ['-C', cwd, 'rev-parse', arg], {
      stdio: ['ignore', 'pipe', 'ignore'],
      encoding: 'utf8',
    }).trim();
    debug(`git -C ${cwd} rev-parse ${arg} → ${out} (${Date.now() - t0}ms)`);
    return out;
  } catch (err) {
    debug(`git -C ${cwd} rev-parse ${arg} failed: ${err.message}`);
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
      try { fs.unlinkSync(stale); log(`removed stale repos-manifest.json (single-repo mode)`); }
      catch (err) { debug(`failed to remove stale manifest: ${err.message}`); }
    }
    debug(`single-repo mode (directory is a git repo)`);
    return;
  }

  log(`scanning for sub-repos under ${directory} (maxDepth=4)...`);
  const gitDirs = findGitDirs(directory, 4);
  const projectRoot = fs.realpathSync(directory);
  const validated = [];

  for (const gitDir of gitDirs) {
    let candidate;
    try {
      candidate = fs.realpathSync(path.dirname(gitDir));
    } catch (err) {
      debug(`realpath failed for ${gitDir}: ${err.message}`);
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

  if (validated.length === 0) {
    log(`no valid sub-repos found`);
    return;
  }
  log(`validated ${validated.length} sub-repo(s)`);

  const manifestPath = path.join(directory, 'repos-manifest.json');
  if (fs.existsSync(manifestPath)) {
    debug(`repos-manifest.json exists, preserving (downstream enrichment)`);
  } else {
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
    log(`wrote repos-manifest.json (${repos.length} repos)`);
  }

  // Copy init_project.py + hint into each validated sub-repo
  const initSrc = path.join(pluginRoot, 'skills', 'long-task-init', 'scripts', 'init_project.py');
  if (!fs.existsSync(initSrc)) {
    debug(`init_project.py source missing, skipping per-repo mirror`);
    return;
  }
  for (const abs of validated) {
    const repoScriptsDir = path.join(abs, 'scripts');
    try {
      fs.mkdirSync(repoScriptsDir, { recursive: true });
      fs.copyFileSync(initSrc, path.join(repoScriptsDir, 'init_project.py'));
      fs.writeFileSync(path.join(repoScriptsDir, '.long-task-plugin-root'), pluginRootHint, 'utf8');
      debug(`mirrored helpers → ${repoScriptsDir}`);
    } catch (err) {
      debug(`per-repo mirror failed for ${abs}: ${err.message}`);
    }
  }
}

/**
 * OpenCode plugin entry point.
 * Runs SessionStart-equivalent setup synchronously (to match claude-code's
 * `async: false` hook), then registers the tool.execute.before lifecycle hook.
 */
export const LongTaskPlugin = async ({ client, directory }) => {
  const t0 = Date.now();
  log(`init start, directory=${directory}${DEBUG ? ' (LONG_TASK_DEBUG=1)' : ''}`);
  try { copyInitScript(directory); }    catch (err) { debug(`copyInitScript failed: ${err.message}`); }
  try { copyRouterScripts(directory); } catch (err) { debug(`copyRouterScripts failed: ${err.message}`); }
  try { detectMultiRepo(directory); }   catch (err) { debug(`detectMultiRepo failed: ${err.message}`); }
  log(`init done in ${Date.now() - t0}ms`);

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
        debug(`ask-user-signal written (tool=${input.tool})`);
      }
    },
  };
};
