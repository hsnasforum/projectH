#!/usr/bin/env python3
import os
import sys
from pathlib import Path

role = ""
handoff = ""
next_control_seq = "2"
written = False


def prompt() -> None:
    sys.stdout.write(">\n")
    sys.stdout.flush()


prompt()
for raw in sys.stdin:
    line = raw.rstrip("\n")
    stripped = line.strip()
    if not stripped:
        continue
    if stripped.startswith("ROLE: "):
        role = stripped.split(":", 1)[1].strip()
        continue
    if stripped.startswith("HANDOFF: "):
        handoff = stripped.split(":", 1)[1].strip()
        continue
    if stripped.startswith("NEXT_CONTROL_SEQ: "):
        next_control_seq = stripped.split(":", 1)[1].strip() or "2"
        continue
    if stripped.startswith("BLOCK_ID: ") and role == "codex_blocked_triage" and handoff and not written:
        target = Path(handoff)
        if not target.is_absolute():
            target = Path(os.getcwd()) / target
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            "STATUS: implement\n"
            f"CONTROL_SEQ: {next_control_seq}\n\n"
            "Next slice: `blocked smoke recovered handoff`\n\n"
            "This handoff was written by the deterministic blocked-triage smoke lane.\n",
            encoding="utf-8",
        )
        sys.stdout.write("• Working smoke blocked triage\n")
        sys.stdout.write(f"• Wrote {target}\n")
        sys.stdout.flush()
        written = True
        prompt()
