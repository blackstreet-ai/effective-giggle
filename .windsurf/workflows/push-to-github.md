---
description: Safely stages, commits, tests, pushes, and opens a Pull Request for the current branch using Conventional Commits.
---

# /push-to-github
## Goal
Safely stage, commit, test, push, and open a Pull Request for the current branch using Conventional Commits.

## Notes for Cascade
- Prefer npm/yarn/pnpm consistent with the lockfile present.
- Use the repo’s configured test and lint commands if found in package.json (or equivalent for other stacks).
- If any step fails, stop and report clearly.

## Steps

### 1) Preflight: identify branch & status
Explain what you will do. Then run:
- `git rev-parse --abbrev-ref HEAD`
- `git status --porcelain`
- If there are NO changes, ask me whether to continue (e.g., still open a PR) or abort.

### 2) Sync with default branch
- Detect default branch (`git remote show origin | sed -n 's/.*HEAD branch: //p'`) and store its name.
- Run `git fetch origin`
- Rebase current branch on top of default: `git rebase origin/<DEFAULT_BRANCH>`
- If conflicts occur, pause and guide me to resolve. After resolution, continue.

### 3) Lint & test locally (fast feedback)
- Try to run lint if available:
  - npm: `npm run lint`  | yarn: `yarn lint` | pnpm: `pnpm lint`
- Try to run tests:
  - npm: `npm test --silent` | yarn: `yarn test --silent` | pnpm: `pnpm test --silent`
- If no scripts exist, skip with a note.

### 4) Stage files deliberately
- Show me a concise diff summary.
- Ask: “Stage all changes?” If yes: `git add -A`. If no: interactively stage chosen paths.

### 5) Create a Conventional Commit message
- Ask me for a short description, then compose a Conventional Commit:
  - Format: `<type>(optional scope): <description>`
  - Types: feat | fix | docs | style | refactor | perf | test | chore
- Example: `feat(auth): add passwordless login`
- Commit with `git commit -m "<MESSAGE>"`.
(Use the Conventional Commits spec.) 

### 6) Push branch
- `git push -u origin <CURRENT_BRANCH>`

### 7) Open a Pull Request with GitHub CLI
- Use `gh pr create` with:
  - `--base <DEFAULT_BRANCH>`
  - `--title "<auto from commit subject>"`
  - `--body "Automated via Windsurf Workflow. Include checklist, testing notes, screenshots if applicable."`
  - `--draft` if I requested a draft
- After creation, print the PR URL and open it in the browser if I confirm.
- Optionally add labels/assignees if I provided them:
  - `--label "<comma-separated>"`  `--assignee "@me"`

### 8) Post-checks
- Run `gh pr status` and display CI checks if available.
- Offer to:
  - Push follow-ups (same workflow from step 1)
  - Update branch when default changes (`gh pr update-branch` if needed)
  - Merge when green (`gh pr merge --squash` or strategy I choose)

### 9) Summary
Provide a concise summary:
- Branch name
- Commit subject
- PR URL
- Any skipped steps or TODOs