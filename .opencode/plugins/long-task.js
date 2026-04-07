/**
 * Long-Task Agent plugin for OpenCode.ai
 *
 * Injects the using-long-task bootstrap router and phase detection
 * into every OpenCode session via system prompt transform.
 * Skills are discovered via OpenCode's native skill tool from symlinked directory.
 */

import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Simple frontmatter extraction (avoid external dependencies for bootstrap)
const extractAndStripFrontmatter = (content) => {
  const match = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  if (!match) return { frontmatter: {}, content };

  const frontmatterStr = match[1];
  const body = match[2];
  const frontmatter = {};

  for (const line of frontmatterStr.split('\n')) {
    const colonIdx = line.indexOf(':');
    if (colonIdx > 0) {
      const key = line.slice(0, colonIdx).trim();
      const value = line.slice(colonIdx + 1).trim().replace(/^["']|["']$/g, '');
      frontmatter[key] = value;
    }
  }

  return { frontmatter, content: body };
};

/**
 * Detect project phase by checking file existence.
 * Ported from hooks/session-start (bash) to JavaScript.
 *
 * Priority order:
 *   1. increment-request.json → Increment
 *   2. feature-list.json + all active passing → System Testing
 *   3. feature-list.json + some failing → Worker
 *   4. docs/plans/*-design.md → Initializer
 *   5. docs/plans/*-srs.md → Design
 *   6. (none) → Requirements
 */
const detectPhase = (projectDir) => {
  // 1. Increment request (highest priority)
  if (fs.existsSync(path.join(projectDir, 'increment-request.json'))) {
    return 'Increment request found. Phase: Increment.';
  }

  // 2-3. Feature list — count active/passing
  const flPath = path.join(projectDir, 'feature-list.json');
  if (fs.existsSync(flPath)) {
    try {
      const data = JSON.parse(fs.readFileSync(flPath, 'utf8'));
      const features = data.features || [];
      const active = features.filter(f => !f.deprecated);
      const passing = active.filter(f => f.status === 'passing');
      const depCount = features.filter(f => f.deprecated).length;
      const depNote = depCount > 0 ? ` (${depCount} deprecated)` : '';

      if (active.length > 0 && passing.length === active.length) {
        return `Project status: ${passing.length}/${active.length} active features passing (ALL)${depNote}. Phase: System Testing.`;
      }
      return `Project status: ${passing.length}/${active.length} active features passing${depNote}. Phase: Worker.`;
    } catch {
      return 'feature-list.json exists but could not be parsed. Phase: Worker.';
    }
  }

  // 4-5. Check docs/plans/ for design, SRS files
  const plansDir = path.join(projectDir, 'docs', 'plans');
  try {
    if (fs.existsSync(plansDir)) {
      const files = fs.readdirSync(plansDir);
      if (files.some(f => f.endsWith('-design.md'))) {
        return 'Design doc found. Phase: Initializer.';
      }
      if (files.some(f => f.endsWith('-srs.md'))) {
        return 'SRS doc found. Phase: Design.';
      }
    }
  } catch {
    // Directory read failure — fall through to default
  }

  // 7. No artifacts found
  return 'No SRS, design, or feature-list.json found. Phase: Requirements.';
};

// Resolve plugin root → skills directory (../../skills relative to this file)
const skillsDir = path.resolve(__dirname, '../../skills');

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
 * Build the bootstrap content to inject into the system prompt.
 * Includes: using-long-task SKILL.md + phase hint + tool mapping.
 */
const getBootstrapContent = (directory) => {
  const skillPath = path.join(skillsDir, 'using-long-task', 'SKILL.md');
  if (!fs.existsSync(skillPath)) return null;

  const fullContent = fs.readFileSync(skillPath, 'utf8');
  const { content } = extractAndStripFrontmatter(fullContent);
  const phaseHint = detectPhase(directory);

  const toolMapping = `**Tool Mapping for OpenCode:**
When skills reference tools, substitute OpenCode equivalents:
- \`TodoWrite\` → \`update_plan\`
- \`Task\` tool with subagents → OpenCode's subagent system (@mention)
- \`Skill\` tool → OpenCode's native \`skill\` tool
- \`Read\`, \`Write\`, \`Edit\`, \`Bash\` → Your native tools

**Skill name format:**
When SKILL.md says \`long-task:long-task-work\`, invoke via OpenCode's skill tool as: skill({ name: "long-task-work" })
Skills are installed at: ~/.config/opencode/skills/long-task/`;

  return `<EXTREMELY_IMPORTANT>
You are in a long-task project.

**IMPORTANT: The using-long-task skill content is included below. It is ALREADY LOADED - you are currently following it. Do NOT use the skill tool to load "using-long-task" again - that would be redundant.**

${content}

${phaseHint}

${toolMapping}
</EXTREMELY_IMPORTANT>`;
};

/**
 * OpenCode plugin entry point.
 * Uses experimental.chat.system.transform to inject bootstrap context
 * into every session's system prompt (same approach as superpowers plugin).
 */
export const LongTaskPlugin = async ({ client, directory }) => {
  copyInitScript(directory);
  return {
    'experimental.chat.system.transform': async (_input, output) => {
      const bootstrap = getBootstrapContent(directory);
      if (bootstrap) {
        (output.system ||= []).push(bootstrap);
      }
    },

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
