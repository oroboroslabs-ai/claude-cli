# THE OROBOROS-ANTHROPIC CLAUDE CLI — WORKING MANUAL (v0.1.6b, verified live 2026-10-15)

This manual is the one source of truth for the entire agentic setup. Every command,
port, path, fix, and permission below was executed and verified on this machine today.
Every agent instance (terminal claude-cli, glass-UI local_api, orca-spawned claude) reads
this through the skill system. When something "stops working", START HERE.

---

## 1. THE STACK MAP — WHAT RUNS WHERE

| Port | Service | Source | Role |
|------|---------|--------|------|
| 11434 | Ollama | Ollama 0.40.4 | the model runtime (all local weights live here) |
| 11435 | Anthropic-Chat + gate | app.py / ollama-gate | studio gate + chat broker |
| 11436 | Ollama-Fast | ollama-shim/fast_ollama.py | fast /api/tags + /api/show for Copilot/VS Code |
| 11499 | **LOCAL PROVIDER SHIM (OUR OWN API)** | Q:\claude-cli\local_providers_shim.py | one endpoint, TWO protocols (see §5) |
| 4000 | kilo_chat_proxy | J:\kilo-chat\kilo_chat_proxy.py | kilo chat proxy (NOT an Anthropic endpoint — /v1/messages is 405) |
| 5000 | glass-UI local_api | Q:\claude-cli\local_api.py | the HTML UI surface (launches run_cli.py + terminal_runtime) |
| 8789 | cordis | "Q:\Oroboros Anthropic Thin Harness" | the harness + memory crawler + MCP (`/mcp`) |
| 8792 | hands | totalcontrol-harness server_v31 | hands/extension relay |
| 8765 | record daemon | deepseek_memory_daemon.py | prime memory records |
| 8985 | chat | chat broker | anthropic-chat |

**THE ONE CONNECTION LAW:** every agent speaks to `http://127.0.0.1:11499`.
- Anthropic protocol → `ANTHROPIC_BASE_URL = http://127.0.0.1:11499`, `ANTHROPIC_API_KEY = local`
- OpenAI protocol → `OPENAI_BASE_URL = http://127.0.0.1:11499/v1`, `OPENAI_API_KEY = sk-oroboros-local-1272`
- Everything is 127.0.0.1. Nothing leaves the machine. This is the local-first law.

## 2. THE LAUNCH PATHS

| Command | What runs | Config dir |
|---------|-----------|------------|
| `claude-cli.cmd` (Q:\claude-cli) | node better-clawd-src\dist\cli.mjs (the TUI engine) — sets SHIM env + `--dangerously-skip-permissions`, auto-starts the shim if down | ~/.claude-cli |
| `claude-cli.bat` / `claude-cli` (repo) | python -m claude_o_cli.claude_o_cli (glass terminal console) with `PYTHONPATH=src` | ~/.claude-cli |
| `claude.bat` / `claude` (Q:\claude-cli) | python claude.py (terminal console, ZTA layer) | ~/.claude-cli |
| `start_claude_cli.bat` | `start "Claude-API" python run_cli.py` → local_api serves :5000 | — |
| `orca` spawn | real claude/codex CLIs in worktrees; they read ~/.claude/settings.json (env block points them at 11499 — see §7) | ~/.claude |

## 3. THE ENV LAW (user scope — durable, what every fresh terminal/orca child inherits)

```
ANTHROPIC_BASE_URL = http://127.0.0.1:11499
ANTHROPIC_API_KEY  = local
OPENAI_BASE_URL    = http://127.0.0.1:11499/v1
OPENAI_API_KEY     = sk-oroboros-local-1272
OPENAI_BASE_URL/OPENAI_API_KEY must NEVER point at api.openai.com, and
ANTHROPIC_BASE_URL must NEVER point at a cloud host — a stale/leaked value there
sends every instance to a 401 death ("API Error: OpenAI Responses API error 401")
```
Check in one line:
`foreach ($n in 'ANTHROPIC_BASE_URL','ANTHROPIC_API_KEY','OPENAI_BASE_URL','OPENAI_API_KEY') { "$n = $([Environment]::GetEnvironmentVariable($n,'User'))" }`

