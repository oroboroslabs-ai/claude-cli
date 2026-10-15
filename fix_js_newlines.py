#!/usr/bin/env python3
"""Fix all \n inside JS strings in run_cli.py by replacing with \\n"""
import re

with open(r'Q:\oroboros-core\claude-o-cli\run_cli.py', 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find("return '''<!DOCTYPE")
end = content.find("# ============================================================\n# MAIN")

html_section = content[start:end]

script_match = re.search(r'<script>(.*?)</script>', html_section, re.DOTALL)
if script_match:
    js = script_match.group(1)
    js_start = script_match.start(1)
    js_end = script_match.end(1)
    
    # Fix: replace \n with \\n inside JS string literals
    # We need to find \n that are between quotes in the JS
    fixed_js = []
    in_string = False
    string_char = None
    changes = 0
    
    for i, ch in enumerate(js):
        if ch in ("'", '"') and (i == 0 or js[i-1] != '\\'):
            if not in_string:
                in_string = True
                string_char = ch
            elif string_char == ch:
                in_string = False
        if ch == '\\' and i+1 < len(js) and js[i+1] == 'n' and in_string:
            fixed_js.append('\\\\n')
            changes += 1
        else:
            fixed_js.append(ch)
    
    fixed_js_str = ''.join(fixed_js)
    
    # Replace in content
    new_content = content[:js_start] + fixed_js_str + content[js_end:]
    
    with open(r'Q:\oroboros-core\claude-o-cli\run_cli.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f'Fixed {changes} \\n -> \\\\n inside JS strings')
else:
    print('Could not find script section')
