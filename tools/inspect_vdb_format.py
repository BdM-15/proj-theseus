#!/usr/bin/env python3
"""
Deep inspection of VDB data format.
"""

import json
import os

def main():
    workspace = "./rag_storage/swa_tas"
    vdb_file = os.path.join(workspace, "vdb_entities.json")
    
    with open(vdb_file, "r", encoding="utf-8") as f:
        vdb_data = json.load(f)
    
    data = vdb_data.get("data", [])
    print(f"Data type: {type(data)}")
    print(f"Data length: {len(data)}")
    
    if isinstance(data, dict):
        print(f"Dict keys (first 10): {list(data.keys())[:10]}")
        first_key = list(data.keys())[0]
        first_val = data[first_key]
        print(f"\nFirst entry key: {first_key}")
        print(f"First entry value type: {type(first_val)}")
        if isinstance(first_val, dict):
            print(f"Value keys: {list(first_val.keys())}")
        elif isinstance(first_val, list):
            print(f"Value length: {len(first_val)}")
    elif isinstance(data, list):
        print(f"First entry type: {type(data[0])}")
        if isinstance(data[0], dict):
            print(f"First entry keys: {list(data[0].keys())}")
        elif isinstance(data[0], list):
            print(f"First entry length: {len(data[0])}")
            for i, elem in enumerate(data[0][:5]):
                if isinstance(elem, list) and len(elem) > 10:
                    print(f"  [{i}]: list of {len(elem)} floats")
                else:
                    print(f"  [{i}]: {type(elem).__name__} = {str(elem)[:100]}")

if __name__ == "__main__":
    main()