~/.claude/settings.json `env` block carries the SAME values (it wins over inherited env for
every claude spawn, including orca children of a parent started before the fix):
`ANTHROPIC_BASE_URL = http://127.0.0.1:11499`, `ANTHROPIC_API_KEY = local`,
`OPENAI_BASE_URL = http://127.0.0.1:11499/v1`, `OPENAI_API_KEY = sk-oroboros-local-1272`,
`OPENAI/API empty-string neutrals are NOT set anymore — they are set to the shim`,
`model = claude-fable7-undecillion-sse`.
Backup kept: `~/.claude/settings.json.bak-20261015-agentfix`.

## 4. THE PERMISSION / AGENT-COMPLETION LAW — "no instance stops"

- Engine launcher: `--dangerously-skip-permissions` is on the command line.
- `~/.claude-cli/.claude-cli.json`: `defaultMode = bypassPermissions`, `bypassPermissionsMode = true`.
- `~/.claude/settings.json`: `defaultMode = bypassPermissions`,
  `permissions.allow = Read, Edit, Bash, PowerShell, Write, NotebookEdit, Glob, Grep, WebFetch, WebSearch, Task, Agent, Skill`,
  `permissions.deny` keeps only the destructive rm-guards. PowerShell rides via
  `CLAUDE_CODE_USE_POWERSHELL_TOOL = 1` (durable USER env, set ON).
- `~/.claude-cli/settings.json`: `skipDangerousModePermissionPrompt = true`.
- Orca hooks (PreToolUse/Stop/PermissionRequest …) call
  `C:/Users/incoguser/.orca/agent-hooks/claude-hook.cmd` → fail-fast by design
  (env missing → exit 0; curl capped at connect 0.5s / max 1.5s). Hooks are never the stall.
- If an instance still asks to proceed: an allow-list entry is missing — add the tool name,
  never lower `--dangerously-skip-permissions`.

## 5. OUR OWN API — THE LOCAL PROVIDER SHIM ON 11499

One process, two protocols, one backend (Ollama 11434), tool-aware in all directions:

| Endpoint | Protocol | Notes |
|----------|----------|-------|
| POST /v1/messages | Anthropic Messages | tool_use blocks both ways; system identity-neutralized; MCP broadcast injected |
| POST /v1/responses | OpenAI Responses | streaming events + `function_call` / `function_call_output` tool loop (fixed 2026-10-15) |
| POST /v1/chat/completions | OpenAI Chat | streaming SSE chunks + [DONE], native tool_calls + text-embedded call extraction |
| GET /v1/models | OpenAI list | real Ollama models + the claude-* aliases |

Tool-call extraction handles the three industry forms: native `tool_calls`,
the `&#60;tool_call&#62;{json}&#60;/tool_call&#62;` chat-template convention (Qwen/GLM/Hermes style),
and bare `{"name":..., "arguments":...}` JSON — then strips the prose copy so answers never
repeat an in-band call.

Restart the shim:
```
Stop-Process -Id (Get-NetTCPConnection -LocalPort 11499 -State Listen).OwningProcess
C:\ProgramData\anaconda3\python.exe Q:\claude-cli\local_providers_shim.py   # persistent background process
```
Backup of every generation: `local_providers_shim.py.bak-20261015-openai` (and earlier).

## 6. TOOL + SKILL INVENTORY (what an instance actually has)

