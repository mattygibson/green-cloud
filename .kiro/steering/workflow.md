# Workflow Conventions

## Task Execution

- Always reference the current task from `.kiro/plans/` before starting work
- Complete one task at a time in order unless instructed otherwise
- Run tests/verification after each implementation step
- Do not move to the next task without confirming the current one works

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
