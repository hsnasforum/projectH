#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import selectors
import sys
import time
from pathlib import Path

from pipeline_runtime.lane_catalog import physical_lane_order

_FIELD_RE = re.compile(r"^\s*([A-Z_]+):\s*(.+?)\s*$", re.MULTILINE)
_ROLE_RE = re.compile(r"^\s*ROLE:\s*([A-Za-z_]+)\s*$", re.MULTILINE)
_OUTPUT_LABEL_RE = re.compile(r"^\s*-\s*([^:]+):\s*(.+?)\s*$", re.MULTILINE)


def _now() -> dt.datetime:
    return dt.datetime.now()


def _date_parts() -> tuple[str, str, str]:
    current = _now()
    return current.strftime("%Y-%m-%d"), str(current.month), str(current.day)


def _extract_field(prompt_text: str, key: str) -> str:
    for match in _FIELD_RE.finditer(prompt_text):
        if match.group(1).strip().upper() == key.upper():
            return match.group(2).strip()
    return ""


def _extract_role(prompt_text: str) -> str:
    match = _ROLE_RE.search(prompt_text)
    return match.group(1).strip().lower() if match else ""


def _extract_output_path(prompt_text: str, label_prefix: str) -> str:
    target = label_prefix.strip().lower()
    for match in _OUTPUT_LABEL_RE.finditer(prompt_text):
        label = match.group(1).strip().lower()
        if label.startswith(target):
            return match.group(2).strip()
    return ""


def _control_seq_from_file(path: Path) -> int:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return 0
    raw = _extract_field(text, "CONTROL_SEQ")
    try:
        return int(raw)
    except ValueError:
        return 0


