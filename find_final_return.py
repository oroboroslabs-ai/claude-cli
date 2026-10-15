#!/usr/bin/env python3
"""Find the final return in api_chat"""
f = open('Q:\\oroboros-core\\claude-o-cli\\run_cli.py', 'r', encoding='utf-8')
c = f.read()
f.close()
idx = c.find('def api_chat()')
# Find the function body end
func_end = c.find('\n@app.route', idx)
print('Function body from', idx, 'to', func_end)
# Find the last return
last_ret = c.rfind('return jsonify', idx, func_end)
print('Last return at:', last_ret)
print(c[last_ret:last_ret+300])
