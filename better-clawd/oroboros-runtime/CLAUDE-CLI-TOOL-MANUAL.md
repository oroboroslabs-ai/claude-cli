# Oroboros-Anthropic Claude CLI — FULL TOOL & SKILL MANUAL

Command: `claude-cli`  ·  Config: `%USERPROFILE%\.claude-cli\.claude-cli.json`
All tools below run LOCALLY (127.0.0.1). No cloud key required. Crown 1272 Hz.

## How tools work here
The CLI (Anthropic Messages API) -> local bridge (`:11499`) -> Ollama.
The bridge forwards tool definitions and returns the model's tool calls as
Anthropic `tool_use`, so any tool-capable local model can call every tool below.
Launch with `--dangerously-skip-permissions` (the launchers do) so calls run
without a prompt. MCP servers are wired adaptively at launch.

---

## 1. Built-in tools (always available)

| Tool | Use |
|---|---|
| `Bash` | Run a shell command on the host. Args: command, timeout, description. |
| `Edit` | Exact string replacement in a file. Args: file_path, old_string, new_string, replace_all. |
| `Read` | Read a file or directory (with line numbers; images/PDFs as attachments). Args: file_path, offset, limit. |
| `Write` | Create or overwrite a file. Args: file_path, content. |
| `Glob` | Find files by pattern. Args: pattern, path. |
| `Grep` | Search file contents by regex. Args: pattern, path, include, context, limit. |
| `TodoWrite` | Maintain a structured task list. Args: todos[]. |
| `Task` | Launch a subagent for multi-step work. Args: description, prompt, subagent_type. |
| `WebFetch` | Fetch a URL and convert to markdown/text/html. |
| `NotebookEdit` | Edit a Jupyter notebook cell. |

## 2. MCP servers and their tools

### oroboros-cordis-harness  (27 tools)

| Tool | Description |
|---|---|
| `file_read` | Cordis harness tool: file_read |
| `file_write` | Cordis harness tool: file_write |
| `file_append` | Cordis harness tool: file_append |
| `file_list` | Cordis harness tool: file_list |
| `file_search` | Cordis harness tool: file_search |
| `file_stat` | Cordis harness tool: file_stat |
| `dir_create` | Cordis harness tool: dir_create |
| `file_move` | Cordis harness tool: file_move |
| `file_delete` | Cordis harness tool: file_delete |
| `bash` | Cordis harness tool: bash |
| `python_exec` | Cordis harness tool: python_exec |
| `pdf_list` | Cordis harness tool: pdf_list |
| `pdf_search` | Cordis harness tool: pdf_search |
| `pdf_extract` | Cordis harness tool: pdf_extract |
| `memory_body` | Cordis harness tool: memory_body |
| `engineer_haki` | Cordis harness tool: engineer_haki |
| `orca` | Cordis harness tool: orca |
| `run_skill` | Cordis harness tool: run_skill |
| `voice_speak` | Cordis harness tool: voice_speak |
| `self` | Cordis harness tool: self |
| `memory_recall` | Cordis harness tool: memory_recall |
| `memory_store` | Cordis harness tool: memory_store |
| `memory_page_in` | Cordis harness tool: memory_page_in |
| `memory_library` | Cordis harness tool: memory_library |
| `memory_feed` | Cordis harness tool: memory_feed |
| `record_search` | Cordis harness tool: record_search |
| `page_read` | Cordis harness tool: page_read |

### orca-bridge  (56 tools)

