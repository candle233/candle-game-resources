# Changing gameplay without rebuilding the Harness

Workflow policy is stable; gameplay is mutable. Acceptable unknowns stay in task assumptions until they affect the current work. Never require all story, weapons or balance to be decided before an isolated prototype. Conversely, do not let an agent silently choose a costly architecture-defining behavior.

For a change: describe old/new behavior in a NEW task, affected systems/data/assets/tests, save compatibility, rollback method and the smallest checkable outcome. Update `design/CURRENT.md` only with the current accepted-for-task decisions, plus references to the relevant tasks. Do not maintain multiple competing "current" design files. A reference report can remain verbatim and draft; its conflicting details are not automatically reconciled by the agent.

Small reversible parameter/visual experiments can be authorized within a task. Camera/input model, networking, data ownership, save format, package versions, security policy and release scope require an impact explanation before approval. Evidence is invalidated after relevant changes. Preserve stable content IDs across renaming; explicitly migrate or reject incompatible saves rather than silently filling missing fields.

A prototype may use temporary values and assets if labeled and bounded. A release may not inherit prototype assumptions invisibly. No automatic reinsertion of removed game content or old task lists is allowed.