def _write_text(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _note_path(project_root: Path, category: str, slug: str) -> Path:
    date_text, month, day = _date_parts()
    return project_root / category / month / day / f"{date_text}-{slug}.md"


def _handoff_path(project_root: Path) -> Path:
    return project_root / ".pipeline" / "implement_handoff.md"


def _advisory_request_path(project_root: Path) -> Path:
    return project_root / ".pipeline" / "advisory_request.md"


def _advisory_advice_path(project_root: Path) -> Path:
    return project_root / ".pipeline" / "advisory_advice.md"


def _operator_request_path(project_root: Path) -> Path:
    return project_root / ".pipeline" / "operator_request.md"


def _render_work_note(control_seq: int, variability: int, payload_rel: str) -> str:
    repeated = "\n".join(
        f"- synthetic payload line {index + 1}: seq={control_seq} size-bucket={variability}"
        for index in range(max(1, variability))
    )
    return (
        "## 변경 파일\n"
        f"- {payload_rel}\n\n"
        "## 사용 skill\n"
        "- 없음\n\n"
        "## 변경 이유\n"
        "- supervisor synthetic soak용 implement round 산출물입니다.\n\n"
        "## 핵심 변경\n"
        f"- CONTROL_SEQ {control_seq} handoff를 소비했고 synthetic implement artifact를 남겼습니다.\n"
        f"{repeated}\n\n"
        "## 검증\n"
        "- synthetic lane generated artifact\n\n"
        "## 남은 리스크\n"
        "- synthetic workload이므로 실제 vendor CLI 품질은 검증하지 않습니다.\n"
    )


def _render_verify_note(control_seq: int, route: str) -> str:
    return (
        "## 변경 파일\n"
        "- 없음\n\n"
        "## 사용 skill\n"
        "- 없음\n\n"
        "## 변경 이유\n"
        "- supervisor synthetic soak용 verify round 산출물입니다.\n\n"
        "## 핵심 변경\n"
        f"- CONTROL_SEQ {control_seq} 검증 결과를 synthetic note로 남겼습니다.\n"
        f"- next route: {route}\n\n"
        "## 검증\n"
        "- synthetic lane validated latest work artifact\n\n"
        "## 남은 리스크\n"
        "- synthetic verify 결과이며 실제 모델 판단을 대체하지 않습니다.\n"
    )


def _render_advisory_report(control_seq: int) -> str:
    return (
        f"# synthetic advisory seq {control_seq}\n\n"
        "- synthetic arbitration report\n"
        "- recommendation: proceed with implement handoff\n"
    )


def _write_handoff(project_root: Path, control_seq: int) -> Path:
    content = (
        "STATUS: implement\n"
        f"CONTROL_SEQ: {control_seq}\n\n"
        "Synthetic bounded slice.\n"
        "- Implement the exact synthetic workload round.\n"
        "- Leave one `/work` closeout and stop.\n"
    )
    return _write_text(_handoff_path(project_root), content)


def _write_advisory_request(project_root: Path, control_seq: int) -> Path:
    content = (
        "STATUS: request_open\n"
        f"CONTROL_SEQ: {control_seq}\n\n"
        "Synthetic arbitration request.\n"
        "- Choose the bounded implement recommendation.\n"
    )
    return _write_text(_advisory_request_path(project_root), content)


def _write_advisory_advice(project_root: Path, control_seq: int) -> Path:
    content = (
        "STATUS: advice_ready\n"
        f"CONTROL_SEQ: {control_seq}\n\n"
        "Recommendation:\n"
        "- proceed with the bounded implement handoff\n"
    )
    return _write_text(_advisory_advice_path(project_root), content)


def _write_operator_request(project_root: Path, control_seq: int, reason: str) -> Path:
    content = (
        "STATUS: needs_operator\n"
        f"CONTROL_SEQ: {control_seq}\n\n"
        f"reason: {reason}\n"
    )
    return _write_text(_operator_request_path(project_root), content)


def handle_prompt(
    project_root: Path,
    lane_name: str,
    prompt_text: str,
    *,
    gemini_every: int = 5,
) -> list[Path]:
    role = _extract_role(prompt_text)
    if not role:
        return []
    written: list[Path] = []
    if role == "implement":
        handoff_rel = _extract_field(prompt_text, "HANDOFF") or ".pipeline/implement_handoff.md"
        handoff_path = project_root / handoff_rel
        control_seq = _control_seq_from_file(handoff_path)
        variability = (control_seq % 4) + 1
        payload_rel = f"synthetic_payloads/implement-{control_seq:04d}.txt"
        payload_path = project_root / payload_rel
        written.append(
            _write_text(
                payload_path,
                "\n".join(
                    f"synthetic payload seq={control_seq} line={index + 1}"
                    for index in range(max(2, variability + 1))
                )
                + "\n",
            )
        )
        work_path = _note_path(project_root, "work", f"synthetic-implement-{control_seq:04d}")
        written.append(_write_text(work_path, _render_work_note(control_seq, variability, payload_rel)))
        return written

    if role == "verify":
        raw_seq = _extract_field(prompt_text, "NEXT_CONTROL_SEQ")
        try:
            control_seq = int(raw_seq)
        except ValueError:
            control_seq = 1
        route = "advisory" if gemini_every > 0 and control_seq % gemini_every == 0 else "implement"
        verify_path = _note_path(project_root, "verify", f"synthetic-verify-{control_seq:04d}")
        written.append(_write_text(verify_path, _render_verify_note(control_seq, route)))
        if route == "advisory":
            written.append(_write_advisory_request(project_root, control_seq))
        else:
            written.append(_write_handoff(project_root, control_seq))
        return written

    if role in {"followup", "verify_triage"}:
        raw_seq = _extract_field(prompt_text, "NEXT_CONTROL_SEQ")
        try:
            control_seq = int(raw_seq)
        except ValueError:
            control_seq = 1
        written.append(_write_handoff(project_root, control_seq))
        return written

    if role == "advisory":
        raw_seq = _extract_field(prompt_text, "NEXT_CONTROL_SEQ")
        try:
            control_seq = int(raw_seq)
        except ValueError:
            control_seq = 1
        report_rel = _extract_output_path(prompt_text, "advisory log") or "report/gemini/synthetic-advisory-advice.md"
        report_path = project_root / report_rel
        written.append(_write_text(report_path, _render_advisory_report(control_seq)))
        written.append(_write_advisory_advice(project_root, control_seq))
        return written

    if role == "operator":
        raw_seq = _extract_field(prompt_text, "NEXT_CONTROL_SEQ")
        try:
            control_seq = int(raw_seq)
        except ValueError:
            control_seq = 1
        written.append(_write_operator_request(project_root, control_seq, "synthetic operator stop"))
    return written


def _ready_banner(lane_name: str) -> str:
    if lane_name == "Claude":
        return "Claude Code\n❯ "
    if lane_name == "Codex":
        return "OpenAI Codex\n› Type your message\n"
    return "Gemini CLI\nType your message\nworkspace\n"


def _busy_banner(lane_name: str, role: str) -> str:
    if lane_name == "Codex":
        return f"\n• Working (synthetic {role})\n"
    if lane_name == "Gemini":
        return f"\n✦ Synthetic {role} in progress\n"
    return f"\nWorking (synthetic {lane_name.lower()} {role})\n"


def _split_prompt_batches(buffer: str) -> list[str]:
    chunks = re.split(r"(?=^\s*ROLE:\s*)", buffer, flags=re.MULTILINE)
    return [chunk.strip() for chunk in chunks if chunk.strip()]


def run_interactive(
    project_root: Path,
    lane_name: str,
    *,
    gemini_every: int,
    idle_flush_sec: float,
    action_delay_sec: float,
) -> int:
    selector = selectors.DefaultSelector()
    selector.register(sys.stdin, selectors.EVENT_READ)
    pending = ""
    last_input_at = 0.0
    sys.stdout.write(_ready_banner(lane_name))
    sys.stdout.flush()
    while True:
        events = selector.select(timeout=idle_flush_sec)
        if events:
            for _key, _mask in events:
                chunk = os.read(sys.stdin.fileno(), 4096)
                if not chunk:
                    if pending.strip():
                        for prompt in _split_prompt_batches(pending):
                            role = _extract_role(prompt)
                            if not role:
                                continue
                            sys.stdout.write(_busy_banner(lane_name, role))
                            sys.stdout.flush()
                            time.sleep(max(0.0, action_delay_sec))
                            handle_prompt(project_root, lane_name, prompt, gemini_every=gemini_every)
                            sys.stdout.write(_ready_banner(lane_name))
                            sys.stdout.flush()
                    return 0
                pending += chunk.decode("utf-8", errors="replace")
                last_input_at = time.time()
        if pending.strip() and last_input_at and (time.time() - last_input_at) >= idle_flush_sec:
            batch = pending
            pending = ""
            for prompt in _split_prompt_batches(batch):
                role = _extract_role(prompt)
                if not role:
                    continue
                sys.stdout.write(_busy_banner(lane_name, role))
                sys.stdout.flush()
                time.sleep(max(0.0, action_delay_sec))
                handle_prompt(project_root, lane_name, prompt, gemini_every=gemini_every)
                sys.stdout.write(_ready_banner(lane_name))
                sys.stdout.flush()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pipeline_runtime_fake_lane")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--lane", required=True, choices=physical_lane_order())
    parser.add_argument("--gemini-every", type=int, default=5)
    parser.add_argument("--idle-flush-sec", type=float, default=0.2)
    parser.add_argument("--action-delay-sec", type=float, default=0.05)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run_interactive(
        Path(args.project_root).resolve(),
        args.lane,
        gemini_every=max(0, int(args.gemini_every)),
        idle_flush_sec=max(0.05, float(args.idle_flush_sec)),
        action_delay_sec=max(0.0, float(args.action_delay_sec)),
    )


if __name__ == "__main__":
    raise SystemExit(main())
