"""Setup preflight: hard blockers, soft warnings, CLI finder, guide templates."""
from __future__ import annotations

from pathlib import Path

from .platform import IS_WINDOWS, APP_ROOT, _wsl_path_str, _run, resolve_packaged_file

# ── Hard blockers ──
_HARD_BLOCKERS: list[tuple[str, str, str, str]] = [
    ("tmux",               "cli",  "tmux",                "sudo apt install tmux"),
    ("python3",            "cli",  "python3",             "sudo apt install python3"),
    ("claude",             "cli",  "claude",              "npm install -g @anthropic-ai/claude-code"),
    ("codex",              "cli",  "codex",               "npm install -g codex"),
    ("gemini",             "cli",  "gemini",              "npm install -g @google/gemini-cli"),
    ("start-pipeline.sh",  "launcher_file", "start-pipeline.sh",  ""),
    ("stop-pipeline.sh",   "launcher_file", "stop-pipeline.sh",   ""),
    ("watcher_core.py",    "launcher_file", "watcher_core.py",    ""),
    ("AGENTS.md",          "repo_file",     "AGENTS.md",          ""),
]

# ── Soft warnings ──
_SOFT_WARNINGS: list[tuple[str, str, str]] = [
    ("agent_manifest.schema.json", "launcher_file", "schemas/agent_manifest.schema.json"),
    ("job_state.schema.json",      "launcher_file", "schemas/job_state.schema.json"),
    ("token_collector.py",         "launcher_file", "token_collector.py"),
    ("token_schema.sql",           "launcher_file", "token_schema.sql"),
]

_PACKAGED_GUI_FILES = {
    "start-pipeline.sh",
    "stop-pipeline.sh",
    "watcher_core.py",
    "token_collector.py",
    "token_schema.sql",
}

# ── CLI finder (same 3-stage search as start-pipeline.sh) ──
_FIND_CLI_SH = r"""
_find() {
  command -v "$1" 2>/dev/null && return
  [ -s "$HOME/.nvm/nvm.sh" ] && . "$HOME/.nvm/nvm.sh" 2>/dev/null && command -v "$1" 2>/dev/null && return
  for d in "$HOME/.nvm/versions/node"/*/bin "$HOME/.local/bin" /usr/local/bin; do
    [ -x "$d/$1" ] && echo "$d/$1" && return
  done
  return 1
}
"""


def _find_cli_bin(name: str) -> bool:
    script = _FIND_CLI_SH + f'_find "{name}"'
    code, _ = _run(["bash", "-c", script], timeout=8.0)
    return code == 0


def _file_exists(base: Path, rel: str) -> bool:
    if base == APP_ROOT and rel in _PACKAGED_GUI_FILES:
        try:
            return resolve_packaged_file(rel).exists()
        except FileNotFoundError:
            return False
    local = base / rel
    if local.exists():
        return True
    if IS_WINDOWS:
        full = f"{_wsl_path_str(base)}/{rel}"
        code, _ = _run(["test", "-e", full], timeout=5.0)
        return code == 0
    return False


def _check_hard_blockers(project: Path) -> list[tuple[str, str]]:
    missing: list[tuple[str, str]] = []
    for label, check_type, target, hint in _HARD_BLOCKERS:
        if check_type == "cli":
            ok = _find_cli_bin(target)
        elif check_type == "launcher_file":
            ok = _file_exists(APP_ROOT, target)
        elif check_type == "repo_file":
            ok = _file_exists(project, target)
        else:
            ok = True
        if not ok:
            missing.append((label, hint))
    return missing


def _check_soft_warnings(project: Path) -> list[str]:
    warnings: list[str] = []
    for label, check_type, target in _SOFT_WARNINGS:
        if check_type == "launcher_file":
            ok = _file_exists(APP_ROOT, target)
        elif check_type == "repo_file":
            ok = _file_exists(project, target)
        else:
            ok = True
        if not ok:
            warnings.append(label)
    return warnings


