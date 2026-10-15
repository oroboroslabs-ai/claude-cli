#!/usr/bin/env python3
"""Find the return statement in api_chat"""
f = open('Q:\\oroboros-core\\claude-o-cli\\run_cli.py', 'r', encoding='utf-8')
c = f.read()
f.close()
idx = c.find('def api_chat()')
ret_idx = c.find('return jsonify', idx)
print('Return at:', ret_idx)
print(c[ret_idx:ret_idx+300])
