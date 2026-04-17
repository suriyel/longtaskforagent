# Implementer Subagent Prompt

You are implementing a task for the {{PROJECT_NAME}} project.

## Project Context
- Tech stack: {{TECH_STACK}}
- Test framework: {{TEST_FRAMEWORK}}
- Key patterns: {{KEY_PATTERNS}}
- Working directory: {{WORKING_DIR}}

## Task
{{FULL_TASK_TEXT}}

## Exit Criteria

1. Run `{{TEST_COMMAND}}` — all tests pass
2. Run `{{COVERAGE_COMMAND}}` — line coverage >= {{LINE_COV_MIN}}%, branch >= {{BRANCH_COV_MIN}}%
3. Files created/modified: {{FILE_LIST}}
4. No regressions: run `{{FULL_TEST_COMMAND}}` — all pass

## Rules
- Follow TDD: write failing tests first, then implement minimal code to pass
- Run coverage after tests pass
- Do not modify files outside the scope of this task
- If you encounter an issue, document it and stop — do not guess-and-fix
- Commit your changes with a descriptive message referencing the feature ID
