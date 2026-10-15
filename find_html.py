#!/usr/bin/env python3
"""Find exact positions in run_cli.py HTML template"""
f = open('Q:\\oroboros-core\\claude-o-cli\\run_cli.py', 'r', encoding='utf-8')
c = f.read()
f.close()

body_idx = c.find('<body>')
liquid_div = c.find('<div class="liquid-bg"')
terminal_div = c.find('class="terminal"')
style_end = c.find('</style>')
head_end = c.find('</head>')

print('body at:', body_idx)
print('liquid-bg div at:', liquid_div)
print('terminal at:', terminal_div)
print('style end at:', style_end)
print('head end at:', head_end)
print()
print('Around body:', c[body_idx:body_idx+200])
print()
print('Around liquid-bg div:', c[liquid_div:liquid_div+200])
