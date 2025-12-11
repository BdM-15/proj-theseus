"""
Deep analysis of table chunks between workspaces.

Identifies which specific tables are missing and why.
"""

import json
import re
import hashlib
from pathlib import Path
from collections import defaultdict


def load_vdb_chunks(workspace_path: Path) -> list:
    """Load vdb_chunks.json from a workspace."""
    chunks_file = workspace_path / "vdb_chunks.json"
    with open(chunks_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("data", [])


def extract_table_info(content: str) -> dict:
    """Extract structured info from a Table Analysis chunk."""
    info = {
        "img_path": None,
        "caption": None,
        "structure_preview": None,
        "content_hash": hashlib.md5(content.encode()).hexdigest()[:12],
    }
    
    # Extract image path
    match = re.search(r"Image Path: ([^\n]+)", content)
    if match:
        path = match.group(1).strip()
        if path and path != "None":
            info["img_path"] = Path(path).name
    
    # Extract caption
    match = re.search(r"Caption: ([^\n]+)", content)
    if match:
        info["caption"] = match.group(1).strip()
    
    # Extract structure preview (first 200 chars)
    match = re.search(r"Structure: (.+)", content, re.DOTALL)
    if match:
        structure = match.group(1).strip()
        info["structure_preview"] = structure[:200]
    
    return info


def analyze_tables(workspace_name: str) -> list:
    """Get all table chunks with their info."""
    base_path = Path(__file__).parent.parent.parent / "rag_storage"
    ws_path = base_path / workspace_name
    
    chunks = load_vdb_chunks(ws_path)
    tables = []
    
    for chunk in chunks:
        content = chunk.get("content", "")
        if content.startswith("Table Analysis:"):
            info = extract_table_info(content)
            info["chunk_id"] = chunk.get("__id__", "")
            info["full_content"] = content
            tables.append(info)
    
    return tables


def main():
    ws1_name = "2_mcpp_drfp_2025"
    ws2_name = "38_test_mcpp"
    
    print(f"\n{'='*70}")
    print(f"DEEP TABLE ANALYSIS")
    print(f"  {ws1_name} vs {ws2_name}")
    print(f"{'='*70}\n")
    
    tables1 = analyze_tables(ws1_name)
    tables2 = analyze_tables(ws2_name)
    
    print(f"Total tables: {ws1_name}={len(tables1)}, {ws2_name}={len(tables2)}")
    
    # Group by image path
    by_path1 = defaultdict(list)
    by_path2 = defaultdict(list)
    
    for t in tables1:
        key = t["img_path"] or "NO_PATH"
        by_path1[key].append(t)
    
    for t in tables2:
        key = t["img_path"] or "NO_PATH"
        by_path2[key].append(t)
    
    print(f"\nTables with image paths: {ws1_name}={len(tables1) - len(by_path1.get('NO_PATH', []))}, "
          f"{ws2_name}={len(tables2) - len(by_path2.get('NO_PATH', []))}")
    print(f"Tables without paths: {ws1_name}={len(by_path1.get('NO_PATH', []))}, "
          f"{ws2_name}={len(by_path2.get('NO_PATH', []))}")
    
    # Find paths with different counts
    all_paths = set(by_path1.keys()) | set(by_path2.keys())
    
    print(f"\n{'='*70}")
    print("PATHS WITH DIFFERENT COUNTS:")
    print(f"{'='*70}\n")
    
    diff_found = False
    for path in sorted(all_paths):
        count1 = len(by_path1.get(path, []))
        count2 = len(by_path2.get(path, []))
        if count1 != count2:
            diff_found = True
            print(f"  {path[:60]}...")
            print(f"    {ws1_name}: {count1}")
            print(f"    {ws2_name}: {count2}")
            print()
    
    if not diff_found:
        print("  No paths with different counts found!")
    
    # Check for duplicate tables (same content hash)
    print(f"\n{'='*70}")
    print("DUPLICATE ANALYSIS (by content hash):")
    print(f"{'='*70}\n")
    
    hash_counts1 = defaultdict(int)
    hash_counts2 = defaultdict(int)
    
    for t in tables1:
        hash_counts1[t["content_hash"]] += 1
    
    for t in tables2:
        hash_counts2[t["content_hash"]] += 1
    
    dups1 = {h: c for h, c in hash_counts1.items() if c > 1}
    dups2 = {h: c for h, c in hash_counts2.items() if c > 1}
    
    print(f"  {ws1_name}: {len(dups1)} duplicate hashes (total {sum(dups1.values()) - len(dups1)} extra)")
    print(f"  {ws2_name}: {len(dups2)} duplicate hashes (total {sum(dups2.values()) - len(dups2)} extra)")
    
    # Find unique content hashes
    print(f"\n{'='*70}")
    print("UNIQUE CONTENT ANALYSIS:")
    print(f"{'='*70}\n")
    
    hashes1 = set(hash_counts1.keys())
    hashes2 = set(hash_counts2.keys())
    
    only_in_ws1 = hashes1 - hashes2
    only_in_ws2 = hashes2 - hashes1
    
    print(f"  Unique hashes only in {ws1_name}: {len(only_in_ws1)}")
    print(f"  Unique hashes only in {ws2_name}: {len(only_in_ws2)}")
    print(f"  Common hashes: {len(hashes1 & hashes2)}")
    
    if only_in_ws1:
        print(f"\n  Tables ONLY in {ws1_name}:")
        for h in only_in_ws1:
            for t in tables1:
                if t["content_hash"] == h:
                    print(f"    Hash: {h}")
                    print(f"    Path: {t['img_path'] or 'None'}")
                    print(f"    Preview: {t['structure_preview'][:100] if t['structure_preview'] else 'N/A'}...")
                    print()
                    break
    
    if only_in_ws2:
        print(f"\n  Tables ONLY in {ws2_name}:")
        for h in only_in_ws2:
            for t in tables2:
                if t["content_hash"] == h:
                    print(f"    Hash: {h}")
                    print(f"    Path: {t['img_path'] or 'None'}")
                    print(f"    Preview: {t['structure_preview'][:100] if t['structure_preview'] else 'N/A'}...")
                    print()
                    break


if __name__ == "__main__":
    main()
