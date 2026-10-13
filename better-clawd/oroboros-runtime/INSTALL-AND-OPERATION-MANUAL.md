# Oroboros-Anthropic Claude CLI — INSTALL & OPERATION MANUAL
### Full process, beginning to end. Local-first. No cloud key required.

---

## 1. What this is
A local agent CLI (built from the Claude Code fork, rebranded) that runs your own
models through Ollama. It speaks the Anthropic Messages API and reaches Ollama
through a local bridge, so it uses local models with no Anthropic/OpenAI account.

- Command: `claude-cli`
- Config: `%USERPROFILE%\.claude-cli\.claude-cli.json`
- Runtime: `Q:\claude-cli`
- Repo (fork): `Q:\claude-cli\better-clawd-src`
- Brand mark: flipped-horizontal A (∀)

---

## 2. Prerequisites
- Windows, Node.js, `bun` (build tool), Python 3.11+
- Ollama running on `127.0.0.1:11434`
- Local models (see §6)

---

## 3. Install / build (from source)
```
git clone <your-fork> Q:\claude-cli\better-clawd-src
cd Q:\claude-cli\better-clawd-src
bun install
bun run build        # -> dist/cli.mjs
```
The runtime support files live in `oroboros-runtime\` (bridge, MCP connector,
tools server, launchers, manual).

---

## 4. Launch
Normal:
```
J:\start_claude_cli.bat
```
Elevated (for system testing):
```
J:\start_claude_cli_admin.bat
```
Or, from any shell (bridge must be running):
```
claude-cli
```
The launcher: starts the provider bridge if down → wires local MCP adaptively →
runs the CLI with `--dangerously-skip-permissions`.

---

## 5. Providers
| Provider | Default | Needs key | Notes |
|---|---|---|---|
| Ollama | primary | no | local; reached via the bridge |
| HuggingFace | primary | `HF_TOKEN` | dormant without a token |
| Anthropic | secondary | `ANTHROPIC_API_KEY` | dormant unless a key is entered |

The bridge (`local_providers_shim.py`, `127.0.0.1:11499`) translates Anthropic
<-> Ollama and carries tools both ways.

---

## 6. Models
- Orchestrator: **Claude 7** (`claude-7:1gb`). Holds the floor until a model is entered.
- Tool-capable local models (reliable agent tools): `oroboros-labs/claude-fable7-undecillion-sse`,
  `oroboros-labs/claude-opus-9-undecillion-sse`, `qwen2.5:14b`, `llama3.2:latest`.
- DeepSeek: `deepseek-prime-cl-1q5duo5:latest` / `:compounded`.
Pick with `/model`; list with `/models`. The picker is restricted to
undecillion + DeepSeek by `availableModels` in the config.

---

## 7. Orchestrator / hand-off
- Claude 7 holds the floor by default and introduces/orchestrates the CLI.
- Entering any model (`/model <name>`) hands control to it entirely: it answers AS
  ITSELF. Claude 7 never wraps, renames, or impersonates it.
- No agent is enforced.

---

## 8. Tools & MCP
Connected adaptively at launch by `oroboros-runtime/connect_local_mcp.py`, which
handshake-tests each candidate and wires only live ones:
- oroboros-cordis-harness (http :8789/mcp)
- oroboros-tools (stdio) — architects_haki, worldfeed_search/feeds/datetime,
  q3_status, q7_status, tor_status, live_systems, mcp_servers, living_loop, orca_status
- orca-bridge, ollama-mcp-bridge, oroboros-bridge, oroboros-synthesizer
Built-in tools: Bash, Edit, Read, Write, Glob, Grep, TodoWrite, Task, WebFetch, NotebookEdit.

Manual: `CLAUDE-CLI-TOOL-MANUAL.md` (Downloads) and
`~/.claude-cli/skills/tool-manual/SKILL.md`.

---

## 9. HOW TO CALL A TOOL (the important part)
The bridge advertises tools and executes calls. A model must EMIT a call, not
describe it. Accepted call forms (the bridge parses all of these):
```
{"name": "Read", "arguments": {"file_path": "Q:\\path\\file.txt"}}
```
```
<tool_call>{"name": "Bash", "arguments": {"command": "ls"}}</tool_call>
```
```
```json
{"name": "Bash", "arguments": {"command": "start chrome"}}
```
```
DO NOT write prose like `Bash start chrome https://youtube.com` — that is not a
call and nothing executes. The bridge injects this rule into every system prompt.

---

## 10. Branding / themes
Two themes, switchable via `/theme`:
- **Oroboros · Black & White** (`oroboros-mono`) — DEFAULT.
- **Oroboros · Red-Orange / Anthropic orange on Black** (`dark`).
Logo: the normal little-guy mascot (orange in color themes, white in B&W).

---

## 11. Orca integration
`orca-data.json` `customAgentCommand` and `agentCmdOverrides` all point to
`claude-cli`, so every Orca agent launches this CLI. Restart Orca after changes.
For elevation, launch from `J:\start_claude_cli_admin.bat` or run Orca elevated
(Orca runs terminals under a persistent daemon, so the daemon must be elevated).

---

## 12. Repo / push
```
cd Q:\claude-cli\better-clawd-src
git remote set-url origin <your-repo>
git push -u origin main
```

---

## 13. Troubleshooting
- **ECONNREFUSED** — the bridge is down; run `python Q:\claude-cli\local_providers_shim.py`
  or the launcher (which starts it).
- **"Bash start chrome…" in the reply, nothing happens** — the model narrated
  instead of emitting a call. Use a tool-capable model (undecillion/qwen2.5/llama3.2).
  The bridge now also parses `<tool_call>`/fenced-JSON text calls.
- **Model answers as "Claude Code"** — the CLI injects its own system prompt; the
  bridge neutralizes the identity line. Enter your own model to get its identity.
- **Tool asks permission** — launch with `--dangerously-skip-permissions` (launchers do).
- **Orca EPERM / elevation** — run Orca or the admin starter elevated.

Crown 1272 Hz. Local and sovereign. No telemetry.
