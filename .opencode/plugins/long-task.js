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

/**
 * OpenCode plugin entry point.
 * Copies init script on startup; provides interactive-tool signal for auto_loop.
 */
export const LongTaskPlugin = async ({ client, directory }) => {
  copyInitScript(directory);
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
