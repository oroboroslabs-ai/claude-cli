#!/usr/bin/env python3
"""Find key positions in run_cli.py"""
f = open('Q:\\oroboros-core\\claude-o-cli\\run_cli.py', 'r', encoding='utf-8')
c = f.read()
f.close()
print('liquid-bg at:', c.find('liquid-bg'))
print('clawd at:', c.find('clawd'))
print('thinking at:', c.find('thinking'))
print('def index at:', c.find('def index'))
print('if __name__ at:', c.find("if __name__"))
print('File length:', len(c))
