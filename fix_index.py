#!/usr/bin/env python3
"""Fix the index() function to use DEFAULT_MODEL at runtime."""
with open(r'Q:\oroboros-core\claude-o-cli\run_cli.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the index function
old = "@app.route('/')\ndef index():\n    html = '''<!DOCTYPE"
new = "@app.route('/')\ndef index():\n    html = '''<!DOCTYPE"
# Already correct start

# Find the end of the template and add the replace
old_end = "</html>'''\n    return html"
new_end = "</html>'''\n    html = html.replace('__DEFAULT_MODEL__', DEFAULT_MODEL)\n    return html"

if old_end in content:
    content = content.replace(old_end, new_end)
    with open(r'Q:\oroboros-core\claude-o-cli\run_cli.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed index() function")
else:
    print("Could not find template end marker")
    # Show what's around that area
    idx = content.find("</html>'''")
    if idx > 0:
        print(f"Found at {idx}: ...{content[idx-20:idx+30]}...")
