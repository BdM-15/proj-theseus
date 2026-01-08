#!/usr/bin/env python
"""
GovCon Domain Ontology Bootstrap CLI Tool

Manual bootstrapping of the GovCon domain ontology into a LightRAG workspace.
Use this tool to:
- Bootstrap a new workspace with domain knowledge
- Re-bootstrap an existing workspace with updated ontology
- Check bootstrap status of a workspace

Usage:
    python tools/bootstrap_ontology.py bootstrap [workspace_name] [--force]
    python tools/bootstrap_ontology.py status [workspace_name]
    python tools/bootstrap_ontology.py validate
    python tools/bootstrap_ontology.py stats

Examples:
    # Bootstrap default workspace
    python tools/bootstrap_ontology.py bootstrap
    
    # Bootstrap specific workspace
    python tools/bootstrap_ontology.py bootstrap swa_tas_3
    
    # Force re-bootstrap
    python tools/bootstrap_ontology.py bootstrap swa_tas_3 --force
    
    # Check status
    python tools/bootstrap_ontology.py status swa_tas_3
    
    # Validate ontology without bootstrapping
    python tools/bootstrap_ontology.py validate

Environment:
    WORKING_DIR: Default workspace directory (from .env)
    RAG_STORAGE: Base path for rag_storage (default: ./rag_storage)
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env BEFORE any lightrag imports
from dotenv import load_dotenv
load_dotenv()


def get_workspace_path(workspace_name: str | None = None) -> str:
    """Get full path to workspace directory."""
    base_path = os.getenv("RAG_STORAGE", "./rag_storage")
    
    if workspace_name:
        return os.path.join(base_path, workspace_name)
    
    # Try to get from WORKING_DIR
    working_dir = os.getenv("WORKING_DIR")
    if working_dir:
        return working_dir
    
    # Default
    return os.path.join(base_path, "default")


def cmd_stats(args):
    """Show ontology statistics."""
    from src.ontology.govcon_kg import get_ontology_stats
    
    print("=" * 60)
    print("GovCon Domain Ontology Statistics")
    print("=" * 60)
    
    stats = get_ontology_stats()
    
    print(f"\n📊 Total Counts:")
    print(f"   Entities:      {stats['total_entities']}")
    print(f"   Relationships: {stats['total_relationships']}")
    print(f"   Chunks:        {stats['total_chunks']}")
    
    print(f"\n📁 By Module:")
    for module, counts in stats["modules"].items():
        print(f"   {module:20s} {counts['entities']:3d}E / {counts['relationships']:2d}R / {counts['chunks']:2d}C")
    
    print("\n✅ Done")


def cmd_validate(args):
    """Validate ontology without bootstrapping."""
    from src.ontology.govcon_kg import validate_ontology, get_ontology_stats
    
    print("=" * 60)
    print("GovCon Domain Ontology Validation")
    print("=" * 60)
    
    # Get stats
    stats = get_ontology_stats()
    print(f"\n📊 Loaded: {stats['total_entities']} entities, "
          f"{stats['total_relationships']} relationships, {stats['total_chunks']} chunks")
    
    # Validate
    print("\n🔍 Validating...")
    is_valid, errors = validate_ontology()
    
    if is_valid:
        print("   ✅ All validations passed!")
    else:
        print(f"   ❌ Found {len(errors)} issues:")
        for error in errors:
            print(f"      - {error}")
    
    return 0 if is_valid else 1


def cmd_status(args):
    """Check bootstrap status of a workspace."""
    from src.ontology.bootstrap import check_bootstrap_status
    
    workspace_path = get_workspace_path(args.workspace)
    
    print("=" * 60)
    print("Bootstrap Status Check")
    print("=" * 60)
    print(f"\n📂 Workspace: {workspace_path}")
    
    if not os.path.exists(workspace_path):
        print("   ❌ Workspace directory does not exist")
        return 1
    
    result = asyncio.run(check_bootstrap_status(workspace_path))
    
    if result["bootstrapped"]:
        print(f"   ✅ Ontology bootstrapped")
        print(f"   📅 At: {result['bootstrapped_at']}")
    else:
        print("   ⚠️ Ontology NOT bootstrapped")
        print("   Run: python tools/bootstrap_ontology.py bootstrap")
    
    return 0


async def _do_bootstrap(workspace_path: str, force: bool) -> dict:
    """Perform the actual bootstrap operation."""
    # Import LightRAG setup (this initializes the instance)
    from lightrag import LightRAG
    from src.server.config import global_args
    
    # Create minimal LightRAG instance for this workspace
    print(f"\n🔧 Initializing LightRAG for {workspace_path}...")
    
    # Override working_dir for this workspace
    rag = LightRAG(
        working_dir=workspace_path,
        llm_model_func=global_args.get("llm_model_func"),
        embedding_func=global_args.get("embedding_func"),
        llm_model_name=global_args.get("llm_model_name"),
        embedding_model_name=global_args.get("embedding_model_name"),
        graph_storage=global_args.get("graph_storage", "NetworkXStorage"),
    )
    
    # Now bootstrap
    from src.ontology.bootstrap import bootstrap_govcon_ontology
    
    result = await bootstrap_govcon_ontology(rag, workspace_path, force=force)
    return result


def cmd_bootstrap(args):
    """Bootstrap ontology into a workspace."""
    from src.ontology.govcon_kg import get_ontology_stats, validate_ontology
    
    workspace_path = get_workspace_path(args.workspace)
    
    print("=" * 60)
    print("GovCon Domain Ontology Bootstrap")
    print("=" * 60)
    print(f"\n📂 Workspace: {workspace_path}")
    print(f"🔄 Force: {args.force}")
    
    # Validate first
    print("\n🔍 Pre-validating ontology...")
    is_valid, errors = validate_ontology()
    if not is_valid:
        print(f"   ⚠️ {len(errors)} validation issues (will proceed)")
    else:
        print("   ✅ Validation passed")
    
    # Get stats
    stats = get_ontology_stats()
    print(f"\n📊 Will inject:")
    print(f"   - {stats['total_entities']} entities")
    print(f"   - {stats['total_relationships']} relationships")
    print(f"   - {stats['total_chunks']} knowledge chunks")
    
    # Confirm
    if not args.yes:
        response = input("\n⚡ Proceed with bootstrap? [y/N] ")
        if response.lower() != 'y':
            print("Cancelled.")
            return 0
    
    # Create workspace dir if needed
    os.makedirs(workspace_path, exist_ok=True)
    
    # Do bootstrap
    print("\n🚀 Starting bootstrap...")
    try:
        result = asyncio.run(_do_bootstrap(workspace_path, args.force))
    except Exception as e:
        print(f"\n❌ Bootstrap failed: {e}")
        return 1
    
    # Report result
    if result["status"] == "success":
        print(f"\n✅ Bootstrap successful!")
        print(f"   Entities:      {result['entities_added']}")
        print(f"   Relationships: {result['relationships_added']}")
        print(f"   Chunks:        {result['chunks_added']}")
        print(f"   Duration:      {result['duration_seconds']:.2f}s")
    elif result["status"] == "already_bootstrapped":
        print(f"\n⚠️ Already bootstrapped at {result['bootstrapped_at']}")
        print("   Use --force to re-bootstrap")
    else:
        print(f"\n❌ Bootstrap failed: {result.get('error', 'Unknown error')}")
        return 1
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="GovCon Domain Ontology Bootstrap Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # bootstrap command
    bootstrap_parser = subparsers.add_parser(
        "bootstrap", 
        help="Bootstrap ontology into a workspace"
    )
    bootstrap_parser.add_argument(
        "workspace",
        nargs="?",
        help="Workspace name (uses WORKING_DIR from .env if not specified)"
    )
    bootstrap_parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force re-bootstrap even if already done"
    )
    bootstrap_parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompt"
    )
    bootstrap_parser.set_defaults(func=cmd_bootstrap)
    
    # status command
    status_parser = subparsers.add_parser(
        "status",
        help="Check bootstrap status of a workspace"
    )
    status_parser.add_argument(
        "workspace",
        nargs="?",
        help="Workspace name"
    )
    status_parser.set_defaults(func=cmd_status)
    
    # validate command
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate ontology without bootstrapping"
    )
    validate_parser.set_defaults(func=cmd_validate)
    
    # stats command
    stats_parser = subparsers.add_parser(
        "stats",
        help="Show ontology statistics"
    )
    stats_parser.set_defaults(func=cmd_stats)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
