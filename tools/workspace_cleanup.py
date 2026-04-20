"""
Workspace Cleanup Tool
======================

Interactively clear Neo4j graph data and/or rag_storage files for one or all workspaces.

Usage:
    python tools/workspace_cleanup.py              # Interactive walkthrough (default)
    python tools/workspace_cleanup.py --workspace NAME          # Non-interactive single workspace
    python tools/workspace_cleanup.py --workspace NAME --neo4j-only
    python tools/workspace_cleanup.py --workspace NAME --storage-only
    python tools/workspace_cleanup.py --all                     # Wipe everything (prompted)

What gets deleted per workspace:
    - Neo4j nodes/relationships with the workspace label
    - rag_storage/{workspace}/ folder (KV stores, VDB files, logs, MinerU output)
    - MinerU artifacts now live under rag_storage/{workspace}/mineru/
    - Legacy orphaned MinerU output dirs in rag_storage root (_{8hex} pattern directories)
"""

import os
import re
import shutil
import sys
from pathlib import Path

# Force UTF-8 output on Windows consoles (avoids cp1252 UnicodeEncodeError)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# tools/ → project root
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.inference.neo4j_graph_io import Neo4jGraphIO


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

SYSTEM_LABELS = {"__Entity__", "__Relation__", "__Community__"}
HEX_SUFFIX = re.compile(r"_[0-9a-f]{8}$", re.IGNORECASE)

DIVIDER = "─" * 70


def _rag_storage_root() -> Path:
    """Parent rag_storage directory (WORKING_DIR env var)."""
    working_dir = os.getenv("WORKING_DIR", "./rag_storage")
    return Path(working_dir).resolve()


def _folder_size_mb(path: Path) -> float:
    """Recursively sum file sizes in path, return MB."""
    total = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
    return round(total / 1024 / 1024, 1)


def _neo4j_workspaces(neo4j_io: Neo4jGraphIO) -> dict[str, int]:
    """Return {workspace_label: node_count} for all non-system labels."""
    with neo4j_io.driver.session(database=neo4j_io.database) as session:
        result = session.run("CALL db.labels() YIELD label RETURN collect(label) as labels")
        record = result.single()
        labels = record["labels"] if record else []

        counts: dict[str, int] = {}
        for label in labels:
            if label in SYSTEM_LABELS:
                continue
            rec = session.run(f"MATCH (n:`{label}`) RETURN count(n) as c").single()
            count = rec["c"] if rec else 0
            if count > 0:
                counts[label] = count
    return counts


def _storage_workspaces(rag_root: Path) -> dict[str, float]:
    """Return {workspace_name: size_mb} for subdirectories that look like workspaces."""
    result: dict[str, float] = {}
    if not rag_root.exists():
        return result
    for entry in rag_root.iterdir():
        if entry.is_dir() and not HEX_SUFFIX.search(entry.name):
            result[entry.name] = _folder_size_mb(entry)
    return result


def _orphaned_mineru_dirs(rag_root: Path) -> list[Path]:
    """Dirs in rag_storage root that match the MinerU _{8hex} suffix pattern."""
    if not rag_root.exists():
        return []
    return [e for e in rag_root.iterdir() if e.is_dir() and HEX_SUFFIX.search(e.name)]


def _delete_neo4j_workspace(neo4j_io: Neo4jGraphIO, workspace_name: str) -> int:
    """Delete all Neo4j nodes for workspace. Returns count deleted."""
    with neo4j_io.driver.session(database=neo4j_io.database) as session:
        rec = session.run(f"MATCH (n:`{workspace_name}`) RETURN count(n) as c").single()
        count = rec["c"] if rec else 0
        if count > 0:
            session.run(f"MATCH (n:`{workspace_name}`) DETACH DELETE n")
    return count


