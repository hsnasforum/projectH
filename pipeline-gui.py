#!/usr/bin/env python3
"""
pipeline-gui.py — 3-agent pipeline desktop GUI launcher.

Usage:
  python3 pipeline-gui.py [project_path]

See scripts/PACKAGING.md for exe packaging.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def _prepare_frozen_import_path() -> None:
    """Keep frozen exe imports deterministic regardless of the launch cwd.

    When the PyInstaller exe is launched from a repo root in PowerShell, the
    current working directory can expose live source packages such as
    ``pipeline_gui`` or ``storage`` ahead of the bundled snapshot. Double-click
    launch and repo-root shell launch then end up importing different code.
    Remove shadowing source roots, put the bundled roots first, and normalize
    the launch cwd to the executable directory so both launch methods resolve
    the same frozen modules and fallback paths.
    """

    if not (getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")):
        return

    bundle_root = Path(sys._MEIPASS).resolve()
    data_root = (bundle_root / "_data").resolve()
    exe_dir = Path(sys.executable).resolve().parent
    cwd = Path.cwd().resolve()
    bundle_prefixes = (bundle_root, data_root)
    shadow_markers = ("pipeline_gui", "storage", "controller")

    def _normalize_provider_prefix(text: str) -> str:
        provider_prefix = "Microsoft.PowerShell.Core\\FileSystem::"
        if text.startswith(provider_prefix):
            return text[len(provider_prefix):]
        return text

    def _is_bundle_path(path: Path) -> bool:
        return any(path == prefix or prefix in path.parents for prefix in bundle_prefixes)

    def _looks_like_shadow_source_root(path: Path) -> bool:
        if _is_bundle_path(path):
            return False
        try:
            return any((path / marker).exists() for marker in shadow_markers)
        except OSError:
            return False

    cleaned: list[str] = []
    for entry in sys.path:
        if not entry:
            continue
        normalized_entry = _normalize_provider_prefix(str(entry))
        try:
            resolved = Path(normalized_entry).resolve()
        except OSError:
            resolved = Path(normalized_entry)
        if resolved == cwd or _looks_like_shadow_source_root(resolved):
            continue
        text = normalized_entry
        if text not in cleaned:
            cleaned.append(text)

    rebuilt: list[str] = []
    for candidate in (str(data_root), str(bundle_root), *cleaned):
        if candidate and candidate not in rebuilt:
            rebuilt.append(candidate)
    sys.path[:] = rebuilt
    try:
        os.chdir(exe_dir)
    except OSError:
        pass


_prepare_frozen_import_path()

from pipeline_gui.project import resolve_project_root
from pipeline_gui.app import PipelineGUI


def main() -> None:
    project = resolve_project_root()
    app = PipelineGUI(project)
    app.run()


if __name__ == "__main__":
    main()
