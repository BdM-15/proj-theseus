"""Check parse cache for entity extraction output with entity types."""
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

workspace = 'rag_storage/swa_tas'

# Check parse cache which may contain raw extraction output
print('=== kv_store_parse_cache ===')
with open(f'{workspace}/kv_store_parse_cache.json', 'r', encoding='utf-8') as f:
    parse_cache = json.load(f)

print(f'Total cached items: {len(parse_cache)}')

# Look for extraction output with entity types
found_extraction = False
for key, value in list(parse_cache.items())[:20]:
    val_str = str(value) if value else ''
    
    # Check if this is entity extraction output (has tuple delimiter format)
    if '<|#|>' in val_str or 'entity_type' in val_str.lower():
        print(f'\n=== {key[:60]} ===')
        # Show a sample of the content
        print(val_str[:2000])
        found_extraction = True
        break
    
if not found_extraction:
    print('\nNo entity extraction cache found with <|#|> delimiter')
    print('Showing first 3 cache entries:')
    for i, (key, value) in enumerate(list(parse_cache.items())[:3]):
        print(f'\n--- {key[:80]} ---')
        val_str = str(value)[:500] if value else 'EMPTY'
        print(f'Type: {type(value)}')
        print(f'Content: {val_str}')
