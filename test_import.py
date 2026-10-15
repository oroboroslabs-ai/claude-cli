import sys
src = r"Q:/oroboros-core/claude-o-cli/src"
if src not in sys.path:
    sys.path.insert(0, src)
try:
    from claude_o_cli.terminal_runtime import TOOL_JSON_RULE
    from claude_o_cli.tool_cycle import run_tool_continue, system_fragment as tool_cycle_frag
    print("import OK")
    print("TOOL_JSON_RULE len", len(TOOL_JSON_RULE))
except Exception as e:
    import traceback; traceback.print_exc()