def _delete_storage_workspace(workspace_name: str, rag_root: Path) -> bool:
    """
    Delete rag_storage/{workspace} folder. Returns True if it existed.

    Windows-safe: log files opened by the server use FILE_SHARE_DELETE
    (see ShareDeleteRotatingFileHandler in logging_config.py), so we can
    rename them out of the workspace folder while the server is running.
    The server keeps writing to the orphaned temp path; the workspace dir
    becomes empty and rmdir succeeds.
    """
    import tempfile

    ws_path = rag_root / workspace_name
    if not ws_path.exists():
        return False

    # ── Phase 1: delete everything we can ───────────────────────────────────
    locked_files: list[Path] = []

    def _on_exc(func, path, exc):
        if isinstance(exc, (PermissionError, OSError)):
            if Path(path).is_file():
                locked_files.append(Path(path))
            # ENOTEMPTY cascades are harmless — we'll sweep dirs in phase 3
        else:
            raise exc

    try:
        shutil.rmtree(ws_path, onexc=_on_exc)
    except TypeError:  # Python < 3.12
        def _on_err(func, path, exc_info):
            exc = exc_info[1]
            if isinstance(exc, (PermissionError, OSError)):
                if Path(path).is_file():
                    locked_files.append(Path(path))
            else:
                raise exc
        shutil.rmtree(ws_path, onerror=_on_err)

    if not locked_files:
        return True

    # ── Phase 2: rename locked files to temp (FILE_SHARE_DELETE allows this) ─
    tmp_dir = Path(tempfile.gettempdir())
    still_locked: list[Path] = []

    for f in locked_files:
        if not f.exists():
            continue
        dest = tmp_dir / f"{workspace_name}_{f.name}"
        try:
            f.rename(dest)
        except OSError:
            still_locked.append(f)

    # ── Phase 3: remove now-empty directories bottom-up ─────────────────────
    for dirpath in sorted(ws_path.rglob("*"), reverse=True):
        if dirpath.is_dir():
            try:
                dirpath.rmdir()
            except OSError:
                pass
    try:
        ws_path.rmdir()
    except OSError:
        pass

    # ── Report ────────────────────────────────────────────────────────────────
    if still_locked:
        print(f"\n  ⚠️  {len(still_locked)} file(s) could not be removed (server lock - restart server and retry):")
        for f in still_locked:
            try:
                print(f"     - {f.relative_to(rag_root)}")
            except ValueError:
                print(f"     - {f}")

    return True


def _handle_orphaned_dirs(rag_root: Path) -> None:
    """Prompt to delete legacy orphaned MinerU output dirs in rag_storage root."""
    orphans = _orphaned_mineru_dirs(rag_root)
    if not orphans:
        return
    print(f"\n   🔍 Found {len(orphans)} legacy MinerU output dir(s) in rag_storage root:")
    for d in orphans:
        print(f"      - {d.name}")
    ans = input(f"\n   Delete these {len(orphans)} legacy orphaned dir(s)? (yes/no): ").strip().lower()
    if ans in ("yes", "y"):
        for d in orphans:
            shutil.rmtree(d)
            print(f"   ✅ Deleted: {d.name}")
    else:
        print("   ⏭️  Skipped")


# ═══════════════════════════════════════════════════════════════════════════════
# Interactive walkthrough
# ═══════════════════════════════════════════════════════════════════════════════

