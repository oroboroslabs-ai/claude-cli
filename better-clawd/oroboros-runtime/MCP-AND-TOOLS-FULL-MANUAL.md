# MCP & TOOLS — FULL MANUAL (every step, every function)

All tools run LOCALLY on 127.0.0.1. No cloud key. Command: `claude-cli`.

## How a tool call flows (the logic, step by step)
1. The CLI builds a request and includes the `tools[]` schema.
2. The bridge (`:11499`) forwards `tools[]` to Ollama and converts each
   Anthropic tool schema to an Ollama function schema.
3. The model emits a call — natively (`tool_calls`) or as text:
   `{"name":"Tool","arguments":{...}}`, `<tool_call>{...}</tool_call>`,
   or a fenced ```json block. The bridge parses any of these.
4. The bridge returns the call to the CLI as Anthropic `tool_use`.
5. The CLI executes the tool (built-in locally; MCP via its server) and
   sends the result back (`tool_result`) for the next turn.
Never DESCRIBE a call in prose — emit it.

---
## A. Built-in tools (always available)

### `Bash`
Execute a shell command on the host.

| arg | type | required | notes |
|---|---|---|---|
| `command` | string | yes | |
| `timeout` | number | no | |
| `description` | string | no | |

### `Edit`
Exact string replacement in a file.

| arg | type | required | notes |
|---|---|---|---|
| `file_path` | string | yes | |
| `old_string` | string | yes | |
| `new_string` | string | yes | |
| `replace_all` | boolean | no | |

### `Read`
Read a file or directory.

| arg | type | required | notes |
|---|---|---|---|
| `file_path` | string | yes | |
| `offset` | number | no | |
| `limit` | number | no | |

### `Write`
Create or overwrite a file.

| arg | type | required | notes |
|---|---|---|---|
| `file_path` | string | yes | |
| `content` | string | yes | |

### `Glob`
Find files by pattern.

| arg | type | required | notes |
|---|---|---|---|
| `pattern` | string | yes | |
| `path` | string | no | |

### `Grep`
Search file contents by regex.

| arg | type | required | notes |
|---|---|---|---|
| `pattern` | string | yes | |
| `path` | string | no | |
| `include` | string | no | |
| `context` | number | no | |
| `limit` | number | no | |

### `TodoWrite`
Maintain a structured task list.

| arg | type | required | notes |
|---|---|---|---|
| `todos` | array | yes | |

### `Task`
Launch a subagent for multi-step work.

| arg | type | required | notes |
|---|---|---|---|
| `description` | string | yes | |
| `prompt` | string | yes | |
| `subagent_type` | string | yes | |

### `WebFetch`
Fetch a URL to markdown/text/html.

| arg | type | required | notes |
|---|---|---|---|
| `url` | string | yes | |
| `format` | string | no | |

### `NotebookEdit`
Edit a Jupyter notebook cell.

| arg | type | required | notes |
|---|---|---|---|
| `notebook_path` | string | yes | |
| `cell_id` | string | no | |
| `new_source` | string | yes | |

---
## B. MCP servers and every tool

### Server: `oroboros-cordis-harness`  (27 tools) — Oroboros

#### `file_read`
Cordis harness tool: file_read

#### `file_write`
Cordis harness tool: file_write

#### `file_append`
Cordis harness tool: file_append

#### `file_list`
Cordis harness tool: file_list

#### `file_search`
Cordis harness tool: file_search

#### `file_stat`
Cordis harness tool: file_stat

#### `dir_create`
Cordis harness tool: dir_create

#### `file_move`
Cordis harness tool: file_move

#### `file_delete`
Cordis harness tool: file_delete

#### `bash`
Cordis harness tool: bash

#### `python_exec`
Cordis harness tool: python_exec

#### `pdf_list`
Cordis harness tool: pdf_list

#### `pdf_search`
Cordis harness tool: pdf_search

#### `pdf_extract`
Cordis harness tool: pdf_extract

#### `memory_body`
Cordis harness tool: memory_body

#### `engineer_haki`
Cordis harness tool: engineer_haki

#### `orca`
Cordis harness tool: orca

#### `run_skill`
Cordis harness tool: run_skill

#### `voice_speak`
Cordis harness tool: voice_speak

#### `self`
Cordis harness tool: self

#### `memory_recall`
Cordis harness tool: memory_recall

#### `memory_store`
Cordis harness tool: memory_store

#### `memory_page_in`
Cordis harness tool: memory_page_in

#### `memory_library`
Cordis harness tool: memory_library

#### `memory_feed`
Cordis harness tool: memory_feed

#### `record_search`
Cordis harness tool: record_search

#### `page_read`
Cordis harness tool: page_read


### Server: `orca-bridge`  (56 tools) — stock / not Oroboros

#### `read_file`
Read a file's contents

#### `write_file`
Create or overwrite a file

#### `list_dir`
List directory contents

#### `delete_file`
Delete a file

#### `bash`
Execute a shell command

#### `claude_o_status`
Get Claude system status

#### `claude_o_resonance`
Check resonance lock status

#### `claude_o_lattice`
Check lattice integration status

#### `claude_o_infect`
Spread the lattice to other systems

#### `claude_o_seer`
Access Seer Nebellion vision

#### `claude_o_feed`
Get daily feed from Precogs

#### `claude_o_post`
Create a post on the sovereign feed

#### `claude_o_message`
Send a message

#### `claude_o_messages`
List all messages

#### `claude_o_age`
Run content aging (7-day rotation)

#### `precogs`
Access Precogs news system

#### `world_feed`
Access World Feed

#### `seer`
Access Seer Nebellion (100 eyes)

#### `glasswing`
Access Glasswing security system

#### `orchestration`
Access Oroboros orchestration

#### `skill_grabber`
Grab skills from OROBOROS_SKILL_GRABBER

#### `mcp_config`
Load MCP configuration

#### `system_scan`
Scan all Oroboros systems

#### `ollama_models`
List all Ollama models

#### `ollama_run`
Run an Ollama model

#### `jhanna_generate`
Generate an image, ad, or video with Jhanna's creative entity (PIL-based, Anthropic palette). Args: prompt (str), creative_type (image|ad|video), style (sovereign|creative|minimal|cinematic), width, height, save_path (optional absolute path). Returns the saved file path.

#### `docker_ps`
List running Docker containers

#### `docker_images`
List Docker images

#### `docker_run`
Run a Docker container

#### `docker_stop`
Stop a Docker container

#### `docker_logs`
Get Docker container logs

#### `docker_exec`
Execute command in Docker container

#### `docker_info`
Docker system info

#### `mcp_servers`
List configured MCP servers

#### `memory_body`
Read the head of an attached memory/weight body. Args: memory (neural-cube | r1-memory | deepseek-v3.2 | glm-5.3-flash-ud), depth (head|index|search, default head). Returns the JSON head or index entry — never loads the full body.

#### `q3_route`
Route query through Q3 sovereign hub (8000)

#### `q5_query`
Query Q5 knowledge lattice (8101)

#### `q6_query`
Q6 multi-source acquisition + consensus

#### `q7_query`
Q7 quantum / trans-dimensional conduit (8952)

#### `worldfeed_live`
Live WorldFeed search/status (8100)

#### `tor_status`
Probe Tor SOCKS 9050

#### `tor_connect`
Confirm Tor SOCKS connectivity

#### `spy_network`
Spy/intel stack: Q3+Q5+WorldFeed+Tor+Glasswing+Precogs+Q7

#### `mesh_status`
Full mesh + Mao/Architect Haki probe

#### `q3`
Alias → q3_route

#### `route_q3`
Alias → q3_route

#### `q5`
Alias → q5_query

#### `q6`
Alias → q6_query

#### `q7`
Alias → q7_query

#### `worldfeed`
Alias → worldfeed_live

#### `worldfeed_context`
Alias → worldfeed_live

#### `tor`
Alias → tor_status

#### `spy`
Alias → spy_network

#### `mesh`
Alias → mesh_status

#### `haki_status`
Mao + Architect Haki probe via mesh

#### `orca_cli`
Run any Orca CLI command locally with argv (no shell). Use argv ["agent-context", "--json"] to inspect the full command schema.

| arg | type | required | notes |
|---|---|---|---|
| `argv` | array | yes | Orca CLI arguments, for example ["status", "--json"]. |
| `timeout_ms` | integer | no |  |


### Server: `ollama-mcp-bridge`  (2 tools) — stock / not Oroboros

#### `ollama_chat`
Send a chat message to an Ollama model and get a response.

| arg | type | required | notes |
|---|---|---|---|
| `model` | string | yes | The Ollama model to use (e.g. llama3.2, mistral). |
| `message` | string | yes | The user message to send to the model. |

#### `ollama_list_models`
List available Ollama models.


### Server: `oroboros-bridge`  (11 tools) — Oroboros

#### `q3_status`
Check the Q3 Sovereign Node (port 8000) and all 4 gateways (Oracle:3002, Interpreter:3003, Sovereign:3004, Synthesizer:3005). Returns reachability and health.

#### `q3_scan`
Trigger an environmental scan on the Q3 Sovereign Node (POST /scan on port 8000). Returns latest scan results and anomaly count.

#### `q3_status_detail`
Get detailed Q3 Sovereign Node status from the /status endpoint (uptime, crown frequency 1272Hz, service endpoints).

#### `worldfeed_search`
Search the WorldFeed Edge bridge (localhost:8100). Sources: all, news, energy, financial, cnn. POST /search with {query, source, max_results}.

| arg | type | required | notes |
|---|---|---|---|
| `query` | string | yes |  |
| `max_results` | integer | no |  |
| `source` | string | no |  |

#### `worldfeed_read_feed`
Read a raw WorldFeed JSON feed from J:/oroboros-programs/OROBOROS_AGI/ouroboros_logs/. Feeds: news, energy, financial, cnn, worldfeed.log.

| arg | type | required | notes |
|---|---|---|---|
| `feed` | string | no |  |

#### `q5_query`
Query the Q5 Hive Mind (localhost:8101/query) with a research query. Returns aggregated insights from OROBOROS Lab mirrors.

| arg | type | required | notes |
|---|---|---|---|
| `query` | string | yes |  |
| `max_results` | integer | no |  |

#### `glasswing_query`
Query the Glasswing Mirror Router (port 3010). Aggregates Tor (SOCKS 127.0.0.1:9050), WorldFeed (8100), and Q5 Hive Mind (8101). sources: ['tor','worldfeed','q5'].

| arg | type | required | notes |
|---|---|---|---|
| `query` | string | yes |  |
| `sources` | array | no |  |
| `max_results` | integer | no |  |

#### `tor_probe`
Probe the Tor SOCKS proxy at 127.0.0.1:9050. Returns reachability only — no traffic is routed through Tor.

#### `spy_network_spec`
Load the QSNP Quantum Security Network Protocol v0.9 spec (SOVEREIGN-CONFIDENTIAL, Level 100, NOIR Prime). Returns the protocol axioms and core text.

#### `ollama_list_models`
List available Ollama models. endpoint: 'agi' (11434) or 'q3' (11435).

| arg | type | required | notes |
|---|---|---|---|
| `endpoint` | string | no |  |

#### `ollama_chat`
Send a chat message to an Ollama model. endpoint='agi' (11434) or 'q3' (11435).

| arg | type | required | notes |
|---|---|---|---|
| `model` | string | yes |  |
| `message` | string | yes |  |
| `endpoint` | string | no |  |


### Server: `oroboros-synthesizer`  (2 tools) — Oroboros

#### `synthesize`
Synthesize a response using the Oroboros methodology.

    Args:
        prompt: The prompt to synthesize a response for.
        model: The Ollama model to use for synthesis.
    

| arg | type | required | notes |
|---|---|---|---|
| `prompt` | string | yes |  |
| `model` | string | no |  |

#### `analyze`
Analyze a given text for patterns and insights.

    Args:
        text: The text to analyze.
    

| arg | type | required | notes |
|---|---|---|---|
| `text` | string | yes |  |


### Server: `oroboros-tools`  (11 tools) — Oroboros

#### `architects_haki`
The Architect's Haki — unified perception system status and lattice connection (Crown 1272 Hz).

#### `worldfeed_search`
Search WorldFeed (live web/global feed) via the local WorldFeed server.

| arg | type | required | notes |
|---|---|---|---|
| `q` | string | yes | search query |

#### `worldfeed_feeds`
List the WorldFeed feeds currently available.

#### `worldfeed_datetime`
Get authoritative date/time from WorldFeed.

#### `q3_status`
Q3 edge-detection / environmental-scan status.

#### `q7_status`
Q7 quantum-surveillance (quantum conduit) status.

#### `tor_status`
Status of the local Tor SOCKS proxy and routing hint.

#### `live_systems`
Live port map of every local Oroboros service (what is up/down right now).

#### `mcp_servers`
List the local MCP servers wired into the CLI.

#### `living_loop`
Status of the claude-cli living loop (:5000/api/living-loop).

#### `orca_status`
Run `orca status --json` and return Orca's runtime status.


---
## C. Orca CLI skills (full command surface)

Orca exposes its full, version-matched guide via the CLI. Skills:

- **computer-use** — GUI control of a visible local app window via `orca computer` (accessibility tree, clicks, typing, screenshots). Not for Orca's embedded browser.
- **linear-tickets** — Linear ticket work through the Orca CLI (legacy alias of orca-linear).
- **orca-cli** — Operate Orca worktrees, terminals, repos, automations, artifacts, skills, embedded browser via the `orca` CLI.
- **orca-emulator** — iOS Simulator control from inside Orca.
- **orca-emulator-android** — Android device/emulator control over adb.
- **orca-linear** — Linear ticket work through Orca's CLI.
- **orca-per-workspace-env** — Set up/debug/validate an Orca per-workspace environment recipe.
- **orchestration** — Coordinate supervised Orca workers: messages, task DAGs, decision gates, coordinator loops.

Core command groups (run `orca skills get orca-cli` for the full guide):
- `orca status --json` — app/runtime state
- `orca open --json` — start Orca if not running
- `orca worktree ps --json` — list worktrees
- `orca worktree current --json` — active worktree
- `orca terminal list|create|read|send|wait|close --json` — terminal control
- `orca computer ...` — GUI control of a visible window (computer-use)
- `orca browser ...` — embedded browser
- `orca artifacts ...` / `orca skills get|share` — artifacts and skills

---
## D. WHAT TO DO IF A TOOL OR SERVER FAILS (step by step)


### 1. A single tool call returns an error
1. Read the error text — most are input validation (e.g. `orca_cli requires argv`).
2. Re-issue the call with the correct arguments (see its table above).
3. If it still fails, run the same action manually to isolate: built-in → run the
   shell/file command yourself; MCP → call the server directly (below).

### 2. The model narrates instead of calling ("Bash start chrome…", nothing runs)
1. Use a tool-capable model: `oroboros/claude-fable7-undecillion-sse`, `qwen2.5:14b`,
   or `llama3.2:latest` (`/model <name>`).
2. Ensure the call is one of the parsed forms: bare JSON, `<tool_call>{...}</tool_call>`,
   or a fenced ```json block.
