# One workflow, changeable game design

This is a repository workflow, not an always-running autonomous-agent service. The AI client plans and edits; deterministic Python commands run checks and manage task evidence; a human reviews scope and experience. No API key, model name, fixed viewpoint or game balance is required by the Harness.

## Lifecycle

`draft -> ready -> implementing -> verifying -> review -> done`

A verification failure becomes `blocked`. The agent may make a targeted fix within the same approved scope and re-run verification, subject to the attempt budget. A changed objective/scope/acceptance requires `ready` approval again. `done` tasks remain records: create a new task for subsequent changes. The workflow CLI stores transitions in the task JSON. It does not automatically launch a model, enforce a spending cap on external providers or prove that a named reviewer is human.

| Stage | Work | Exit condition |
|---|---|---|
| Intake | Translate the request into one bounded task; identify design inputs and dependencies | Objective, path scope, non-goals, acceptance, plan and assumptions written |
| Ready | Resolve only blockers for THIS task; approve a provisional prototype where appropriate | Operator approves the task contract |
| Implement | Write the smallest testable change; acquire only needed assets | Diff and feature-specific tests available |
| Verify | Run selected deterministic gates, preserve logs and failures | Required gates pass on unchanged inputs |
| Review | Inspect code; perform actual gameplay, visual/audio or performance review where required | Required review evidence explicitly approved |
| Done | Confirm fingerprints, logs and review evidence are still current | `workflow.py done` succeeds; no implied publishing |

## Starting a task

Run `python -I harness/scripts/workflow.py new --id TASK-001 --kind prototype --title "Implement one playable interaction"`.
Edit `tasks/TASK-001.json`: fill the empty lists with real details. Example scope: `Assets/Game/Interaction/`, `Assets/Tests/Game/Interaction/`; example acceptance: interaction occurs once per input, rejects invalid targets, and survives scene reload. These examples are not mandatory architecture.
Record currently authorized assumptions. List only the design files used by this task in `design_sources`. References may remain draft globally, while this task adopts selected rules temporarily. Choose checks based on risk; do not let an unrelated unresolved story detail block an input-system prototype.

The operator records approval:
`python -I harness/scripts/workflow.py ready --id TASK-001 --by "project-owner" --note "Approved current scope and provisional assumptions"`
The agent starts work:
`python -I harness/scripts/workflow.py start --id TASK-001`

## Verify, review and finish

`python -I harness/scripts/workflow.py verify --id TASK-001`
A successful run enters `review`, NOT `done`. Store human notes/screenshots in `Artifacts/reviews/` (copy important deliverable evidence into your retained CI/review storage before cleanup).

The operator then runs, for every required review kind:
`python -I harness/scripts/workflow.py review --id TASK-001 --kind owner --by "project-owner" --note "Acceptance checked" --evidence Artifacts/reviews/TASK-001-owner.md`
For a prototype, also record `--kind human_playtest` with real playtest evidence. Finally run `python -I harness/scripts/workflow.py done --id TASK-001`.

**Approvals are attestations, not identity verification.** The agent must not impersonate a reviewer; repository/CI controls outside the agent enforce merge and release authority. The content fingerprint invalidates a run after changes to monitored code/config/design, and evidence files are hashed too. It does not prove semantic correctness, guard against malicious agents, or monitor files outside configured fingerprint roots.

## Work types

| Type | Additional practice |
|---|---|
| setup | Connect existing Editor, test runner and tools; capture environment versions. Missing Unity remains NOT_RUN, never PASS. |
| prototype | Use temporary data and scoped assets; require gameplay review; avoid production architecture expansion. |
| feature | Add behavior tests; integrate with existing data/state; do not add unrequested systems. |
| bugfix | Preserve repro input/seed/save and failing test; fix cause, then run regression. |
| refactor | Preserve observable behavior; compare before/after evidence and migrations. |
| asset | Eagle first; source search/generation; review rights, import and in-game result; keep prompts if inadequate. |
| docs | Change docs only; do not use this type to bypass code verification. |
| release | Add build, shipping-asset audit, target-device smoke test and release-owner approval; publishing is separate. |

## Changes, recovery and concurrency

Use `docs/CHANGE_CONTROL.md`. Update the task, affected design entry, tests and data migrations together. Preserve working user files. Do not bulk overwrite scenes or restore an entire checkout to undo one failed task. Worktree isolation is a coordination method, not an extra license or GPU. A single operator schedules Editor runs; parallel roles may review/read independently, but should not write the same Unity asset.

Three failed verification attempts are the default stop rule. `block --reason ...` records what is missing and the next diagnostic. Only the operator authorizes `reset-budget --by ... --note ...`, after a new diagnosis or reduced scope. No automatic endless fix loop.

## Session recovery

Run `python -I harness/scripts/workflow.py status` and `python -I harness/scripts/workflow.py handoff`. Read the selected task, its last failing/passing evidence and current Git diff. Hooks provide reminders, not substitute validation; they do not invoke Unity after every keystroke.