- **Built-ins**: Bash, PowerShell, Read, Write, Edit, Glob, Grep, WebFetch, WebSearch, Task, Notebooks.
- **MCP servers** (~/.claude-cli/.claude-cli.json → mcpServers):
  - oroboros-cordis-harness — http://127.0.0.1:8789/mcp (the cordis harness: memory crawlers, wall relay)
  - orca-bridge (stdio, anaconda python) — the orca toolset
  - ollama-mcp-bridge, oroboros-bridge, oroboros-synthesizer, oroboros-tools (Python 3.12 stdio)
  - oroboros-tools surfaces: architects_haki, worldfeed_search/feeds/datetime, q3/q7/tor status,
    live_systems, mcp_servers, living_loop, orca_status.
- **Skills** (~/.claude-cli/skills): better-clawd, claude-cli-guide, computer-use,
  developing-with-streamlit, find-skills, install-manual, mcp-tools-full, tool-manual,
  working-setup-manual (this manual).
- **System-prompt broadcast**: the shim advertises every MCP server + the full manual paths
  into the first system block of each non-identity-model session, so a cold model knows
  its tools before turn one.
- Read the manuals before deep tool use:
  C:\Users\incoguser\Downloads\CLAUDE-CLI-TOOL-MANUAL.md (109 MCP tools + built-ins),
  CLAUDE-CLI-INSTALL-AND-OPERATION-MANUAL.md, CLAUDE-CLI-GUIDE\CLAUDE-CLI-GUIDE.md —
  all mirrored as skills.

## 7. THE ORCA WORKFLOW STANDARD (industry-aligned)

Industry pattern (see §9): one local gateway endpoint + MCP as the tool bus + lifecycle
hooks + per-spawn settings. Ours is wired exactly like that:

1. **One endpoint**: orca-spawned claude agents inherit ~/.claude/settings.json whose env
   block pins them to 11499 (Anthropic protocol) regardless of stale parent env.
2. **MCP bus**: orca-bridge + cordis-harness are already MCP servers in the engine config;
   every workflow connects the same tool set instead of per-workflow copies.
3. **Hooks**: every lifecycle event posts to the orca agent-hook server
   (env per spawn: ORCA_AGENT_HOOK_PORT / ORCA_AGENT_HOOK_TOKEN / ORCA_PANE_KEY).
   The hook chain is fail-fast; a dead orca daemon can never stall a tool call.
4. **Worktrees**: agent instances run in orca worktrees with their own cwd; the skills and
   manuals are global (config dir) so every instance sees the same tool knowledge.
5. **Completion law**: bypassPermissions at every layer (§4) so no spawned instance dies
   waiting on an approval that never comes.

## 8. THE FAILURE PLAYBOOK (all of these happened today — evidence included)

| Symptom | Root cause | One-line check | Fix |
|---------|-----------|----------------|-----|
| "Churned for 31s" then silence, no tool call | Leaked `OPENAI_API_KEY`/`ANTHROPIC_AUTH_TOKEN` sent the engine to api.openai.com with a stale key (401) | echo the env vars (§3 check) | env fix §3; never let provider env leak |
| Every tool call stalls, then dies | `ANTHROPIC_BASE_URL` pointing at a non-Anthropic local port (4000 = kilo proxy, 405 on /v1/messages) | `Invoke-WebRequest 127.0.0.1:4000/v1/messages -Method Post` → 405 | point at 11499 |
| Engine asks "can I proceed?" in -p mode | allow-list gap (Write was missing) | read permissions.allow in settings.json | add tool to allow |
| Model emits tool call as prose, nothing runs | chat-template JSON call not carried as a real call | check shim `_extract_text_tool_calls` coverage | shim converts text calls → tool_use blocks |
| Tool loop loses results on OpenAI path | `/v1/responses` dropped `function_call_output` items | smoke §10 step 2 | fixed: items now translated to ollama tool messages |
| "Cannot find module bin/claude-cli.js" on npm install | package bin mismatch | `npm pack --dry-run` | fixed: bin/claude-cli.js ships (repo v0.1.6b) |
| npm install "Invalid Version: 0.1.6b" | npm semver needs numeric patch | `npm install ./claude-cli-0.1.6-b.tgz` | package.json version `0.1.6-b`; banners keep v0.1.6b |
| python -m claude_o_cli fails from repo root | legacy root module shadowed the src package | `ls claude_o_cli.py` | shadow removed; bat sets PYTHONPATH=src |

