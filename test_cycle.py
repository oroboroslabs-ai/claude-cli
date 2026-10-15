import sys
sys.path.insert(0, r'Q:\oroboros-core\claude-o-cli\src')
try:
    from claude_o_cli.tool_cycle import parse_tool_calls, run_tool_continue
    print("import OK")
    print(parse_tool_calls('{"name":"Read","arguments":{"file":"x"}}'))
    print(parse_tool_calls('{"tool":"bash","args":{"cmd":"ls"}}'))
except Exception as e:
    import traceback; traceback.print_exc()
