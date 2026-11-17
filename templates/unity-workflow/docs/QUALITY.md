# Risk-based verification

Mandatory gate types are `check`, `python`, `compile`, `editmode`, `playmode`, `build`, `assets`. The CLI rejects code tasks lacking compilation and both Unity test modes. A text-only request uses `docs`; do not mislabel code as docs to bypass gates. Any gate waiver must be a reviewed change to workflow policy, not a hidden task edit.

A passing run must have current input/spec fingerprints, fresh command logs, successful exits, and nonzero passing Unity tests where applicable. Skipped tests are reported and must be reviewed; an acceptance criterion cannot rely on a skipped test. Bundled connectivity tests prove runner wiring only. Implement actual feature tests, add their names to the review evidence, and inspect that they ran.

Gameplay, art, audio, accessibility and performance require appropriate in-game/target-device observations. Test scripts cannot certify fun or production rights. Record build id/commit, device, settings, seed/save, input sequence, expected/observed outcomes and screenshots/logs. Disable sensitive logging by default. For visual regression, fix camera, resolution, lighting, seed and relevant timing; approve baseline changes explicitly. For performance, define a reference device, frame-time metric, percentile, load and memory limit before measuring. Do not claim Editor timings are shipped-player timings.

Save/load tasks require interrupted-write and migration tests. Randomized systems require seed provenance, fixed-input tests and distinct random streams when unrelated systems should not perturb each other. Do not promise cross-platform bitwise physics determinism without measuring it. Scene tests must cover missing references and blocked progression. Release also requires an executable launch/smoke check, approved assets/credits, human playtest and release-owner attestation. The built-in build command does not launch or publish the game.

## Test evidence locations
Task runs: `Artifacts/harness/tasks/<task>/<run>/`.
Unity runs: `Artifacts/harness/unity/<run>/`.
Review evidence: `Artifacts/reviews/` or a reviewed retained storage location mirrored locally.
Do not delete evidence until the task/release record is archived elsewhere. An unavailable tool produces NOT_RUN/blocked, never success. Mock-process tests in this package validate Harness behavior only.
