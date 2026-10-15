#!/usr/bin/env python3
"""Fix all \n in JS strings within the HTML template in run_cli.py"""
import re

with open(r'Q:\oroboros-core\claude-o-cli\run_cli.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the HTML section
start = content.find("return '''<!DOCTYPE")
end = content.find("# ============================================================\n# MAIN")

if start < 0 or end < 0:
    print("Could not find HTML section")
    exit(1)

html_section = content[start:end]

# Find the script section
script_match = re.search(r'<script>(.*?)</script>', html_section, re.DOTALL)
if not script_match:
    print("Could not find script section")
    exit(1)

js = script_match.group(1)
js_start = script_match.start(1)
js_end = script_match.end(1)

# Find all \n that are inside JS string literals (between quotes)
# These come from \n in Python source and become actual newlines in HTML
# We need to find them and replace with \\n

# Strategy: find all lines that look like broken JS strings
# A broken string is a line starting with ' that doesn't end with ' or + or \\
# and the next line starts with ' or + 

lines = js.split('\n')
fixed_lines = []
broken_count = 0

for i, line in enumerate(lines):
    stripped = line.strip()
    # Check if this is a broken string continuation
    if stripped.startswith("'") and not stripped.endswith("'") and not stripped.endswith('+') and not stripped.endswith('\\\\'):
        if i+1 < len(lines):
            next_line = lines[i+1].strip()
            if next_line.startswith("'") or next_line.startswith('+'):
                # This line is broken - it needs to end with + to continue
                # Actually the issue is that \n in Python source became a real newline
                # We need to join these lines
                broken_count += 1
                print(f"Line {i+1}: BROKEN: {stripped[:80]}")
                print(f"  Next: {next_line[:80]}")
                # Join the lines
                fixed_lines.append(stripped + " +")
                continue
    fixed_lines.append(line)

if broken_count == 0:
    print("No broken strings found via line analysis")
    # Try another approach: find all \n that appear inside JS string literals
    # by looking for the pattern '...\n...' where \n is an actual newline
    # These are the ones that need to be \\n
    
    # Find all occurrences of \n in the JS that are inside string literals
    # We can do this by finding all lines that start with ' and checking if
    # the previous line also started with ' (meaning a string was broken)
    
    for i in range(1, len(lines)):
        prev = lines[i-1].strip()
        curr = lines[i].strip()
        if prev.startswith("'") and not prev.endswith("'") and not prev.endswith('+'):
            if curr.startswith("'") or curr.startswith('+'):
                print(f"Lines {i}-{i+1}: BROKEN: {prev[:60]} | {curr[:60]}")
                broken_count += 1

print(f"\nTotal broken strings found: {broken_count}")
print(f"Total JS lines: {len(lines)}")
