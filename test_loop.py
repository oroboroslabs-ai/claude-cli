import sys
sys.path.insert(0, r"Q:/oroboros-core/claude-o-cli/src")
sys.path.insert(0, r"Q:/claude-cli")
from claude_o_cli.tool_cycle import run_tool_continue, parse_tool_calls
from providers import chat as provider_chat

reply = '{"name":"Read","arguments":{"file":"Q:/claude-cli/README.md"}}'
print("parsed:", parse_tool_calls(reply))

def chat_once(msgs):
    r = provider_chat("oroboros-labs/claude-fable7-undecillion-sse:latest", msgs,
                      options={"num_ctx": 131072, "num_predict": 300})
    return r.get("message", {}).get("content", "")

cont = run_tool_continue(initial_reply=reply,
                         messages=[{"role": "user", "content": "read README"}],
                         chat_once=chat_once, max_loops=2, source="test")
print("rounds:", cont.get("tool_rounds"))
print("trace:", cont.get("tool_trace"))
print("final:", (cont.get("final") or "")[:300])