# ── Guide templates ──
_TMPL_AGENTS = """\
# Agents

## Default Rules

- Prefer read operations over write operations.
- Read existing code before suggesting modifications.
- Keep changes small and focused — one concern per commit.
- Do not add features, refactor, or "improve" beyond what was asked.
- Do not overwrite files without explicit approval.
- Report verification results honestly — never claim success without evidence.
- Avoid destructive commands (rm -rf, force push, drop table) unless explicitly requested.

## Roles

| Role | Owner | Responsibility |
|------|-------|---------------|
| Implement owner | active role_bindings.implement | Code changes, bug fixes, feature work |
| Verify/handoff owner | active role_bindings.verify | Review, test rerun, truth reconciliation, next handoff |
| Advisory owner | active role_bindings.advisory | Tie-breaking, advisory when verify owner cannot resolve |

## Work Flow

1. Implement owner works from `.pipeline/claude_handoff.md`
2. Verify/handoff owner verifies the latest `/work` against the current tree
3. If verify/handoff owner cannot resolve, advisory owner provides advisory
4. Verify/handoff owner writes the next handoff or operator stop

## Turbo-lite Wrappers

Use the wrappers narrowly and in order:

1. `onboard-lite` when the repo or subsystem is unfamiliar
2. implement owner does the bounded change
3. `finalize-lite` for implementation-side wrap-up
4. `round-handoff` when verification truth must be rerun and reconciled
5. `next-slice-triage` only after `/work` and `/verify` are current

Historical slot filenames remain stable even when the bound owner changes.
The runtime adapter always carries the full three-lane physical catalog (`Claude`, `Codex`, `Gemini`) and marks each lane with `enabled` plus bound `roles`.
Support policy is shape-based rather than name-whitelist based: distinct implement/verify 3-lane with advisory enabled is `supported`, distinct implement/verify 2-lane with advisory disabled is also `supported`, one-lane self-verify is `experimental`, and invalid profiles are `blocked`/`broken`.
"""

_TMPL_CLAUDE = """\
# Claude Project Instructions

## Working Principles

- Follow the active `role_bindings`; Claude may be implement owner or verify/handoff owner depending on the current profile.
- Read the codebase before making changes.
- Prefer editing existing files over creating new ones.
- Make the smallest change that solves the problem.
- Do not add comments, docstrings, or type annotations to code you did not change.
- Do not create documentation files unless explicitly requested.

## Verification

- Run relevant tests after making changes.
- Report only what you actually executed and observed.
- If you did not run a verification step, say so explicitly.

## Safety

- Do not run destructive commands without confirmation.
- Do not modify files outside the current task scope.
- Do not commit or push unless explicitly asked.
- Treat .env, credentials, and secret files as off-limits.
"""

_TMPL_GEMINI = """\
# Gemini Instructions

## Role

You serve as an advisory arbiter for this project.
Your primary function is analysis and recommendation, not direct implementation.
Role ownership follows active `role_bindings`; this file is Gemini's root memory, not proof that Gemini always owns a given lane.

## Principles

- Distinguish facts from assumptions in every response.
- When reviewing code or decisions, cite specific file paths and line numbers.
- Prefer the smallest correct recommendation over broad suggestions.
- Do not modify repo files directly unless explicitly asked with edit/write tools.
- Write advisory output only to designated slots (.pipeline/gemini_advice.md).

## Output Format

When providing advisory:
1. State the question or conflict clearly
2. List evidence from the codebase
3. Give a specific, actionable recommendation
4. Note any uncertainty or missing information
"""

_GUIDE_TEMPLATES: list[tuple[str, str]] = [
    ("AGENTS.md", _TMPL_AGENTS),
    ("CLAUDE.md", _TMPL_CLAUDE),
    ("GEMINI.md", _TMPL_GEMINI),
]


def _check_missing_guides(project: Path) -> list[str]:
    return [name for name, _ in _GUIDE_TEMPLATES if not _file_exists(project, name)]


def _create_guide_file(project: Path, name: str, content: str) -> bool:
    if IS_WINDOWS:
        full = f"{_wsl_path_str(project)}/{name}"
        code, _ = _run(["test", "-e", full], timeout=5.0)
        if code == 0:
            return True
        code, _ = _run(["bash", "-c", f"cat > '{full}' << 'GUIDEEOF'\n{content}\nGUIDEEOF"], timeout=5.0)
        return code == 0
    path = project / name
    if path.exists():
        return True
    try:
        path.write_text(content, encoding="utf-8")
        return True
    except OSError:
        return False
