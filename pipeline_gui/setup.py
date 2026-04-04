"""Setup preflight: hard blockers, soft warnings, CLI finder, guide templates."""
from __future__ import annotations

from pathlib import Path

from .platform import IS_WINDOWS, APP_ROOT, _wsl_path_str, _run

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
]

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

| Role | Agent | Responsibility |
|------|-------|---------------|
| Implementer | Claude | Code changes, bug fixes, feature work |
| Verifier | Codex | Review, test rerun, truth reconciliation |
| Arbiter | Gemini | Tie-breaking, advisory when verifier cannot resolve |

## Work Flow

1. Claude implements based on handoff instructions
2. Codex verifies the implementation against current tree
3. If Codex cannot resolve, Gemini provides advisory
4. Operator makes final decisions on ambiguous cases
"""

_TMPL_CLAUDE = """\
# Claude Project Instructions

## Working Principles

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
