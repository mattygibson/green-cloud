# Workflow Conventions

## GitHub Issue Management (HARD RULE — never deviate)

- **Before ANY work begins**, a GitHub issue MUST exist for that work
- If no issue exists, create one before writing any code or making any changes
- When starting work on a task, the corresponding GitHub issue MUST be labelled `in progress` immediately
- When work is complete, the issue MUST be closed
- This applies to all work: planned tasks, bug fixes, ad-hoc requests, refactors — no exceptions
- Repository: `mattygibson/green-cloud`

## Task Execution

- Always reference the current task from `.kiro/plans/` before starting work
- Complete one task at a time in order unless instructed otherwise
- Run tests/verification after each implementation step
- Do not move to the next task without confirming the current one works

## Branching Strategy (HARD RULE — never deviate)

- **Never commit directly to `main`** — all work goes through a feature branch
- Create a branch for each issue before starting work: `<type>/<issue-number>-<short-description>`
  - Examples: `feature/2-compose-stacks`, `infra/3-local-registry`, `docs/11-add-runbook`
- When work is complete, merge the branch to `main` via PR (or direct merge if no review is needed)
- The PR/merge commit should reference the issue: `Closes #<number>`
- Delete the branch after merging
- Branch naming types: `feature/`, `fix/`, `infra/`, `docs/`, `refactor/`, `test/`

## Code Changes

- Read existing code before modifying it
- Match existing project style and conventions from `greencloud.md`
- Keep commits focused — one logical change per commit
- Use conventional commit messages: `feat:`, `fix:`, `docs:`, `infra:`, `test:`, `refactor:`

## Docker and Infrastructure

- Always test Docker Compose changes by running `docker compose config` to validate
- Use `docker compose up --build` when Dockerfiles change
- Keep infrastructure config (infra/) separate from application code (services/)

## When Stuck

- If a build fails twice with the same approach, step back and try a different strategy
- If a dependency conflict arises, pin the working version and document it
- If hardware-specific code can't be tested locally, add a clear stub with a TODO comment
