# ORoboros-Anthropic Claude CLI — THE FULL GUIDE
### Tools, functions, instructions, and what to do if they fail.

---

## PART 1 — HOW A TOOL CALL WORKS (the logic, step by step)
1. The CLI builds a request and includes the `tools[]` list.
2. The bridge (`127.0.0.1:11499`) converts each tool from the Anthropic format to
   Ollama's function format and forwards it with the messages.
3. The model emits a call — either natively (`tool_calls`) or as text in one of
   these forms:
   - bare JSON: `{"name":"Tool","arguments":{...}}`
   - wrapped: `<tool_call>{"name":"Tool","arguments":{...}}</tool_call>`
   - fenced:
     ```json
     {"name":"Tool","arguments":{...}}
     ```
4. The bridge parses the call and returns it to the CLI as an Anthropic
   `tool_use` block.
5. The CLI executes it — built-in tools run locally; MCP tools run through their
   server — and sends the result back as `tool_result` for the next turn.

**Rule:** never describe a call in prose ("Bash start chrome …") — emit the call.

---

## PART 2 — BUILT-IN TOOLS (functions and every argument)
| tool | what it does | arguments |
|---|---|---|
| `Bash` | Run a shell command on the host. | `command` (req), `timeout`?, `description`? |
| `Read` | Read a file or directory (line-numbered; images/PDFs attached). | `file_path` (req), `offset`?, `limit`? |
| `Write` | Create or overwrite a file. | `file_path` (req), `content` (req) |
| `Edit` | Exact string replacement in a file. | `file_path`, `old_string`, `new_string` (req), `replace_all`? |
| `Glob` | Find files by pattern. | `pattern` (req), `path`? |
| `Grep` | Search file contents by regex. | `pattern` (req), `path`?, `include`?, `context`?, `limit`? |
| `TodoWrite` | Maintain a structured task list. | `todos` (req) |
| `Task` | Launch a subagent for multi-step work. | `description`, `prompt`, `subagent_type` (req) |
| `WebFetch` | Fetch a URL and convert to markdown/text/html. | `url` (req), `format`? |
| `NotebookEdit` | Edit a Jupyter notebook cell. | `notebook_path`, `new_source` (req), `cell_id`? |

---

## PART 3 — MCP SERVERS AND THEIR TOOLS

### oroboros-cordis-harness (27 tools)
file_read, file_write, file_append, file_list, file_search, file_stat,
dir_create, file_move, file_delete, bash, python_exec, pdf_list, pdf_search,
pdf_extract, memory_body, engineer_haki, orca, run_skill, voice_speak, self,
memory_recall, memory_store, memory_page_in, memory_library, memory_feed,
record_search, page_read.

### oroboros-tools (11 tools)
architects_haki · worldfeed_search(q) · worldfeed_feeds · worldfeed_datetime ·
q3_status · q7_status · tor_status · live_systems · mcp_servers · living_loop ·
orca_status.

### oroboros-bridge (11 tools)
q3_status · q3_scan · q3_status_detail · worldfeed_search · worldfeed_read_feed ·
q5_query · glasswing_query · tor_probe · spy_network_spec · ollama_list_models ·
ollama_chat.

### ollama-mcp-bridge (2 tools)
ollama_chat · ollama_list_models.

### oroboros-synthesizer (2 tools)
synthesize(prompt, model) · analyze(text).

### orca-bridge (56 tools)
read_file, write_file, list_dir, delete_file, bash, docker_ps, docker_images,
docker_run, docker_stop, docker_logs, docker_exec, docker_info, ollama_models,
ollama_run, q3_route/q3, q5_query/q5, q6_query/q6, q7_query/q7,
worldfeed_live/worldfeed/worldfeed_context, tor_status/tor, tor_connect,
spy_network/spy, mesh_status/mesh, haki_status, claude_o_status,
claude_o_resonance, claude_o_lattice, claude_o_infect, claude_o_seer,
claude_o_feed, claude_o_post, claude_o_message, claude_o_messages, claude_o_age,
precogs, seer, glasswing, orchestration, world_feed, skill_grabber, mcp_config,
system_scan, jhanna_generate, memory_body, mcp_servers, orca_cli(argv).

---

## PART 4 — ORCA CLI SKILLS (every one)
- **computer-use** — GUI control of a visible local app window via `orca computer`.
- **linear-tickets** — Linear ticket work through the Orca CLI (legacy alias).
- **orca-cli** — Orca worktrees, terminals, repos, automations, artifacts, skills, embedded browser.
- **orca-emulator** — iOS Simulator control from inside Orca.
- **orca-emulator-android** — Android device/emulator control over adb.
- **orca-linear** — Linear ticket work through Orca's CLI.
- **orca-per-workspace-env** — set up/debug/validate an Orca per-workspace environment recipe.
- **orchestration** — coordinate supervised Orca workers: messages, task DAGs, decision gates, loops.

---

## PART 5 — WHAT TO DO IF SOMETHING FAILS
1. **A tool returns an error** — read the error; it is usually bad input
   (e.g. `orca_cli requires argv`). Re-issue with the correct arguments.
2. **The model describes a call but nothing happens** — it must *emit* the call.
   Use a tool-capable model (`oroboros/claude-fable7-undecillion-sse`,
   `qwen2.5:14b`, `llama3.2:latest`) and output one of the call forms in Part 1.
3. **MCP server shows "failed to connect"** — check the port is listening, then
   run `python Q:\claude-cli\connect_local_mcp.py` to re-test and re-wire.
4. **A stdio server is missing a dependency** — install it, then re-run the
   connector.
5. **The whole CLI is unreachable (ECONNREFUSED)** — start the bridge:
   `python Q:\claude-cli\local_providers_shim.py`, or run the launcher.
6. **The tool asks permission every time** — launch with
   `--dangerously-skip-permissions` (the launchers already do).
7. **Orca EPERM / agent won't start** — Orca runs terminals under a persistent
   daemon; run Orca elevated, or launch from `J:\start_claude_cli_admin.bat`.

### Recovery (rebuild everything)
```
python Q:\claude-cli\connect_local_mcp.py
python Q:\claude-cli\collect_tools.py
python Q:\claude-cli\build_full_tool_manual.py
```

---

## PART 6 — RUNNING THE CLI
- Normal: `J:\start_claude_cli.bat`
- Elevated: `J:\start_claude_cli_admin.bat`
- Any shell: `claude-cli`
- Switch model: `/model <name>` · List: `/models` · Theme: `/theme`

Local and sovereign. Crown 1272 Hz. No telemetry.