def interactive_walkthrough() -> None:
    """Full interactive workspace selection and cleanup flow."""
    print(f"\n{'═' * 70}")
    print("  🧹  Workspace Cleanup Tool")
    print(f"{'═' * 70}\n")

    neo4j_io = Neo4jGraphIO()
    rag_root = _rag_storage_root()
    active_workspace = neo4j_io.workspace

    print(f"  Active workspace : {active_workspace}")
    print(f"  rag_storage root : {rag_root}\n")
    print(f"  {DIVIDER}")
    print("  Scanning workspaces…")

    neo4j_ws = _neo4j_workspaces(neo4j_io)
    storage_ws = _storage_workspaces(rag_root)

    # Merge all known workspace names
    all_names = sorted(set(neo4j_ws.keys()) | set(storage_ws.keys()))

    if not all_names:
        print("\n  ℹ️  No workspaces found in Neo4j or rag_storage.")
        neo4j_io.close()
        return

    # ── Display table ────────────────────────────────────────────────────────
    print(f"\n  {'#':<4}  {'Workspace':<35}  {'Neo4j nodes':>11}  {'Storage':>8}  {'':>8}")
    print(f"  {DIVIDER}")

    for idx, name in enumerate(all_names, start=1):
        nodes = neo4j_ws.get(name, 0)
        size = storage_ws.get(name)
        size_str = f"{size} MB" if size is not None else "—"
        nodes_str = f"{nodes:,}" if nodes else "—"
        marker = "← active" if name == active_workspace else ""
        print(f"  [{idx:<2}]  {name:<35}  {nodes_str:>11}  {size_str:>8}  {marker}")

    print(f"\n  [A ]  Delete ALL workspaces (Neo4j + rag_storage)")
    print(f"  [Q ]  Quit")
    print(f"\n  {DIVIDER}")

    # ── Workspace selection ──────────────────────────────────────────────────
    choice = input("\n  Select workspace (number, A, or Q): ").strip().upper()

    if choice == "Q":
        print("\n  Bye!\n")
        neo4j_io.close()
        return

    if choice == "A":
        _interactive_delete_all(neo4j_io, neo4j_ws, all_names, rag_root)
        neo4j_io.close()
        return

    if not choice.isdigit() or not (1 <= int(choice) <= len(all_names)):
        print(f"\n  ❌ Invalid selection: '{choice}'\n")
        neo4j_io.close()
        return

    selected = all_names[int(choice) - 1]
    _interactive_delete_one(neo4j_io, selected, neo4j_ws, storage_ws, rag_root, active_workspace)
    neo4j_io.close()


def _interactive_delete_one(
    neo4j_io: Neo4jGraphIO,
    workspace_name: str,
    neo4j_ws: dict[str, int],
    storage_ws: dict[str, float],
    rag_root: Path,
    active_workspace: str,
) -> None:
    """Show details for one workspace and prompt what to delete."""
    nodes = neo4j_ws.get(workspace_name, 0)
    size = storage_ws.get(workspace_name)
    active_tag = "  ← active workspace" if workspace_name == active_workspace else ""

    print(f"\n  {DIVIDER}")
    print(f"  Selected : {workspace_name}{active_tag}")
    print(f"  Neo4j    : {nodes:,} nodes" if nodes else "  Neo4j    : —")
    print(f"  Storage  : {size} MB  ({rag_root / workspace_name})" if size is not None else "  Storage  : — (folder not found)")

    has_neo4j = nodes > 0
    has_storage = size is not None

    if not has_neo4j and not has_storage:
        print("\n  ℹ️  Nothing to delete for this workspace.\n")
        return

    print(f"\n  What would you like to delete?")
    options: list[tuple[str, str]] = []
    if has_neo4j and has_storage:
        options.append(("1", f"Both Neo4j ({nodes:,} nodes) + rag_storage ({size} MB)  — full reset"))
        options.append(("2", f"Neo4j only  ({nodes:,} nodes)  — keeps VDB/KV caches"))
        options.append(("3", f"rag_storage only  ({size} MB)  — keeps graph"))
    elif has_neo4j:
        options.append(("1", f"Neo4j ({nodes:,} nodes)"))
    else:
        options.append(("1", f"rag_storage ({size} MB)"))
    options.append(("Q", "Cancel"))

    for key, label in options:
        print(f"    [{key}]  {label}")

    ans = input("\n  Choice: ").strip().upper()

    if ans == "Q" or ans not in {k for k, _ in options}:
        print("\n  ❌ Cancelled\n")
        return

    # Determine what to delete
    delete_neo4j = False
    delete_storage = False
    if has_neo4j and has_storage:
        delete_neo4j = ans in ("1", "2")
        delete_storage = ans in ("1", "3")
    elif has_neo4j:
        delete_neo4j = True
    else:
        delete_storage = True

    # Final confirmation
    targets = []
    if delete_neo4j:
        targets.append(f"{nodes:,} Neo4j nodes")
    if delete_storage:
        targets.append(f"rag_storage/{workspace_name}/")
    print(f"\n  ⚠️  About to delete: {', '.join(targets)}")
    confirm = input("  Confirm? (yes/no): ").strip().lower()
    if confirm not in ("yes", "y"):
        print("\n  ❌ Cancelled\n")
        return

    print()
    if delete_neo4j:
        deleted = _delete_neo4j_workspace(neo4j_io, workspace_name)
        print(f"  ✅ Deleted {deleted:,} Neo4j nodes from '{workspace_name}'")
    if delete_storage:
        found = _delete_storage_workspace(workspace_name, rag_root)
        if found:
            print(f"  ✅ Deleted rag_storage/{workspace_name}/")
        else:
            print(f"  ℹ️  rag_storage/{workspace_name}/ was not found")

    # Offer orphan cleanup if we just cleared storage
    if delete_storage:
        _handle_orphaned_dirs(rag_root)

    print(f"\n  ✅ Done!\n")


