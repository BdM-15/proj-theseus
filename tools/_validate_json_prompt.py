import re, json, sys
t = open(r'prompts/extraction/govcon_lightrag_json.txt', encoding='utf-8').read()
blocks = re.findall(r'Output:\s*\n(\{[\s\S]*?\n\})\s*\n\s*---', t)
print(f'Found {len(blocks)} example output JSON blocks (split by ---)')
fail = 0
for i, b in enumerate(blocks, 1):
    try:
        d = json.loads(b)
        ne = len(d.get('entities', []))
        nr = len(d.get('relationships', []))
        print(f'  Example {i}: OK  entities={ne} rels={nr}')
    except Exception as e:
        fail += 1
        print(f'  Example {i}: FAIL  {e}')
        print(b[:400])
# Final example (Example 8) doesn't end with --- since it's the last; catch with another regex
final_blocks = re.findall(r'Output:\s*\n(\{[\s\S]*?\n\})\s*\n', t)
print(f'\nWith looser regex (any Output: block): found {len(final_blocks)} blocks')
for i, b in enumerate(final_blocks, 1):
    try:
        json.loads(b)
    except Exception as e:
        print(f'  Block {i} FAIL: {e}')
        print(b[:300])
        fail += 1
sys.exit(0 if fail == 0 else 1)