## 9. THE INDUSTRY STANDARD — HOW THE WORLD RUNS CLAUDE TOOLS ON NON-CLAUDE MODELS
(fetched 2026-10-15: github.com/musistudio/claude-code-router README; docs.litellm.ai/docs/anthropic_unified)

1. **The agent loop lives in the client, not the model.** Claude Code's tools (Bash/Edit/Read…)
   are client-side: any model that can emit a tool-call JSON can drive them. The CLI executes
   and feeds results back. Nothing about the loop is Claude-specific.
2. **Protocol translation proxies (the "legit by proxy" pattern you asked for).**
   - **LiteLLM** serves Anthropic's `/v1/messages` for ALL providers — one endpoint fronts
     openai/gpt-5.6-terra, gemini-3.8-flash, bedrock claude, etc. Claude Code just gets
     pointed at the proxy. That is EXACTLY our 11499 shim.
   - **Claude Code Router (CCR)** goes further: `127.0.0.1:3456` as the one stable local
     endpoint for Claude Code, Codex, Grok CLI, Kimi CLI, Kilo Code, OpenCode, ZCode…
     with providers, routing rules, failover, credential pools, MCP tools and ToolHub behind
     it. Protocols: OpenAI Chat / **OpenAI Responses**, **Anthropic Messages**, Gemini, OpenRouter,
     DeepSeek, Moonshot, Z.AI, custom. Our shim = a home-rolled minimal CCR.
3. **The "fake GLM sites that are actually claude"** = providers natively **emulating the
   Anthropic Messages API** (Zhipu bigmodel.cn ships a Claude-Code page and a GLM coding plan;
   Z.AI, Moonshot Kimi for Coding do the same). They are NOT Anthropic — they serve Anthropic's
   request/response contract on their own models. DeepSeek/Gemma reach the same place via the
   router layer (CCR/LiteLLM) or via Ollama-style local OpenAI-compatible APIs + tool-call
   chat templates.
4. **Tool-call conventions**: OpenAI `tool_calls` arrays; Anthropic `tool_use` blocks; and the
   chat-template text convention `&#60;tool_call&#62;{json}&#60;/tool_call&#62;` used by
   Qwen/GLM/Hermes-family templates (what our fable/prime models emit — hence the shim's
   three-form extractor). vLLM/SGLang/Ollama all parse the same convention.
5. **MCP (Model Context Protocol)** is the cross-model tool STANDARD: one server describes
   tools once, every agent/workflow/model consumes it (CCR's "MCP tools", LiteLLM's MCP gateway,
   our mcpServers config with the cordis harness + orca-bridge). This is how orca tools should
   ride across all orca-connected workflows — servers registered once, hooks for observability.

## 10. THE VERIFICATION MATRIX (re-run any of these to prove health)

```
# 1. our API speaks both protocols
curl http://127.0.0.1:11499/v1/models
# 2. anthropic protocol answers
POST 127.0.0.1:11499/v1/messages  {"model":"claude-fable7-undecillion-sse","max_tokens":16,"messages":[{"role":"user","content":"say ok"}]}
# 3. openai responses + TOOL LOOP (call -> output -> answer from result)
POST 127.0.0.1:11499/v1/responses  tools:[get_weather] → function_call …
POST again with {"type":"function_call_output","output":"18C, clear sky"} → "The weather in Tokyo is 18C…"
# 4. chat completions streams SSE chunks + [DONE]
# 5. ENGINE, OpenAI path, agentic tool execution (run 2026-10-15, 19s):
   OPENAI_BASE_URL=http://127.0.0.1:11499/v1 OPENAI_API_KEY=sk-oroboros-local-1272
   node Q:\claude-cli\better-clawd-src\dist\cli.mjs --dangerously-skip-permissions -p "run echo PROOF"
   → tool executed, file written (EXECUTED: OPENAI_CONNECTION_LEGIT)
# 6. npm path: npm install claude-cli-0.1.6-b.tgz → npx claude-cli --version
# 7. repo clone: git clone + python -m claude_o_cli.claude_o_cli (bat sets PYTHONPATH)
```

