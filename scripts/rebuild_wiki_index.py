#!/usr/bin/env python3
"""
Rebuild the Wikipedia title index
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path for wiki_rag imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from wiki_rag.wikipedia import get_title_to_path_index


def rebuild_index(json_dir_path):
    json_dir = Path(json_dir_path)

    if not json_dir.exists():
        print(f"Error: Directory does not exist: {json_dir}")
        sys.exit(1)

    if not json_dir.is_dir():
        print(f"Error: Path is not a directory: {json_dir}")
        sys.exit(1)

    index_file = json_dir / "title_to_file_path_idx.pkl"

    # Backup old index
    if index_file.exists():
        backup_file = index_file.with_suffix('.pkl.backup')
        print(f"Backing up old index to {backup_file}")
        import shutil
        shutil.copy2(index_file, backup_file)

    print(f"Building new Wikipedia index from {json_dir}")
    print("This may take a while...")

    # Build new index
    title_index = get_title_to_path_index(json_dir, index_file)

    print(f"✅ Index rebuilt with {len(title_index)} articles")
    print(f"Saved to: {index_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Rebuild Wikipedia title index for fast article lookup")
    parser.add_argument(
        "json_dir",
        help="Path to Wikipedia JSON directory (e.g., /path/to/wikipedia/json)"
    )

    args = parser.parse_args()
    rebuild_index(args.json_dir)


if __name__ == "__main__":
    main()
