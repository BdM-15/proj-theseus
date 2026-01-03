"""Analyze LightRAG's entity storage to understand field names used."""
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

lightrag_path = r'.venv\Lib\site-packages\lightrag'

# Read operate.py which handles entity extraction
print('=== Analyzing LightRAG operate.py ===')
with open(f'{lightrag_path}/operate.py', 'r', encoding='utf-8') as f:
    operate_content = f.read()

# Find where entities are upserted/stored
# Look for upsert function definitions and entity data construction
print('\nSearching for entity upsert/insert operations...')
lines = operate_content.split('\n')
in_entity_section = False
entity_lines = []

for i, line in enumerate(lines):
    if 'upsert' in line.lower() and 'entity' in line.lower():
        in_entity_section = True
        context_start = max(0, i - 5)
        context_end = min(len(lines), i + 30)
        print(f'\n--- Found entity upsert near line {i} ---')
        for j in range(context_start, context_end):
            print(f'{j}: {lines[j]}')
        print('')
        break

# Look for entity data structure
print('\nSearching for entity data dict construction...')
# Pattern: data = { ... entity_name ...}
pattern = r'data\s*=\s*\{[^}]*\}'
matches = re.findall(pattern, operate_content)
for m in matches[:5]:
    if 'entity' in m.lower() or 'content' in m.lower():
        print(f'Found: {m}')
        print('')

# Check for content field usage
print('\nSearching for content field assignment...')
for i, line in enumerate(lines):
    if "'content'" in line or '"content"' in line:
        context_start = max(0, i - 2)
        context_end = min(len(lines), i + 3)
        print(f'Line {i}:')
        for j in range(context_start, context_end):
            print(f'  {lines[j]}')
        print('')