def _interactive_delete_all(
    neo4j_io: Neo4jGraphIO,
    neo4j_ws: dict[str, int],
    all_names: list[str],
    rag_root: Path,
) -> None:
    """Wipe every workspace — Neo4j + rag_storage."""
    total_nodes = sum(neo4j_ws.values())
    storage_dirs = [rag_root / n for n in all_names if (rag_root / n).exists()]
    total_mb = sum(_folder_size_mb(d) for d in storage_dirs)

    print(f"\n  {DIVIDER}")
    print(f"  ⚠️  DELETE ALL WORKSPACES")
    print(f"  Neo4j    : {total_nodes:,} total nodes across {len(neo4j_ws)} workspaces")
    print(f"  Storage  : {total_mb} MB across {len(storage_dirs)} workspace folders")
    print(f"  {DIVIDER}")
    print(f"\n  What would you like to delete?")
    print(f"    [1]  Both Neo4j + rag_storage (complete wipe)")
    print(f"    [2]  Neo4j only")
    print(f"    [3]  rag_storage only")
    print(f"    [Q]  Cancel")

    ans = input("\n  Choice: ").strip().upper()
    if ans == "Q" or ans not in ("1", "2", "3"):
        print("\n  ❌ Cancelled\n")
        return

    delete_neo4j = ans in ("1", "2")
    delete_storage = ans in ("1", "3")

    # Double-confirm
    print(f"\n  Type DELETE ALL to confirm wiping {', '.join(filter(None, ['Neo4j' if delete_neo4j else '', 'rag_storage' if delete_storage else '']))}: ", end="")
    confirm = input().strip()
    if confirm != "DELETE ALL":
        print("\n  ❌ Cancelled\n")
        return

    print()
    if delete_neo4j:
        with neo4j_io.driver.session(database=neo4j_io.database) as session:
            session.run("MATCH (n) DETACH DELETE n")
        print(f"  ✅ Deleted all {total_nodes:,} Neo4j nodes")

    if delete_storage:
        for d in storage_dirs:
            _delete_storage_workspace(d.name, rag_root)
            print(f"  ✅ Deleted rag_storage/{d.name}/ (any locked files reported above)")
        _handle_orphaned_dirs(rag_root)

    print(f"\n  ✅ Done!\n")


# ═══════════════════════════════════════════════════════════════════════════════
# Non-interactive (CLI flags) path
# ═══════════════════════════════════════════════════════════════════════════════

def clear_workspace(workspace_name: str = None, neo4j_only: bool = False, storage_only: bool = False):
    """Non-interactive: clear a specific workspace."""
    neo4j_io = Neo4jGraphIO()

    if workspace_name is None:
        workspace_name = neo4j_io.workspace

    rag_root = _rag_storage_root()

    print(f"\n🗑️  Clearing workspace: {workspace_name}")
    print(f"   rag_storage root : {rag_root}")

    neo4j_count = 0
    if not storage_only:
        with neo4j_io.driver.session(database=neo4j_io.database) as session:
            rec = session.run(f"MATCH (n:`{workspace_name}`) RETURN count(n) as c").single()
            neo4j_count = rec["c"] if rec else 0
        print(f"   Neo4j nodes      : {neo4j_count:,}")

    ws_path = rag_root / workspace_name
    storage_exists = ws_path.exists()
    if not neo4j_only:
        print(f"   rag_storage dir  : {'exists' if storage_exists else 'not found'} ({ws_path})")

    parts = []
    if not storage_only and neo4j_count > 0:
        parts.append(f"{neo4j_count:,} Neo4j nodes")
    if not neo4j_only and storage_exists:
        parts.append(f"rag_storage/{workspace_name}/")
    if not parts:
        print(f"\n   ℹ️  Nothing to delete for workspace '{workspace_name}'")
        neo4j_io.close()
        return

    confirm = input(f"\n   Delete {' + '.join(parts)}? (yes/no): ").strip().lower()
    if confirm not in ("yes", "y"):
        print("   ❌ Cancelled")
        neo4j_io.close()
        return

    if not storage_only and neo4j_count > 0:
        deleted = _delete_neo4j_workspace(neo4j_io, workspace_name)
        print(f"   ✅ Deleted {deleted:,} Neo4j nodes from '{workspace_name}'")

    if not neo4j_only and storage_exists:
        found = _delete_storage_workspace(workspace_name, rag_root)
        if found:
            print(f"   ✅ Deleted rag_storage/{workspace_name}/ (any locked files reported above)")

    if not neo4j_only:
        _handle_orphaned_dirs(rag_root)

    neo4j_io.close()