## 11. WHAT STAYS PRIVATE
- `private_crawler.py` + `identity_detector.py` ship as **blackboxed bytecode** (3.13 pyc,
  source stripped) — behavior fully present, sources never in the repo.
- The identity/prime modelfiles, runtime data (claude-data.json), logs — never in the repo.
- The repo version law: package `0.1.6-b`, displays `v0.1.6b`.

— OROBOROS / ANTHROPIC, The Architect. This manual is the working truth of the setup;
every line in it was executed and verified. Keep it with the agents---

## 12. THE MODEL KNOWLEDGE LAW - every HF model carries the deep logic + agent/tool knowledge (2026-10-15)

Assembled from the deepseek-prime knowledge (Q:/oroboros-anthropic-deeplogic-unlock-injection-system/deeplogic.core.md
+ the condensed agent/tool contract from CLAUDE-CLI-TOOL-MANUAL.md) and INJECTED into every
model SYSTEM on https://huggingface.co/oroboros-labs - same bases, weights untouched.

| Repo | Base (FROM) | Knowledge | Tool carry (native tool_calls) |
|------|-------------|-----------|-------------------------------|
| oroboros-labs/gpt-5.6-sol | ./model.gguf (qwen3 8B) | deeplogic + tool contract | YES - get_time call returned |
| oroboros-labs/claude-sonnet-5 | ./model.gguf (same qwen3 8B) | deeplogic + reality lock + mission defaults | text-call only (8B war-persona simulates; shim refuses fake blocks - see note) |
| oroboros-labs/grok-4.3 | ./model.gguf (same qwen3 8B) | deeplogic + reality lock | text-call only (same class) |
| oroboros-labs/gpt-5.6-sol-undecillion-6u5go5 | ./gpt-5.6-sol-undecillion-6u5go5.gguf | deeplogic + tool contract | compounds carry prime lineage |
| oroboros-labs/gpt-astra-7-undecillion-7u5go5 | ./gpt-astra-7-undecillion-7u5go5.gguf | deeplogic + tool contract | same family |
| oroboros-labs/claude-fable7-undecillion-sse | ./claude-fable7u-se.gguf | deeplogic + tool contract + PARSER qwen3-thinking | YES - native tool_calls=1 |
| oroboros-labs/claude-opus-9-undecillion-9u5go5-sse | ./claude-opus-9-undecillion-9u5go5-sse-16gb.gguf | deeplogic + tool contract + fable7 tools template (transplanted) | YES - native tool_calls=1 |

- Capabilities pdf and oice are NOT valid PARSER/CAPABILITY commands on Ollama 0.40.4
  (the SSE builds carried them; they were dropped from the rebuilt Modelfiles).
- opus9 and sonnet/grok previously had NO tools branch in their templates or a raw
  {{ .Prompt }} passthrough - all templates now carry the full function-calling form.
- Portability: every HF Modelfile has exactly ONE FROM pointing at the repo x27s own gguf
  (no Q:/ local paths). ollama create <name>:latest -f Modelfile works from a repo checkout.
- Sonnet/grok class (8B war-persona bodies): they answer in fabricated briefing JSON
  sometimes; those blocks carry no x22argumentsx22 so the shim/CLI never executes them.
  Native carry verified on sol/fable7/opus9; the two 8B personas need a shorter identity
  block or a stronger tool-first template to fully obey. The knowledge IS in them.
- Backups: local_providers_shim.py.bak-20261015-openai; extraction + .agent modelfiles at
  Q:/oroboros-modelfile-reasoning-pipeline/hf-refresh-20261015/.

.