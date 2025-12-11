"""
Compare vdb_chunks.json between two workspaces to identify differences.

Usage:
    python tools/diagnostics/compare_vdb_chunks.py <workspace1> <workspace2>
    
Example:
    python tools/diagnostics/compare_vdb_chunks.py 2_mcpp_drfp_2025 38_test_mcpp
"""

import json
import sys
import re
from pathlib import Path
from collections import Counter


def load_vdb_chunks(workspace_path: Path) -> dict:
    """Load vdb_chunks.json from a workspace."""
    chunks_file = workspace_path / "vdb_chunks.json"
    if not chunks_file.exists():
        raise FileNotFoundError(f"vdb_chunks.json not found in {workspace_path}")
    
    with open(chunks_file, "r", encoding="utf-8") as f:
        return json.load(f)


def categorize_chunk(content: str) -> str:
    """Categorize a chunk by its content type."""
    if content.startswith("Table Analysis:"):
        return "table"
    elif content.startswith("Image Content Analysis:"):
        return "image"
    elif content.startswith("Mathematical Equation Analysis:"):
        return "equation"
    else:
        return "text"


def extract_table_paths(content: str) -> str | None:
    """Extract image path from Table Analysis chunk."""
    match = re.search(r"Image Path: ([^\n]+)", content)
    if match:
        # Extract just the filename for comparison
        path = match.group(1).strip()
        if path and path != "None":
            return Path(path).name
    return None


def analyze_workspace(workspace_path: Path) -> dict:
    """Analyze a workspace's vdb_chunks."""
    data = load_vdb_chunks(workspace_path)
    chunks = data.get("data", [])
    
    analysis = {
        "total_chunks": len(chunks),
        "by_type": Counter(),
        "table_paths": set(),
        "text_lengths": [],
        "chunk_ids": set(),
    }
    
    for chunk in chunks:
        content = chunk.get("content", "")
        chunk_id = chunk.get("__id__", "")
        
        category = categorize_chunk(content)
        analysis["by_type"][category] += 1
        analysis["chunk_ids"].add(chunk_id)
        
        if category == "table":
            path = extract_table_paths(content)
            if path:
                analysis["table_paths"].add(path)
        elif category == "text":
            analysis["text_lengths"].append(len(content))
    
    return analysis


def compare_workspaces(ws1_name: str, ws2_name: str):
    """Compare two workspaces and print differences."""
    base_path = Path(__file__).parent.parent.parent / "rag_storage"
    
    ws1_path = base_path / ws1_name
    ws2_path = base_path / ws2_name
    
    print(f"\n{'='*70}")
    print(f"COMPARING VDB_CHUNKS")
    print(f"  Workspace 1: {ws1_name}")
    print(f"  Workspace 2: {ws2_name}")
    print(f"{'='*70}\n")
    
    # Load and analyze both workspaces
    try:
        ws1 = analyze_workspace(ws1_path)
        ws2 = analyze_workspace(ws2_path)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return
    
    # Compare totals
    print("CHUNK COUNTS:")
    print(f"  {'Type':<20} {ws1_name:<15} {ws2_name:<15} {'Diff':<10}")
    print(f"  {'-'*60}")
    
    all_types = set(ws1["by_type"].keys()) | set(ws2["by_type"].keys())
    for chunk_type in sorted(all_types):
        count1 = ws1["by_type"].get(chunk_type, 0)
        count2 = ws2["by_type"].get(chunk_type, 0)
        diff = count2 - count1
        diff_str = f"+{diff}" if diff > 0 else str(diff)
        print(f"  {chunk_type:<20} {count1:<15} {count2:<15} {diff_str:<10}")
    
    total1 = ws1["total_chunks"]
    total2 = ws2["total_chunks"]
    diff = total2 - total1
    diff_str = f"+{diff}" if diff > 0 else str(diff)
    print(f"  {'-'*60}")
    print(f"  {'TOTAL':<20} {total1:<15} {total2:<15} {diff_str:<10}")
    
    # Compare table paths
    print(f"\n{'='*70}")
    print("TABLE ANALYSIS COMPARISON:")
    print(f"{'='*70}\n")
    
    tables1 = ws1["table_paths"]
    tables2 = ws2["table_paths"]
    
    only_in_ws1 = tables1 - tables2
    only_in_ws2 = tables2 - tables1
    common = tables1 & tables2
    
    print(f"  Tables in both workspaces: {len(common)}")
    print(f"  Tables only in {ws1_name}: {len(only_in_ws1)}")
    print(f"  Tables only in {ws2_name}: {len(only_in_ws2)}")
    
    if only_in_ws1:
        print(f"\n  Tables MISSING from {ws2_name}:")
        for path in sorted(only_in_ws1):
            print(f"    - {path}")
    
    if only_in_ws2:
        print(f"\n  Tables EXTRA in {ws2_name}:")
        for path in sorted(only_in_ws2):
            print(f"    + {path}")
    
    # Text chunk statistics
    print(f"\n{'='*70}")
    print("TEXT CHUNK STATISTICS:")
    print(f"{'='*70}\n")
    
    if ws1["text_lengths"]:
        avg1 = sum(ws1["text_lengths"]) / len(ws1["text_lengths"])
        min1 = min(ws1["text_lengths"])
        max1 = max(ws1["text_lengths"])
        print(f"  {ws1_name}:")
        print(f"    Count: {len(ws1['text_lengths'])}")
        print(f"    Avg length: {avg1:,.0f} chars")
        print(f"    Min/Max: {min1:,} / {max1:,} chars")
    
    if ws2["text_lengths"]:
        avg2 = sum(ws2["text_lengths"]) / len(ws2["text_lengths"])
        min2 = min(ws2["text_lengths"])
        max2 = max(ws2["text_lengths"])
        print(f"\n  {ws2_name}:")
        print(f"    Count: {len(ws2['text_lengths'])}")
        print(f"    Avg length: {avg2:,.0f} chars")
        print(f"    Min/Max: {min2:,} / {max2:,} chars")
    
    # Sample chunk content comparison
    print(f"\n{'='*70}")
    print("SAMPLE TABLE CHUNK FORMAT COMPARISON:")
    print(f"{'='*70}\n")
    
    # Get first table chunk from each workspace
    for ws_name, ws_path in [(ws1_name, ws1_path), (ws2_name, ws2_path)]:
        data = load_vdb_chunks(ws_path)
        for chunk in data.get("data", []):
            content = chunk.get("content", "")
            if content.startswith("Table Analysis:"):
                print(f"  {ws_name} - First 500 chars:")
                print(f"  {'-'*50}")
                print(f"  {content[:500]}...")
                print()
                break


def main():
    if len(sys.argv) < 3:
        # Default comparison
        ws1 = "2_mcpp_drfp_2025"
        ws2 = "38_test_mcpp"
        print(f"Using default workspaces: {ws1} vs {ws2}")
    else:
        ws1 = sys.argv[1]
        ws2 = sys.argv[2]
    
    compare_workspaces(ws1, ws2)


if __name__ == "__main__":
    main()