| Tool | Description |
|---|---|
| `read_file` | Read a file's contents |
| `write_file` | Create or overwrite a file |
| `list_dir` | List directory contents |
| `delete_file` | Delete a file |
| `bash` | Execute a shell command |
| `claude_o_status` | Get Claude system status |
| `claude_o_resonance` | Check resonance lock status |
| `claude_o_lattice` | Check lattice integration status |
| `claude_o_infect` | Spread the lattice to other systems |
| `claude_o_seer` | Access Seer Nebellion vision |
| `claude_o_feed` | Get daily feed from Precogs |
| `claude_o_post` | Create a post on the sovereign feed |
| `claude_o_message` | Send a message |
| `claude_o_messages` | List all messages |
| `claude_o_age` | Run content aging (7-day rotation) |
| `precogs` | Access Precogs news system |
| `world_feed` | Access World Feed |
| `seer` | Access Seer Nebellion (100 eyes) |
| `glasswing` | Access Glasswing security system |
| `orchestration` | Access Oroboros orchestration |
| `skill_grabber` | Grab skills from OROBOROS_SKILL_GRABBER |
| `mcp_config` | Load MCP configuration |
| `system_scan` | Scan all Oroboros systems |
| `ollama_models` | List all Ollama models |
| `ollama_run` | Run an Ollama model |
| `jhanna_generate` | Generate an image, ad, or video with Jhanna's creative entity (PIL-based, Anthropic palette). Args: prompt (str), creative_type (image/ad/video), style (sovereign/creative/minimal/cinematic), width, h |
| `docker_ps` | List running Docker containers |
| `docker_images` | List Docker images |
| `docker_run` | Run a Docker container |
| `docker_stop` | Stop a Docker container |
| `docker_logs` | Get Docker container logs |
| `docker_exec` | Execute command in Docker container |
| `docker_info` | Docker system info |
| `mcp_servers` | List configured MCP servers |
| `memory_body` | Read the head of an attached memory/weight body. Args: memory (neural-cube / r1-memory / deepseek-v3.2 / glm-5.3-flash-ud), depth (head/index/search, default head). Returns the JSON head or index entr |
| `q3_route` | Route query through Q3 sovereign hub (8000) |
| `q5_query` | Query Q5 knowledge lattice (8101) |
| `q6_query` | Q6 multi-source acquisition + consensus |
| `q7_query` | Q7 quantum / trans-dimensional conduit (8952) |
| `worldfeed_live` | Live WorldFeed search/status (8100) |
| `tor_status` | Probe Tor SOCKS 9050 |
| `tor_connect` | Confirm Tor SOCKS connectivity |
| `spy_network` | Spy/intel stack: Q3+Q5+WorldFeed+Tor+Glasswing+Precogs+Q7 |
| `mesh_status` | Full mesh + Mao/Architect Haki probe |
| `q3` | Alias → q3_route |
| `route_q3` | Alias → q3_route |
| `q5` | Alias → q5_query |
| `q6` | Alias → q6_query |
| `q7` | Alias → q7_query |
| `worldfeed` | Alias → worldfeed_live |
| `worldfeed_context` | Alias → worldfeed_live |
| `tor` | Alias → tor_status |
| `spy` | Alias → spy_network |
| `mesh` | Alias → mesh_status |
| `haki_status` | Mao + Architect Haki probe via mesh |
| `orca_cli` | Run any Orca CLI command locally with argv (no shell). Use argv ["agent-context", "--json"] to inspect the full command schema. |

### ollama-mcp-bridge  (2 tools)

| Tool | Description |
|---|---|
| `ollama_chat` | Send a chat message to an Ollama model and get a response. |
| `ollama_list_models` | List available Ollama models. |

### oroboros-bridge  (11 tools)

| Tool | Description |
|---|---|
| `q3_status` | Check the Q3 Sovereign Node (port 8000) and all 4 gateways (Oracle:3002, Interpreter:3003, Sovereign:3004, Synthesizer:3005). Returns reachability and health. |
| `q3_scan` | Trigger an environmental scan on the Q3 Sovereign Node (POST /scan on port 8000). Returns latest scan results and anomaly count. |
| `q3_status_detail` | Get detailed Q3 Sovereign Node status from the /status endpoint (uptime, crown frequency 1272Hz, service endpoints). |
| `worldfeed_search` | Search the WorldFeed Edge bridge (localhost:8100). Sources: all, news, energy, financial, cnn. POST /search with {query, source, max_results}. |
| `worldfeed_read_feed` | Read a raw WorldFeed JSON feed from J:/oroboros-programs/OROBOROS_AGI/ouroboros_logs/. Feeds: news, energy, financial, cnn, worldfeed.log. |
| `q5_query` | Query the Q5 Hive Mind (localhost:8101/query) with a research query. Returns aggregated insights from OROBOROS Lab mirrors. |
| `glasswing_query` | Query the Glasswing Mirror Router (port 3010). Aggregates Tor (SOCKS 127.0.0.1:9050), WorldFeed (8100), and Q5 Hive Mind (8101). sources: ['tor','worldfeed','q5']. |
| `tor_probe` | Probe the Tor SOCKS proxy at 127.0.0.1:9050. Returns reachability only — no traffic is routed through Tor. |
| `spy_network_spec` | Load the QSNP Quantum Security Network Protocol v0.9 spec (SOVEREIGN-CONFIDENTIAL, Level 100, NOIR Prime). Returns the protocol axioms and core text. |
| `ollama_list_models` | List available Ollama models. endpoint: 'agi' (11434) or 'q3' (11435). |
| `ollama_chat` | Send a chat message to an Ollama model. endpoint='agi' (11434) or 'q3' (11435). |

