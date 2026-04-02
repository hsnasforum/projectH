"""CLI for migrating JSON stores to SQLite.

Usage:
  python -m storage.migrate
  python -m storage.migrate --db-path data/projecth.db
"""

from __future__ import annotations

import argparse

from storage.sqlite_store import migrate_json_to_sqlite


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate JSON stores to SQLite")
    parser.add_argument("--sessions-dir", default="data/sessions")
    parser.add_argument("--artifacts-dir", default="data/artifacts")
    parser.add_argument("--corrections-dir", default="data/corrections")
    parser.add_argument("--preferences-dir", default="data/preferences")
    parser.add_argument("--db-path", default="data/projecth.db")
    args = parser.parse_args()

    print(f"Migrating to {args.db_path}...")
    counts = migrate_json_to_sqlite(
        sessions_dir=args.sessions_dir,
        artifacts_dir=args.artifacts_dir,
        corrections_dir=args.corrections_dir,
        preferences_dir=args.preferences_dir,
        db_path=args.db_path,
    )

    for table, count in counts.items():
        print(f"  {table}: {count} records")
    print("Done.")


if __name__ == "__main__":
    main()
