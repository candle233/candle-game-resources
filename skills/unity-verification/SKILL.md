---
name: unity-verification
description: Verify Unity changes with compile, EditMode, PlayMode, build and evidence checks; use before review or whenever tests fail.
---

# Unity Verification

Read docs/QUALITY.md. Run workflow.py verify for the selected task. Inspect actual logs and nonzero test results, not only an exit code. Recognize that HarnessConnectivity tests are not feature tests. Verify specific behaviors and collect in-game evidence for human review. On failure preserve evidence and diagnose within the attempt budget. Never weaken tests or acceptance to pass. Missing Editor, missing output and mocked execution are not Unity success.

Use repository-relative commands from the project root. This skill requires the accompanying project Harness files; it is not a standalone game generator.
