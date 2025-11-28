#!/usr/bin/env python3
import argparse
from pathlib import Path
import shutil
import sys
import time
import json
from typing import List, Dict

def find_empty_files(path: Path, recursive: bool = True, ignore_hidden: bool = True):
    empty_files = []
    iterator = path.rglob("*") if recursive else path.iterdir()
    for p in iterator:
        if p.is_file():
            if ignore_hidden and any(part.startswith(".") for part in p.parts):
                continue
            try:
                if p.stat().st_size == 0:
                    empty_files.append(p)
            except OSError:
                pass
    return empty_files

def make_quarantine_dir(base: Path = None):
    t = time.strftime("%Y%m%d-%H%M%S")
    base = Path(base) if base else Path.cwd()
    q = base.joinpath(f"quarantine-{t}")
    q.mkdir(parents=True, exist_ok=True)
    return q.resolve()

def _unique_path_if_exists(path: Path) -> Path:
    """Return a non-existing path by appending _1, _2..."""
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    counter = 1
    while True:
        candidate = parent.joinpath(f"{stem}_{counter}{suffix}")
        if not candidate.exists():
            return candidate
        counter += 1

def safe_move(src: Path, dst_dir: Path, preserve_structure: bool, target_root: Path, dry_run: bool=False):
    """
    Move src to dst_dir. If preserve_structure True, recreate src's path relative to target_root.
    Avoid name collisions by appending a counter suffix.
    Returns final destination Path and metadata dict.
    """
    if preserve_structure:
        try:
            rel = src.relative_to(target_root)
        except Exception:
            rel = Path(src.name)
        dest_path = dst_dir.joinpath(rel)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        dest_path = dst_dir.joinpath(src.name)
        dest_path.parent.mkdir(parents=True, exist_ok=True)

    final_dest = _unique_path_if_exists(dest_path)

    if dry_run:
        # Do not move; just return the would-be destination and metadata
        return final_dest, {
            "original": str(src.resolve()),
            "moved_to": str(final_dest.resolve()),
            "size": src.stat().st_size if src.exists() else None,
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "action": "dry-run"
        }

    shutil.move(str(src), str(final_dest))
    metadata = {
        "original": str(src.resolve()),
        "moved_to": str(final_dest.resolve()),
        "size": final_dest.stat().st_size if final_dest.exists() else None,
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "action": "moved"
    }
    return final_dest, metadata

def write_metadata(quarantine_dir: Path, records: List[Dict]):
    meta_file = quarantine_dir.joinpath("metadata.json")
    # If metadata exists, append; else write fresh
    existing = []
    if meta_file.exists():
        try:
            existing = json.loads(meta_file.read_text())
        except Exception:
            existing = []
    existing.extend(records)
    meta_file.write_text(json.dumps(existing, indent=2))

def find_latest_quarantine(base: Path = None) -> Path:
    base = Path(base) if base else Path.cwd()
    candidates = [p for p in base.iterdir() if p.is_dir() and p.name.startswith("quarantine-")]
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.name, reverse=True)  # latest name usually has the newest timestamp
    return candidates[0].resolve()

def restore_from_quarantine(quarantine_dir: Path, dry_run: bool = False, yes: bool = False):
    meta_file = quarantine_dir.joinpath("metadata.json")
    if not meta_file.exists():
        print(f"No metadata.json found in {quarantine_dir}. Cannot restore reliably.")
        return

    try:
        records = json.loads(meta_file.read_text())
    except Exception as e:
        print(f"Failed to read metadata.json: {e}")
        return

    restored = []
    skipped = []
    errors = []

    for entry in records:
        original = Path(entry.get("original"))
        moved_to = Path(entry.get("moved_to"))
        if not moved_to.exists():
            skipped.append((original, moved_to, "moved file missing"))
            continue

        target_parent = original.parent
        if not target_parent.exists():
            try:
                if not dry_run:
                    target_parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append((original, moved_to, f"failed to create parent: {e}"))
                continue

        # If original exists:
        if original.exists():
            if yes:
                # overwrite
                try:
                    if not dry_run:
                        # move to temp unique path then remove or overwrite
                        tmp = _unique_path_if_exists(original)
                        # prefer removing original then moving; if no permission, fallback to renaming
                        original.unlink()
                        shutil.move(str(moved_to), str(original))
                        restored.append((original, moved_to))
                    else:
                        restored.append((original, moved_to))
                except Exception as e:
                    # try unique rename instead
                    try:
                        candidate = _unique_path_if_exists(original)
                        if not dry_run:
                            shutil.move(str(moved_to), str(candidate))
                        restored.append((candidate, moved_to))
                    except Exception as ee:
                        errors.append((original, moved_to, f"overwrite error: {e}; fallback failed: {ee}"))
                continue
            else:
                # do not overwrite; create unique name next to original
                candidate = _unique_path_if_exists(original)
                try:
                    if not dry_run:
                        shutil.move(str(moved_to), str(candidate))
                    restored.append((candidate, moved_to))
                except Exception as e:
                    errors.append((original, moved_to, f"collision handling error: {e}"))
                continue

        # original does not exist, just move back
        try:
            if not dry_run:
                shutil.move(str(moved_to), str(original))
            restored.append((original, moved_to))
        except Exception as e:
            errors.append((original, moved_to, f"move error: {e}"))

    # summary output
    print(f"\nRestore Summary for: {quarantine_dir}")
    print(f"Files restored/moved: {len(restored)}")
    if restored:
        for o, m in restored:
            print(" - Restored:", o, "<-", m)
    if skipped:
        print(f"\nSkipped (missing moved file): {len(skipped)}")
        for o, m, reason in skipped:
            print(" - Skipped:", m, "->", o, "|", reason)
    if errors:
        print(f"\nErrors: {len(errors)}")
        for o, m, err in errors:
            print(" - Error restoring", m, "->", o, ":", err)

