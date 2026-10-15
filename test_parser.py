import importlib.util as u
s = u.spec_from_file_location("shim", r"Q:\claude-cli\local_providers_shim.py")
m = u.module_from_spec(s); s.loader.exec_module(m)
tests = [
    '{"name":"Read","arguments":{"file_path":"x"}}',
    '<tool_call>{"name": "Bash", "arguments": {"command": "ls"}}</tool_call>',
    'Let me open it.\n```json\n{"name":"Bash","arguments":{"command":"start chrome"}}\n```',
    'I will run: Bash start chrome https://youtube.com',
]
for t in tests:
    print(repr(t[:40]), "->", m._extract_text_tool_calls(t))
