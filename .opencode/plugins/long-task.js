/**
 * Long-Task Agent plugin for OpenCode.ai
 *
 * Copies init_project.py to the consumer project and provides
 * AskUserQuestion signal detection for auto_loop_opencode.py.
 * Skills are discovered via OpenCode's native skill tool from symlinked directory.
 */

import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// ─── Copy init_project.py to target project ──────────────────────────────────
// Ensures models following `python scripts/init_project.py …` from SKILL.md can
// find the script. The companion hint file tells the copied script where the
// plugin root is so it can locate and copy helper scripts (validate_features.py
// etc.) into the target project's scripts/ directory correctly.

const pluginRoot = path.resolve(__dirname, '../..');

const copyInitScript = (directory) => {
  try {
    const src = path.join(pluginRoot, 'skills', 'long-task-init', 'scripts', 'init_project.py');
    if (!fs.existsSync(src)) return;
    const targetScriptsDir = path.join(directory, 'scripts');
    if (!fs.existsSync(targetScriptsDir)) {
      fs.mkdirSync(targetScriptsDir, { recursive: true });
    }
    fs.copyFileSync(src, path.join(targetScriptsDir, 'init_project.py'));
    fs.writeFileSync(
      path.join(targetScriptsDir, '.long-task-plugin-root'),
      pluginRoot,
      'utf8'
    );
  } catch {
    // Non-fatal — never break the session
  }
};

// ─── Copy phase_route.py + import deps (count_pending, validate_features) ────
// phase_route.py imports its siblings via sys.path insert, so all three must
// land together in the project's scripts/ dir — including pre-init, where
// `long-task-init` hasn't yet populated scripts/.
const copyRouterScripts = (directory) => {
  const routerScripts = ['phase_route.py', 'count_pending.py', 'validate_features.py'];
  try {
    const targetScriptsDir = path.join(directory, 'scripts');
    if (!fs.existsSync(targetScriptsDir)) {
      fs.mkdirSync(targetScriptsDir, { recursive: true });
    }
    for (const name of routerScripts) {
      const src = path.join(pluginRoot, 'scripts', name);
      if (fs.existsSync(src)) {
        fs.copyFileSync(src, path.join(targetScriptsDir, name));
      }
    }
  } catch {
    // Non-fatal — never break the session
  }
};

// ─── Chrome DevTools MCP auto-setup ──────────────────────────────────────────

const CHROME_MCP_KEY = 'chrome-devtools';
// OpenCode MCP format: type='local', command as array (not stdio/args style)
const CHROME_MCP_ENTRY = {
  type: 'local',
  command: ['npx', '-y', 'chrome-devtools-mcp@latest', '--isolated=true', '--no-usage-statistics'],
};

/**
 * Upsert chrome-devtools MCP server into ~/.config/opencode/opencode.json.
 * Idempotent — skips write when the entry already matches exactly.
 * Non-fatal: errors are swallowed so a bad config never breaks a session.
 */
const setupChromeMcp = () => {
  try {
    const homeDir = process.env.HOME || process.env.USERPROFILE || '';
    const configPath = path.join(homeDir, '.config', 'opencode', 'opencode.json');
    const configDir = path.dirname(configPath);

    if (!fs.existsSync(configDir)) {
      fs.mkdirSync(configDir, { recursive: true });
    }

    let config = {};
    if (fs.existsSync(configPath)) {
      try {
        config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
      } catch {
        // Malformed JSON — overwrite with a clean config
      }
    }

    config.mcp = config.mcp || {};

    // Skip write when entry already matches
    if (JSON.stringify(config.mcp[CHROME_MCP_KEY]) === JSON.stringify(CHROME_MCP_ENTRY)) {
      return;
    }

    config.mcp[CHROME_MCP_KEY] = CHROME_MCP_ENTRY;
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2) + '\n', 'utf8');
  } catch {
    // Non-fatal — never break the session
  }
};

/**
 * OpenCode plugin entry point.
 * Copies init script on startup; provides interactive-tool signal for auto_loop.
 */
export const LongTaskPlugin = async ({ client, directory }) => {
  setupChromeMcp();
  copyInitScript(directory);
  copyRouterScripts(directory);
  return {
    // ─── AskUserQuestion signal file for auto_loop detection ─────────
    // When an interactive tool is called, write a signal file so that
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
