# Resource repository instructions

This is the reusable resource repository, not a Unity game checkout. Maintain canonical Skills in `skills/`, project files in `templates/unity-workflow/`, and third-party provenance in `catalog/resources.json` and `THIRD_PARTY_NOTICES.md`. Do not run game tasks against this repository or copy game state into templates.

Read the current request, existing files and relevant docs before editing. Preserve local changes. Keep Python tools standard-library-only, isolated (`python -I`), create-only and dry-run by default. Do not modify global client settings, enable MCP servers, download dependencies, publish or push without separate authorization.

Third-party references are candidates, not installed dependencies. Never infer package executables or licenses from names. When copying upstream content, record exact source/version and preserve license/NOTICE/copyright. The supplied original framework has no identified license; `docs/LICENSING.md` describes the unresolved redistribution prerequisite. A clean structure check is not permission to publish.

After changing templates or Skills, regenerate `MANIFEST.json`, run `tools/resources.py verify`, both offline test suites and reproducible Skill packaging. Never label mocks as Unity, Eagle, native client or MCP runtime acceptance. Report real results and gaps. `dist/`, credentials, local client fragments and game artifacts stay out of Git.
