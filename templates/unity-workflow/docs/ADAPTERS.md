# Client adapters

## Codex
The root `AGENTS.md`, `.agents/skills/`, `.codex/config.toml`, `.codex/hooks.json` and `.codex/rules/safety.rules` are native mechanisms, not an invented omnibus YAML. The project must be trusted. Review exact Hooks with `/hooks`; changed definitions require review again. The configuration inherits the user's model/auth, uses workspace-write and on-request approval, and disables sandboxed shell networking by default.

Hooks locate the Git root before importing `harness/scripts/hooks.py`. Native Windows uses `py -3 -I`; POSIX uses `python3 -I`. Confirm these commands resolve to Python 3.11+. Network-denied shell work includes the Eagle loopback request on some hosts; authorize the narrow local API operation through your client/OS rather than turning off all protections. MCP/services have their own permissions; a sandbox flag is not universal egress control.

## ZCode
Open the same project root, use root `AGENTS.md`, and import the six Skills from Settings > Skills > Import. Import the project-local .agents/skills copies, not cross-repository symlinks: fingerprinting and installer checks reject symlinked inputs. Their canonical source is candle-game-resources/skills; update through a reviewed resource synchronization. Verify the names are visible and enabled in the current session.

Generate actual machine paths using `python -I harness/scripts/configure.py --adapter zcode`. The output `Artifacts/harness/zcode-user-hooks.json` is a **merge fragment for `~/.zcode/cli/config.json`**, not a project config. Merge `hooks.events` arrays while preserving your existing hooks/settings. The handler returns immediately outside this project. Do not add the same fragment repeatedly, and remove its entries when the project is retired. Start a new session and inspect Settings > Hooks.

ZCode's currently documented project-level Hooks are ignored; this package does not put fake working Hooks into `.zcode/config.json`. Use standard per-operation safety confirmations, not unrestricted auto-execution. ZCode permissions are not a copy of Codex's TOML. Client version differences must be verified locally with a harmless hook test. The package does not mutate user-level configuration automatically.

## Hook behavior
SessionStart injects a short task reminder. PreToolUse blocks selected obvious destructive patterns. PostToolUse reminds the agent to re-verify. Stop provides an advisory status message; it does not launch an expensive Editor process or infinitely block a conversation. The handler writes event name/tool/time only, never command contents or transcripts.

These regular-expression guards do not interpret all shells, indirect scripts, MCP code execution or encoded commands. Native runtime errors can fail open. OS sandboxing, reviewed tools, external approvals and protected CI are the security boundary.
