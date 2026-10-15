#!/usr/bin/env python3
"""Find all \n inside JS strings in run_cli.py"""
import re

with open(r'Q:\oroboros-core\claude-o-cli\run_cli.py', 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find("return '''<!DOCTYPE")
end = content.find("# ============================================================\n# MAIN")

html_section = content[start:end]

script_match = re.search(r'<script>(.*?)</script>', html_section, re.DOTALL)
if script_match:
    js = script_match.group(1)
    # Find all \n that are inside JS string literals
    count = 0
    in_string = False
    string_char = None
    for i, ch in enumerate(js):
        if ch in ("'", '"') and (i == 0 or js[i-1] != '\\'):
            if not in_string:
                in_string = True
                string_char = ch
            elif string_char == ch:
                in_string = False
        if ch == '\\' and i+1 < len(js) and js[i+1] == 'n' and in_string:
            count += 1
            # Find the line number
            line_num = js[:i].count('\n') + 1
            print(f'Line {line_num}: \\n inside JS string')
    
    print(f'\nTotal: {count} \\n inside JS strings')
    
    # Also find all \n in the source that become actual newlines
    # These are the ones we need to fix
    lines = js.split('\n')
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("'") and not stripped.endswith("'") and not stripped.endswith('+'):
            if i+1 < len(lines):
                nxt = lines[i+1].strip()
                if nxt.startswith("'") or nxt.startswith('+'):
                    print(f'BROKEN at line {i+1}: {stripped[:80]}')
