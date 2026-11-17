# Permissions and responsibilities

| Operation | Default | Approval / evidence |
|---|---|---|
| Read project text and tests | Allowed within the workspace | Respect private data and task scope |
| Edit scoped C# / tests / docs | Allowed after readiness | Review diff; preserve user changes |
| Start Unity | One process per checkout | Matching license/Editor; no interactive lock |
| Read Eagle local API | Ask when not already authorized | Minimal query; no raw private library dump |
| Add prompt card to Eagle | Explicit authorized task / `--try-eagle` | API success plus lookup confirmation |
| Download asset / call MCP | Not enabled by this package | Review exact server, version, tools, network destination and source rights |
| Billable model/art/audio generation | Off until budget approval | Set provider-side cap; record actual receipts; no invented token accounting |
| Blender/editor scripting | Ask for new write/exec capability | Do not load untrusted embedded scripts or enable auto-run |
| Engine/package/render-pipeline change | Ask | Explain compatibility and migration impact |
| Delete files / rewrite Git history | Denied to autonomous execution | Operator performs narrowly approved maintenance |
| Publish build / upload source / deploy | Separate explicit approval | Build provenance, rights, playtest and rollback checked |
| Read/use secrets | Not in repo | Client credential store or narrowly scoped environment |

Only selected Codex guards are machine-enforced locally. Narrative rules are workflow contracts, not access-control lists. ZCode requires native safety configuration. Review attestations are editable local records; protected branches/environments and separate human control must enforce actual authority. Never run untrusted pull-request code on a privileged Unity runner. Do not give an untrusted MCP a broad home-directory mount.
