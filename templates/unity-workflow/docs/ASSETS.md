# Asset production workflow

1. Write a task-scoped brief: use, in-game camera/size, style, technical output, quality/performance requirements, rights and acceptable temporary substitute.
2. When available and authorized, search Eagle first with `python -I harness/scripts/assets.py search --query "..."`. If unavailable or not authorized, record that limitation and retain a local TODO; do not block unrelated code work or claim a search occurred. A library hit still needs source and rights review.
3. If no candidate works, use a reviewed provider from `harness/integrations.json`; exact server identifiers/versions/credentials must be configured by the operator. This catalog is not executable MCP configuration.
4. Stage outside shipping assets. Inspect for unsafe payloads, embedded scripts, excessive texture sizes, incompatible rigs/materials/code and unwanted dependencies.
5. If unsuitable, create a full generation prompt and local TODO, then attempt Eagle sync when authorized. Do not keep requesting paid variations without a cap.
6. Review the returned asset's source rights, technical compatibility, art/audio direction and in-game behavior. Import only accepted files. Register every imported media file (including textures bundled with a model) in `harness/assets/registry.json`.
7. Re-run asset checks after modification; a changed file hash invalidates the previous review. Close the TODO only after final in-game acceptance.

## User-selected routing
Music/SFX: Eagle -> Freesound MCP and/or SoundCraft -> prompt TODO.
3D: Eagle -> arielshad/3d-asset-server and/or local Blender -> prompt TODO.
Images/icons: Eagle -> Lucide / Tabler / Heroicons / Iconify; reviewed Openverse, stock-images or NASA connectors; image generation, VectorCraft or PhotoCraft -> prompt TODO.
VFX: Eagle -> reviewed Pixabay/VFX connectors or generated images assembled into suitable effects; prefer actual Unity particles/shaders/VFX/flipbooks for interactive effects. A rendered video is not automatically a real-time game effect.

Routing order is a preference, not automatic execution. Do not assume a tool named in a list is installed, trustworthy, commercially usable or capable of a particular operation. A software repository license does not license assets returned by that tool. Free download, public web access and AI generation are not automatic clearance; record the actual terms and review. Keep attribution/credits when required. The checker validates record completeness and hashes, not legal truth.

## Prompt TODO example
Save the full prompt in `todo/music-prompt.txt`, then:

```powershell
py -3 -I harness/scripts/assets.py todo --type music --name "combat-loop" --brief "Loop for the currently approved combat prototype" --prompt-file todo/music-prompt.txt --try-eagle
```

The local JSON/Markdown/SVG exist even if Eagle fails. The SVG is a text prompt card, not finished artwork. Full text is kept in the Eagle annotation. `sync --id <printed-id>` reconciles an existing item by its unique name before upload. A timed-out write becomes `uncertain`; do not reset this status until a human checks Eagle. The bridge requires the SAME host filesystem as Eagle's addFromPath API; a remote server cannot submit an unrelated local path. No direct database/library-file edits occur.

## Asset record example (replace with real values)
See `harness/templates/asset-record.json`. `evidence_file` points to a saved license/rights-review document inside the repo. `reviewer` is an operator attestation, not cryptographic identity. `prototype_only` assets may pass non-release checks but cannot pass the release audit. A task using `assets` runs the strict shipping audit by default; temporary placeholder tasks should retain an explicit non-shipping review and not claim asset production is finished.

No automatic uploader, paid generator or external model is installed by this package. Costs and credentials are handled through the selected provider/client. To return final results to Eagle, use an explicitly approved importer/API operation and record its item ID; prompt-card sync does not import the final game asset by itself.
