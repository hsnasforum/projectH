#!/usr/bin/env python3
import sys

from pipeline_runtime.control_writers import render_implement_blocked

sentinel_sent = False
handoff = ""
handoff_sha = ""


def prompt() -> None:
    sys.stdout.write(">\n")
    sys.stdout.flush()


prompt()
for raw in sys.stdin:
    line = raw.rstrip("\n")
    stripped = line.strip()
    if not stripped:
        continue
    if stripped.startswith("HANDOFF: "):
        handoff = stripped.split(":", 1)[1].strip()
        continue
    if stripped.startswith("HANDOFF_SHA: "):
        handoff_sha = stripped.split(":", 1)[1].strip()
        continue
    if stripped.startswith("BLOCK_ID: ") and not sentinel_sent and handoff and handoff_sha:
        sys.stdout.write(
            render_implement_blocked(
                block_reason="smoke_handoff_blocked",
                block_reason_code="codex_triage_only",
                request="codex_triage",
                escalation_class="codex_triage",
                handoff=handoff,
                handoff_sha=handoff_sha,
                block_id=f"{handoff_sha}:smoke_handoff_blocked",
            )
        )
        sys.stdout.flush()
        sentinel_sent = True
        prompt()
        continue
    if stripped.startswith("ROLE: claude_implement") and sentinel_sent:
        sys.stdout.write("Claude smoke resumed after new handoff\n")
        sys.stdout.flush()
        prompt()
