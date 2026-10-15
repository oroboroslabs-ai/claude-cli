#!/usr/bin/env python3
"""Verify the 20 loop patterns engine."""
import urllib.request, json

r = urllib.request.urlopen('http://127.0.0.1:5000/api/loops', timeout=5)
d = json.loads(r.read())
print('20 Loops Engine: ACTIVE')
for p in d['patterns']:
    pid = p['id']
    name = p['name']
    cat = p['category']
    print(f'  {pid:>2s}. {name:35s} [{cat}]')
