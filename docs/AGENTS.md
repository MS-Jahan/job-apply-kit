# Other agents: skills + MCP locations

The kit registers MCP servers for Claude Code and OpenCode
(`install.py`, `docs/EXTERNAL_TOOLS.md` §5); skills themselves stay in this repo
and are read in place. Everything else on this page is
for the other harnesses. Paths below were verified against official docs in
Oct 2026; when a vendor moves things, re-anchor with the fallback query and
update this file. Aggregators worth bookmarking: https://clients.dev and
https://agentskills.io.

Portable trick: most agents below read the shared `.agents/skills/` directory
(Codex, Gemini, Cursor, Amp, Roo, Kilo-compat). Dropping a skill folder there
covers several harnesses at once — but prefer each agent's native location
when you only target one.

| Agent | Skills live in | MCP config file (key) | Manage via CLI | Official docs |
|---|---|---|---|---|
| Claude Code | `~/.claude/skills/` | `~/.claude.json` (`mcpServers`) | `claude mcp add -s user` | https://code.claude.com/docs/en/mcp-servers.md |
| OpenCode | `~/.config/opencode/skills/` | `~/.config/opencode/opencode.json` (`mcp`) | edit JSON | https://opencode.ai/docs/mcp-servers/ |
| Codex CLI | `~/.agents/skills/` (also `.agents/skills/`, `/etc/codex/skills/`) | `~/.codex/config.toml` (`[mcp_servers.*]`) | `codex mcp` | https://developers.openai.com/codex |
| Gemini CLI | `~/.gemini/skills/` or `~/.agents/skills/` | `~/.gemini/settings.json` (`mcpServers`) | `gemini mcp add --scope user` | https://github.com/google-gemini/gemini-cli/blob/main/docs/tools/mcp-server.md |
| Kilo Code | `.kilo/skills/`, `skills.paths`/`skills.urls` in `kilo.jsonc` | `kilo.jsonc` (`mcp`): global `~/.config/kilo/kilo.jsonc`, project `kilo.jsonc` | `kilo mcp add` | https://kilo.ai/docs |
| Cline | `~/.cline/data/skills/`, `.cline/skills/` | CLI: `~/.cline/data/settings/cline_mcp_settings.json` (`mcpServers`) | `cline config mcp` | https://docs.cline.bot/mcp/mcp-overview |
| Roo Code | `.roo/skills/`, `.agents/skills/`, `~/.roo/skills/`, `~/.agents/skills/` | project `.roo/mcp.json`, global `mcp_settings.json` in VS Code globalStorage (`mcpServers`) | settings UI | https://docs.roocode.com |
| Cursor | `.agents/skills/`, `.cursor/skills/`, `~/.agents/skills/`, `~/.cursor/skills/` | `.cursor/mcp.json`, `~/.cursor/mcp.json` (`mcpServers`) | Customize UI | https://cursor.com/docs/mcp |
| Windsurf | `.devin/skills/` (legacy `.windsurf/skills/`), global `~/.codeium/windsurf/skills/` | `~/.codeium/windsurf/mcp_config.json` (`mcpServers`) | MCP panel / raw JSON | https://docs.devin.ai |
| Amp | `.agents/skills/`, `~/.config/agents/skills/`, `~/.agents/skills/`, `~/.config/amp/skills/` | `amp.mcpServers` in `~/.config/amp/settings.json` / `.amp/settings.json` | `amp mcp add` | https://ampcode.com/docs/customize/mcp |
| Aider | — (reads `AGENTS.md`/repo conventions) | experimental: `--mcp-servers` / `--mcp-servers-file` flags on builds that include it | — | https://aider.chat (MCP still PR-stage upstream) |

Notes and traps (read before copying entries between clients):

- **Bare `npx` in an MCP entry depends on the host's PATH.** A client started before a
  Node install/PATH change spawns the server dead (`'npx' is not recognized`, exit 1).
  Prefer the absolute npx path in the entry — with nvm for Windows the shim dir
  (`...\nvm\.nodejs\npx.exe`) is stable across version switches. Diagnosis flow:
  `docs/EXTERNAL_TOOLS.md` §5.1.

- **Windsurf remote URLs use `serverUrl`, not `url`.** A block copied from
  Cursor/Claude with `"url"` parses fine and then silently does nothing.
- **Cline CLI does NOT read `~/.cline/mcp.json`.** Older Cline docs say it
  does; the CLI actually reads
  `~/.cline/data/settings/cline_mcp_settings.json` (overridable with
  `CLINE_MCP_SETTINGS_PATH`). The VS Code extension instead uses
  `.../Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`
  (Roo Code: same shape under `rooveterinaryinc.roo-cline`).
- **Codex MCP:** stdio via `command`/`args`, remote via `url` in
  `[mcp_servers.<name>]`; project `.codex/config.toml` only loads for trusted
  projects; home dir follows `$CODEX_HOME`. Skills can also be toggled per
  path in config (`skills.config`).
- **Kilo Code** reads the same `kilo.jsonc` from CLI, VS Code, and JetBrains;
  its settings UI edits the file for you, and it can one-time import
  `~/.claude/skills/` plus top-level `~/.claude.json` servers (disabled until
  enabled).
- **Amp** prefers MCP servers bundled inside skills (`mcp.json` in the skill
  folder, loaded only when the skill runs) over always-on user settings; it
  also reads `~/.claude/skills/` for compatibility.
- **Cursor** also reads `.claude/skills/` and `.codex/skills/`; nested
  `.cursor/skills/` dirs scope skills to that subtree.
- **Aider** has no stable MCP/skills surface: MCP exists only in unmerged
  upstream PRs. Treat any Aider MCP instructions you find online as
  version-specific until aider.chat documents it.

Copying this kit's chrome-devtools entry elsewhere: the canonical definition
is `mcp/servers.json` in this repo. Claude-shaped clients take
`command` + `args` verbatim; TOML clients (Codex) need it as
`command = "npx"` plus `args = [...]`; OpenCode needs the `command: [...]`
array form — see `docs/EXTERNAL_TOOLS.md` §5 for all three shapes.