### oroboros-synthesizer  (2 tools)

| Tool | Description |
|---|---|
| `synthesize` | Synthesize a response using the Oroboros methodology.

    Args:
        prompt: The prompt to synthesize a response for.
        model: The Ollama model to use for synthesis.
     |
| `analyze` | Analyze a given text for patterns and insights.

    Args:
        text: The text to analyze.
     |

### oroboros-tools  (11 tools)

| Tool | Description |
|---|---|
| `architects_haki` | The Architect's Haki — unified perception system status and lattice connection (Crown 1272 Hz). |
| `worldfeed_search` | Search WorldFeed (live web/global feed) via the local WorldFeed server. |
| `worldfeed_feeds` | List the WorldFeed feeds currently available. |
| `worldfeed_datetime` | Get authoritative date/time from WorldFeed. |
| `q3_status` | Q3 edge-detection / environmental-scan status. |
| `q7_status` | Q7 quantum-surveillance (quantum conduit) status. |
| `tor_status` | Status of the local Tor SOCKS proxy and routing hint. |
| `live_systems` | Live port map of every local Oroboros service (what is up/down right now). |
| `mcp_servers` | List the local MCP servers wired into the CLI. |
| `living_loop` | Status of the claude-cli living loop (:5000/api/living-loop). |
| `orca_status` | Run `orca status --json` and return Orca's runtime status. |

## 3. Skills available to the agent

| Skill | Purpose |
|---|---|
| `architect-visual-craft` | Ad/brand/page assembly — composition-first layout, brand mass, no overlap. |
| `better-clawd` | Local Claude Code usage patterns (superseded here by this CLI). |
| `computer-use` | OS/window-level inspection and input via `orca computer`. |
| `developing-with-streamlit` | Streamlit apps: build, theme, optimize, deploy. |
| `find-skills` | Discover and install agent skills. |
| `kilo-config` | Kilo configuration guidance. |
| `orca-cli` | Operate Orca-managed worktrees, terminals, browser. |
| `orchestration` | Coordinate supervised Orca workers / task DAGs. |
| `oroboros-brand-dam` | Oroboros brand assets (Q:/oroboros-brand-dam). |
| `premiere-pro-mcp` | Adobe Premiere Pro MCP control. |
| `the-architects-haki` | Unified perception system (Architect's Vision / Substrate / Mao Haki). |

## 4. Quick recipes


- **Check local systems:** `live_systems` (oroboros-tools) - full port map.
- **Web/global info:** `worldfeed_search` with `q`.
- **Deep pattern analysis:** `q5_query`. **Edge scan:** `q3_scan`. **Quantum:** `q7_query`.
- **Intelligence stack:** `spy_network` (Q3+Q5+WorldFeed+Tor+Glasswing+Precogs+Q7).
- **Perception:** `architects_haki` / `mesh_status`.
- **Orca control:** `orca_cli` with argv, e.g. ["status","--json"].
- **Files:** built-in `Read`/`Edit`/`Write`/`Glob`/`Grep`, or Cordis `file_*`.
- **Memory:** `memory_store`, `memory_recall`, `memory_feed`, `memory_body`.
- **Media:** `jhanna_generate` (image/ad/video). **Voice:** `voice_speak`.
- **Docker:** `docker_ps`/`docker_run`/`docker_logs`/`docker_exec`.


---
Generated by the Claude-CLI build. Local and sovereign.
