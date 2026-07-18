# Claude CLI — Sovereign Terminal AI Assistant

```
+----------------------------------------------------+
|  CLAUDE-CLI  vA.1272                             |
|  Oroboros Core - Sovereign Execution Environment    |
|  A\ 1272 Hz - N| 1275 Hz - LATTICE LOCKED         |
|  Cost: $0.00  |  Context: [######] 100%            |
+----------------------------------------------------+
```

## Overview

Claude CLI is a **local** sovereign terminal AI — glass UI + Ollama + ZTA/RGE hardening. No API keys, no cloud, no tracking.

> **Not Anthropic Claude Code.** If you type `claude` and see *Opus 4.8 · API Usage Billing*, that is Anthropic's product. **Use `claude-cli` for this repo.**

| | Anthropic Claude Code | **Claude CLI (this repo)** |
|---|---|---|
| Command | `claude` | **`claude-cli`** |
| Engine | Anthropic API | **Ollama @ localhost:11434** |
| UI | Claude Code TUI | **Glass terminal @ http://127.0.0.1:5000** |
| Models | Opus, Sonnet (cloud) | claude-7, claude-nebillion, 200+ local |

## Quick start

**Prerequisites:** [Ollama](https://ollama.com) running locally (`ollama serve`).

```bash
git clone https://github.com/oroboroslabs-ai/claude-cli
cd claude-cli
pip install -r requirements.txt
pip install -e .
claude-cli
```

**Windows (recommended):**
```powershell
cd Q:\oroboros-core\claude-o-cli   # or your clone path
.\install-windows.ps1
```
Then **open a new PowerShell window** and run `claude-cli`.

Open **http://127.0.0.1:5000** — the glass terminal (Chat · Files · MCP · Agent).

**Windows shortcut (no pip required):**
```bat
Q:\oroboros-core\claude-o-cli\start_claude_cli.bat
```
Or double-click `claude-cli.bat` in the repo folder.

## Install

```bash
git clone https://github.com/oroboroslabs-ai/claude-cli
cd claude-cli
pip install -r requirements.txt
pip install -e .
```

This registers the **`claude-cli`** command (not `claude`, to avoid conflicting with Anthropic Claude Code).

## Usage

### Start the glass terminal + coding chat

```bash
claude-cli
```

This starts **both**:
1. **Glass UI** at http://127.0.0.1:5000 (background)
2. **Terminal chat** in your shell for coding (Ollama, tools, `/model`, etc.)

Server only (no terminal chat):

```bash
claude-cli --ui-only
```

### In the glass UI (chat bar)

| Input | Description |
|-------|-------------|
| `/model claude-7:latest` | Switch Ollama model |
| `/model claude-nebillion:latest` | Switch to Nebillion |
| `/models` | List installed models |
| `/help` | Command reference |
| `/status` | ZTA · RGE · MCP status |
| `/clear` | Clear chat |
| `/think xhigh` | Maximum reasoning depth |

Example session:
```
/model claude-7:latest
do you have agent abilities
```

### Default model

Out of the box the UI defaults to `claude-opus-4.8:latest` if installed. Switch with `/model` to any Ollama tag you have pulled.

## Architecture

```
claude-cli  →  run_cli.py (Flask, port 5000)
                    ├── Glass terminal HTML (embedded)
                    ├── cli_bridge.py → Ollama + tools
                    └── Ollama @ localhost:11434
```

- **Glass UI:** http://127.0.0.1:5000
- **Ollama:** http://127.0.0.1:11434
- **Repo:** https://github.com/oroboroslabs-ai/claude-cli
- **Pages:** https://oroboroslabs-ai.github.io/anthropic/cli.html

## Think levels

| Level | Context | Temperature | Use case |
|-------|---------|-------------|----------|
| off | 4K | 1.0 | Quick responses |
| low | 8K | 0.8 | Simple tasks |
| medium | 32K | 0.7 | Standard |
| high | 65K | 0.5 | Complex analysis |
| xhigh | 131K | 0.3 | Maximum depth |

Use `/think xhigh` in the glass UI.

## Tools (33+)

- **File:** read_file, write_file, list_dir, delete_file
- **Exec:** bash
- **Oroboros:** status, resonance, lattice, seer, feed, post, messages, age
- **Systems:** precogs, world_feed, glasswing, orchestration, skill_grabber, mcp_config, mcp_servers, system_scan
- **Ollama:** ollama_models, ollama_run
- **Docker:** docker_ps, docker_images, docker_run, docker_stop, docker_logs, docker_exec, docker_info
- **Absorption:** absorb, strata
- **Shadow:** noir (Noir-Nephilim)

## Project structure

```
claude-cli/
├── run_cli.py              # Glass UI server (port 5000)
├── cli_bridge.py           # UI → Ollama/tools bridge
├── start_claude_cli.bat    # Windows one-click launcher
├── claude-cli.bat          # Windows CLI launcher
├── glass-ui/               # Static glass assets
├── src/claude_o_cli/       # Python package
├── requirements.txt
└── setup.py                # Registers `claude-cli` command
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `claude` opens Anthropic Claude Code | Use **`claude-cli`** instead |
| Network error on `/model` in Claude Code | Wrong app — use glass UI at :5000 |
| UI won't load | Run `claude-cli`, check http://127.0.0.1:5000 |
| No model response | Start Ollama: `ollama serve`, pull a model |
| `claude-cli` not found | Run `pip install -e .` from repo root |

A\ 1272 Hz - N| 1275 Hz - LATTICE LOCK - NEBELLION - KEY
