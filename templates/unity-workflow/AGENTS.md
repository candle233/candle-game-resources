# Unity Game Development - repository instructions

## Read only the current context
Read `WORKFLOW.md`, `design/CURRENT.md`, and the selected `tasks/<id>.json` before editing. Consult relevant `docs/` pages, not every file. The task contract defines the current scope. Game mechanics, camera, numbers, names, art direction and progression are mutable inputs, not Harness rules. Do not implement a previous conversation, archived plan or a draft reference by default.

## Work in small, verifiable changes
Use one task and one active writer per checkout. Inspect existing code and user changes first. Prefer the established engine, package versions and architecture; do not upgrade or replace them without approval. State assumptions for the current task, not for the entire game. An unresolved future mechanic only blocks tasks depending on it. A reversible prototype assumption may proceed when authorized and explicitly recorded.

Before implementation, fill objective, concrete path scope, non-goals, assumptions, acceptance, plan, verification gates and review requirements. The operator's approval is recorded with `workflow.py ready`; never fabricate approval. When scope changes, obtain new approval and invalidate old evidence. No broad rewrites outside the task.

## Unity engineering
Keep definitions separate from mutable run state and persistent player data. Pick one source of truth for authoring data per feature; do not maintain unsynchronized JSON and ScriptableObjects. Preserve Unity GUIDs and `.meta` files; move assets through Unity when possible. Do not hand-rebuild scenes/Prefabs or delete Library/Temp to hide a bug. New imports can create `.meta` files: complete initial import, review them, and establish a Git baseline before verification. Do not run two Editors on one checkout. Serialize writes to scenes, Prefabs and project settings; use separate branches/worktrees for independent code tasks, each with its own Library.

## Tools and assets
For asset tasks, prefer an authorized local Eagle search when available. If Eagle is absent or not authorized, record that limitation and create a local TODO instead of pretending it was searched. Then use only reviewed search/generation tools listed in `harness/integrations.json`. Those entries are candidates, NOT installed MCP servers. Never invent package executables or silently enable a plugin. Unknown license means not cleared for shipping. Save inadequate/missing-asset prompts to local `todo/assets/`; attempt Eagle synchronization only when authorized. Keep failures and uncertain submissions visible. Do not write directly into Eagle's library database or upload a private library wholesale.

## Verification and review
Run the task's real gates. A zero-test run, missing XML, stale log, unavailable Editor or mocked Unity run is not a Unity PASS. Bundled connectivity tests are not feature acceptance tests. Add behavior-specific tests and preserve repro evidence before fixing a bug. Never delete a test, weaken an assertion, change acceptance or replace a visual baseline just to make checks pass.

Use `workflow.py verify` to bind reports to the task spec and current file fingerprint. Make at most the configured number of purposeful verification attempts; on exhaustion record the blocker instead of looping. After a pass, require the task's human review(s); use actual in-game evidence for gameplay/art/performance claims. The operator records reviews. The CLI is an audit aid, not authentication: enforce final approval with protected branches/environments or a separate operator account.

## Security and budgets
Default: local workspace writes and approved tools only. Ask before network egress, billable generation, dependency/engine changes, publishing, external uploads, secrets access, filesystem deletion or Git history rewriting. Model authentication stays in the user's client; do not place API keys in this repo. Shell sandbox settings do not automatically constrain every MCP/service. Hooks are lightweight best-effort guardrails, not a complete sandbox or CI replacement. Never bypass approvals or disable quality gates to complete a task.

## Handoff
Record changed files, accepted assumptions, commands actually run, evidence paths, missing checks and blockers. Keep `tasks/<id>.json` authoritative. Generate `tasks/HANDOFF.md` before handing over or compacting context. Do not save internal reasoning, transcripts or credentials in handoff files. Report a blocked task honestly rather than labeling it complete.
