#!/usr/bin/env python3
"""Fix oroboros_cli.py - replace embedded HTML with file read"""
f = open('Q:\\oroboros-core\\claude-o-cli\\oroboros_cli.py', 'r', encoding='utf-8')
c = f.read()
f.close()

idx = c.find('def index():')
end_idx = c.find("if __name__ == '__main__':")

new_index = "# --- HTML UI ---\n@app.route('/')\ndef index():\n    gui_file = GUI_DIR / 'index.html'\n    if gui_file.exists():\n        return gui_file.read_text(encoding='utf-8')\n    return 'GUI not found', 404\n\n"

new_c = c[:idx] + new_index + c[end_idx:]
f2 = open('Q:\\oroboros-core\\claude-o-cli\\oroboros_cli.py', 'w', encoding='utf-8')
f2.write(new_c)
f2.close()
print('Done. New size:', len(new_c))
