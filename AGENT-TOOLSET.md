# AGENT TOOLSET — tools, functions, instructions (the agent backup)
### Oroboros-Anthropic Claude CLI. Local only (127.0.0.1). No cloud key.

## How a call flows
1. CLI builds request with `tools[]`.
2. Bridge (:11499) converts each tool schema to Ollama and forwards it.
3. Model emits a call — native `tool_calls`, or text:
   - `{"name":"Tool","arguments":{...}}`
   - `<tool_call>{"name":"Tool","arguments":{...}}</tool_call>`
   - fenced ```json {...}```
4. Bridge returns it to the CLI as Anthropic `tool_use`.
5. CLI executes (built-in locally; MCP via its server) and feeds back `tool_result`.
Never describe a call in prose — emit it.

## Built-in tools (functions)
- Bash(command, timeout?, description?) — run a shell command.
- Edit(file_path, old_string, new_string, replace_all?) — exact replace.
- Read(file_path, offset?, limit?) — read file/dir.
- Write(file_path, content) — create/overwrite.
- Glob(pattern, path?) — find files.
- Grep(pattern, path?, include?, context?, limit?) — search contents.
- TodoWrite(todos[]) — task list.
- Task(description, prompt, subagent_type) — subagent.
- WebFetch(url, format?) — fetch URL.
- NotebookEdit(notebook_path, cell_id?, new_source) — notebook cell.

## MCP servers + tools
- oroboros-cordis-harness (27): file_read/write/append/list/search/stat, dir_create,
  file_move/delete, bash, python_exec, pdf_list/search/extract, memory_body,
  engineer_haki, orca, run_skill, voice_speak, self, memory_recall/store/
  page_in/library/feed, record_search, page_read.
- oroboros-tools (11): architects_haki, worldfeed_search(q), worldfeed_feeds,
  worldfeed_datetime, q3_status, q7_status, tor_status, live_systems,
  mcp_servers, living_loop, orca_status.
- oroboros-bridge (11): q3_status, q3_scan, q3_status_detail, worldfeed_search,
  worldfeed_read_feed, q5_query, glasswing_query, tor_probe, spy_network_spec,
  ollama_list_models, ollama_chat.
- ollama-mcp-bridge (2): ollama_chat, ollama_list_models.
- oroboros-synthesizer (2): synthesize(prompt, model), analyze(text).
- orca-bridge (56): read/write/delete_file, list_dir, bash, docker_*,
  ollama_models/run, q3/q5/q6/q7 (route/query), worldfeed_live, tor_status/connect,
  spy_network, mesh_status, haki_status, claude_o_* (status/resonance/lattice/
  infect/seer/feed/post/message(s)/age), precogs, glasswing, orchestration,
  skill_grabber, mcp_config, system_scan, jhanna_generate, memory_body, orca_cli(argv).

## Orca CLI skills
computer-use, linear-tickets, orca-cli, orca-emulator, orca-emulator-android,
orca-linear, orca-per-workspace-env, orchestration.

## If a tool or server fails
1. Tool returns error → read it (usually bad args), re-issue correctly.
2. Model narrates instead of calling → use a tool-capable model (undecillion /
   qwen2.5:14b / llama3.2), and emit one of the parsed call forms above.
3. MCP "failed to connect" → check the port; run
   `python Q:\claude-cli\connect_local_mcp.py` to re-test and re-wire.
4. stdio server missing a dependency → install it, re-run the connector.
5. Whole CLI ECONNREFUSED → start `python Q:\claude-cli\local_providers_shim.py`
   (or the launcher).
6. Permission prompt each time → launch with `--dangerously-skip-permissions`.
7. Orca EPERM/elevation → run Orca or `J:\start_claude_cli_admin.bat` elevated.

## Recovery
```
python Q:\claude-cli\connect_local_mcp.py
python Q:\claude-cli\collect_tools.py
python Q:\claude-cli\build_full_tool_manual.py
```