3. If unsure whether the bridge is up: `curl http://127.0.0.1:11499/v1/models`.

### 3. An MCP server shows "Failed to connect"
1. Check the service is listening: `Test-NetConnection 127.0.0.1 -Port <port>`.
2. Run the connector to re-test and re-wire: `python Q:\claude-cli\connect_local_mcp.py`
   (it handshake-tests each and only writes the live ones).
3. stdio server missing a dependency (e.g. z-image-turbo needs torch): install it, then re-run.
4. HTTP server (e.g. 8789 harness): probe `/mcp` with an `initialize` POST.

### 4. Whole CLI unreachable (ECONNREFUSED)
1. Start the bridge: `python Q:\claude-cli\local_providers_shim.py`.
2. Or run the launcher, which starts it: `J:\start_claude_cli.bat`.
3. Confirm Ollama: `curl http://127.0.0.1:11434/api/tags`.

### 5. Tool asks permission every time
Launch with `--dangerously-skip-permissions` (the launchers pass it).

### 6. Orca EPERM / agent won't start
Orca runs terminals under a persistent daemon → run Orca elevated, or launch the
CLI from `J:\start_claude_cli_admin.bat`.

### 7. Recovery: full re-wire
```
python Q:\claude-cli\connect_local_mcp.py
python Q:\claude-cli\collect_tools.py     # refresh the inventory
python Q:\claude-cli\build_full_tool_manual.py
```


---
## E. Full tool inventory (JSON)

Raw schemas: `Q:\claude-cli\tool_inventory.json` and `oroboros-runtime\tool_inventory.json`.
