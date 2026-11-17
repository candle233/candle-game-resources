# Tasks
Create task JSON with `python -I harness/scripts/workflow.py new --id TASK-001 --kind setup --title "Validate the local development environment"`.
There are no preloaded game tasks. `scope`, `acceptance` and `plan` must be filled before readiness. Use concrete relative paths, not the whole repository. All task state is in one JSON per task; `HANDOFF.md` is a generated summary, not a second truth source.
Human-review commands record an operator attestation. They do not authenticate the operator or replace external branch/environment controls. Logs live under `Artifacts/`; retain important evidence before deleting it. Commands will refuse completion if referenced evidence disappears.
