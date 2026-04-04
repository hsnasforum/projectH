#!/usr/bin/env python3
"""
pipeline-gui.py — 3-agent pipeline desktop GUI launcher.

Usage:
  python3 pipeline-gui.py [project_path]

See scripts/PACKAGING.md for exe packaging.
"""
from pipeline_gui.project import resolve_project_root
from pipeline_gui.app import PipelineGUI


def main() -> None:
    project = resolve_project_root()
    app = PipelineGUI(project)
    app.run()


if __name__ == "__main__":
    main()
