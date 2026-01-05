#!/usr/bin/env python3
"""
Debug VDB structure to understand data format.
"""

import json
import os

def main():
    workspace = "./rag_storage/swa_tas"
    vdb_file = os.path.join(workspace, "vdb_entities.json")
    
    with open(vdb_file, "r", encoding="utf-8") as f:
        vdb_data = json.load(f)
    
    print(f"VDB data type: {type(vdb_data)}")
    
    if isinstance(vdb_data, list):
        print(f"List length: {len(vdb_data)}")
        if vdb_data:
            print(f"\nFirst entry type: {type(vdb_data[0])}")
            if isinstance(vdb_data[0], dict):
                print(f"First entry keys: {list(vdb_data[0].keys())}")
            elif isinstance(vdb_data[0], list):
                print(f"First entry (nested list) length: {len(vdb_data[0])}")
                if vdb_data[0]:
                    print(f"First nested item: {vdb_data[0][0][:100] if isinstance(vdb_data[0][0], str) else vdb_data[0][0]}")
    elif isinstance(vdb_data, dict):
        print(f"Dict keys count: {len(vdb_data)}")
        keys = list(vdb_data.keys())[:5]
        print(f"First 5 keys: {keys}")
    
    # Try to find table entries by searching strings
    print("\n--- Searching for 'table' in data ---")
    
    table_count = 0
    sample_found = None
    
    if isinstance(vdb_data, list):
        for i, entry in enumerate(vdb_data):
            # Check if entry is a list with entity name as first element
            if isinstance(entry, list) and len(entry) > 0:
                entity_str = str(entry[0]).lower() if entry else ""
                if "table" in entity_str:
                    table_count += 1
                    if not sample_found:
                        sample_found = entry
                        print(f"\nSample table entry structure:")
                        print(f"  Entry length: {len(entry)}")
                        for j, item in enumerate(entry[:5]):
                            if isinstance(item, list) and len(item) > 10:
                                print(f"  [{j}]: list of {len(item)} items (likely vector)")
                            else:
                                preview = str(item)[:200] if isinstance(item, str) else str(item)
                                print(f"  [{j}]: {preview}")
    
    print(f"\nTable entries found: {table_count}")

if __name__ == "__main__":
    main()