def list_quarantines(base: Path = None):
    base = Path(base) if base else Path.cwd()
    quarantines = [p for p in base.iterdir() if p.is_dir() and p.name.startswith("quarantine-")]
    quarantines.sort()
    if not quarantines:
        print("No quarantine directories found in", base)
        return
    print("Quarantine directories:")
    for q in quarantines:
        meta = q.joinpath("metadata.json")
        count = "?" 
        if meta.exists():
            try:
                arr = json.loads(meta.read_text())
                count = len(arr)
            except Exception:
                count = "?"
        print(f" - {q}  (items recorded: {count})")

def main():
    parser = argparse.ArgumentParser(description="Move empty files to a quarantine folder (safe).")
    parser.add_argument("target", nargs="?", default=".", help="Target directory to scan")
    parser.add_argument("--no-recursive", dest="recursive", action="store_false", help="Do not search recursively")
    parser.add_argument("--dry-run", action="store_true", help="Show files that would be moved")
    parser.add_argument("--yes", action="store_true", help="Move/restore without asking for confirmation / overwrite when restoring")
    parser.add_argument("--quarantine", help="Quarantine folder path (default: ./quarantine-<timestamp> or for restore, specify which quarantine)")
    parser.add_argument("--preserve-structure", action="store_true", help="Preserve folder structure inside quarantine")
    parser.add_argument("--ignore-hidden", dest="ignore_hidden", action="store_true", help="Ignore hidden files/dirs (default)")
    parser.add_argument("--include-hidden", dest="ignore_hidden", action="store_false", help="Include hidden files/dirs")
    parser.add_argument("--restore", action="store_true", help="Restore files from a quarantine (uses --quarantine or finds latest in cwd)")
    parser.add_argument("--list-quarantines", action="store_true", help="List quarantine folders in current directory")
    args = parser.parse_args()

    target = Path(args.target).resolve()
    if not args.restore:
        # normal scan/move flow
        if not target.exists() or not target.is_dir():
            print(f"Target directory does not exist or is not a directory: {target}")
            sys.exit(1)

        empty_files = find_empty_files(target, recursive=args.recursive, ignore_hidden=args.ignore_hidden)
        if not empty_files:
            print("No empty files found.")
            return

        print("Empty files found:")
        for f in empty_files:
            print(" -", f)

        if args.dry_run:
            print("\nDry-run: no files were moved.")
            return

        quarantine_base = Path(args.quarantine) if args.quarantine else None
        quarantine_dir = make_quarantine_dir(quarantine_base)
        print(f"\nQuarantine folder (will be used): {quarantine_dir}")

        if not args.yes:
            confirm = input("\nMove these files to quarantine? Type 'yes' to confirm: ")
            if confirm.strip().lower() != "yes":
                print("Aborted by user.")
                return

        moved_meta = []
        for src in empty_files:
            try:
                dest, meta = safe_move(src, quarantine_dir, preserve_structure=args.preserve_structure, target_root=target, dry_run=False)
                moved_meta.append(meta)
                print(f"[MOVED] {src} -> {dest}")
            except Exception as e:
                print(f"[ERROR] Could not move {src}: {e}")

        if moved_meta:
            try:
                write_metadata(quarantine_dir, moved_meta)
            except Exception as e:
                print(f"Warning: failed to write metadata.json: {e}")

        print("\nSummary:")
        print(f"Files moved: {len(moved_meta)}")
        if moved_meta:
            print(f"Quarantine location: {quarantine_dir}")
        else:
            print("No files were moved.")
    else:
        # restore / list flow
        if args.list_quarantines:
            list_quarantines(base=target)
            return

        if args.quarantine:
            qdir = Path(args.quarantine).resolve()
            if not qdir.exists() or not qdir.is_dir():
                print(f"Provided quarantine path does not exist or is not a directory: {qdir}")
                return
        else:
            qdir = find_latest_quarantine(base=Path.cwd())
            if not qdir:
                print("No quarantine directories found in current directory.")
                return
            print(f"No --quarantine provided. Using latest quarantine: {qdir}")

        if args.dry_run:
            print("Dry-run: no files will be moved. Showing restore plan...\n")

        if not args.yes:
            confirm = input(f"\nRestore files from {qdir}? Type 'yes' to confirm: ")
            if confirm.strip().lower() != "yes" and not args.dry_run:
                print("Aborted by user.")
                return

        restore_from_quarantine(qdir, dry_run=args.dry_run, yes=args.yes)

if __name__ == "__main__":
    main()
