# Current design input

Status: editable input; no gameplay is frozen by the Harness.

## Active task decisions
No game-specific requirements are pre-approved in this clean package. For the next task, identify the relevant request, selected design source, provisional assumptions and acceptance criteria in `tasks/<id>.json`.

## How to add or replace a design
Place the currently chosen source in `design/inputs/` and describe its role here. Mark it as draft/reference/accepted-for-task, and state which task uses it. A source is not automatically executable authorization. Keep its wording; do not silently reconcile contradictory passages. A task can adopt a reversible assumption without deciding every future mechanic.

## Scope boundary
This file does not select a camera, combat model, day count, growth system, economy, building system, character roster or story. Such decisions belong to design inputs and approved task contracts. The workflow should continue to work after those decisions change.