def clear_all_neo4j():
    """Non-interactive: wipe ALL data from Neo4j only."""
    neo4j_io = Neo4jGraphIO()
    print(f"\n⚠️  WARNING: This will delete ALL data from Neo4j!")

    with neo4j_io.driver.session(database=neo4j_io.database) as session:
        rec = session.run("MATCH (n) RETURN count(n) as c").single()
        node_count = rec["c"] if rec else 0

        if node_count == 0:
            print("   ℹ️  Database is already empty")
            neo4j_io.close()
            return

        print(f"   Found {node_count:,} total nodes…")
        confirm = input("   Type 'DELETE ALL' to confirm: ").strip()
        if confirm != "DELETE ALL":
            print("   ❌ Cancelled")
            neo4j_io.close()
            return

        session.run("MATCH (n) DETACH DELETE n")
        print(f"   ✅ Deleted all {node_count:,} nodes")

    neo4j_io.close()


def list_workspaces():
    """List all workspaces visible in Neo4j and rag_storage."""
    neo4j_io = Neo4jGraphIO()
    rag_root = _rag_storage_root()

    neo4j_ws = _neo4j_workspaces(neo4j_io)
    storage_ws = _storage_workspaces(rag_root)
    all_names = sorted(set(neo4j_ws.keys()) | set(storage_ws.keys()))

    print(f"\n{'Workspace':<35}  {'Neo4j nodes':>11}  {'Storage':>8}  {''}")
    print(DIVIDER)
    for name in all_names:
        nodes = neo4j_ws.get(name, 0)
        size = storage_ws.get(name)
        nodes_str = f"{nodes:,}" if nodes else "—"
        size_str = f"{size} MB" if size is not None else "—"
        marker = "← active" if name == neo4j_io.workspace else ""
        print(f"{name:<35}  {nodes_str:>11}  {size_str:>8}  {marker}")

    neo4j_io.close()


# ═══════════════════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Workspace Cleanup Tool — clear Neo4j graph data and/or rag_storage files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/workspace_cleanup.py                        # interactive walkthrough
  python tools/workspace_cleanup.py --workspace my_ws     # clear specific workspace
  python tools/workspace_cleanup.py --workspace my_ws --neo4j-only
  python tools/workspace_cleanup.py --all                 # wipe everything (prompted)
  python tools/workspace_cleanup.py --list                # list all workspaces
        """,
    )
    parser.add_argument("--workspace", type=str, help="Workspace name to clear (non-interactive)")
    parser.add_argument("--all", action="store_true", help="Wipe ALL Neo4j data (prompted)")
    parser.add_argument("--list", action="store_true", help="List all known workspaces")
    parser.add_argument("--neo4j-only", action="store_true", help="Only clear Neo4j; keep rag_storage")
    parser.add_argument("--storage-only", action="store_true", help="Only clear rag_storage; keep Neo4j")

    args = parser.parse_args()

    try:
        if args.list:
            list_workspaces()
        elif args.all:
            clear_all_neo4j()
        elif args.workspace:
            clear_workspace(
                args.workspace,
                neo4j_only=args.neo4j_only,
                storage_only=args.storage_only,
            )
        else:
            # No flags → interactive walkthrough
            interactive_walkthrough()

        print("\n✅ Done!\n")

    except KeyboardInterrupt:
        print("\n\n  ⏹️  Interrupted by user.\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
