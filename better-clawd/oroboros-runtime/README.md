# Oroboros-Anthropic Claude CLI

Local-first agent CLI, built from the Claude Code fork and rebranded for Oroboros.
Runs your own models through Ollama. No Anthropic account, no cloud key required.

## What it is
- **Command:** `claude-cli`
- **Config:** `%USERPROFILE%\.claude-cli\.claude-cli.json`
- **Body:** Ollama (local), reached through a local provider bridge
- **Providers:** Ollama + HuggingFace are primary. Anthropic is secondary and **dormant** unless a key is entered.
- **Agents:** none enforced. The user drives; every model speaks as itself.

## Architecture
```
claude-cli  (dist/cli.mjs, Anthropic Messages API)
      |
      v  OPENROUTER_BASE_URL -> 127.0.0.1:11499
local provider bridge  (oroboros-runtime/local_providers_shim.py)
      |  translates Anthropic <-> Ollama, carries TOOLS both ways
      v
Ollama  (127.0.0.1:11434)  ->  local models
```
The bridge is **tool-aware**: it forwards `tools[]` to Ollama and converts the
model's tool calls (native `tool_calls`, or `<tool_call>` text from Qwen models)
back into Anthropic `tool_use`, so the CLI actually executes tools.

## Tools and systems (all local)
Connected automatically at launch by `oroboros-runtime/connect_local_mcp.py`,
which handshake-tests each candidate and wires only the live ones:

| Server | Kind | What |
|---|---|---|
| oroboros-cordis-harness | http :8789/mcp | Cordis memory crawler + 27 tools |
| oroboros-tools | stdio | architects_haki, worldfeed_search/feeds/datetime, q3_status, q7_status, tor_status, live_systems, mcp_servers |
| orca-bridge | stdio | Orca CLI control |
| ollama-mcp-bridge | stdio | Ollama (+ Q3 node) |
| oroboros-bridge | stdio | Oroboros core bridge |
| oroboros-synthesizer | stdio | Oroboros synthesizer |

Built-in tools always available: **Bash, Edit, Read, Write, Glob, Grep**.

The bridge also injects a **TOOL ADVERTISEMENT** into every system prompt, so
the model in the control seat sees its tools the moment it starts.

## Run
```
J:\start_claude_cli.bat          (normal)
J:\start_claude_cli_admin.bat    (elevated, for system testing)
```
or, from any shell:
```
claude-cli
```
The launcher starts the provider bridge if needed, wires local MCP adaptively,
and passes `--dangerously-skip-permissions` so tools execute without prompts.

## Adaptive
On any machine, `connect_local_mcp.py` probes each candidate (HTTP + stdio
handshake) and connects only what is present. Nothing is assumed; a service
that is down is skipped, not left dead in the config.

## Models
Undecillion builds (fable7 / fable5 / opus9, Qwen2.5-based, tool-capable) plus
Claude 7. Pick with `/model`. Tool-capable models can be listed with `/models`.

Crown 1272 Hz. Local and sovereign. No telemetry.
