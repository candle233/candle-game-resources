---
name: unity-implementation
description: Implement Unity features, prototypes, bugs, refactors, scenes or UI within an approved task; use for C#, scene, Prefab and gameplay edits.
---

# Unity Implementation

Inspect the actual project and approved task before editing. Read docs/ENVIRONMENT.md, docs/QUALITY.md and relevant current design. For bugs, preserve a repro and failing test first. For prototypes, label temporary data/assets. Preserve GUIDs, package versions and user edits. Keep definitions, run state and persistent state separate; do not impose a new framework. Implement feature-specific tests, inspect diff, then use unity-verification. Treat unresolved future design as unrelated unless the task depends on it.

Use repository-relative commands from the project root. This skill requires the accompanying project Harness files; it is not a standalone game generator.
