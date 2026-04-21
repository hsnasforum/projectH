from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Optional


DEFAULT_IMPLEMENT_PROMPT = (
    "ROLE: implement\n"
    "OWNER: {runtime_implement_owner}\n"
    "HANDOFF: {active_handoff_path}\n"
    "HANDOFF_SHA: {active_handoff_sha}\n"
    "GOAL:\n"
    "- do only the handoff; if done, leave one `/work` closeout and stop\n"
    "READ_FIRST:\n"
    "- {runtime_implement_read_first_doc}\n"
    "- {active_handoff_path}\n"
    "RULES:\n"
    "- no commit, push, branch/PR publish, or next-slice choice\n"
    "- do not write .pipeline/gemini_request.md or .pipeline/operator_request.md yourself\n"
    "- if the handoff is blocked or not actionable, emit the exact sentinel below and stop\n"
    "BLOCKED_SENTINEL:\n"
    "STATUS: implement_blocked\n"
    "BLOCK_REASON: <short_reason>\n"
    "BLOCK_REASON_CODE: <reason_code>\n"
    "REQUEST: codex_triage\n"
    "ESCALATION_CLASS: codex_triage\n"
    "HANDOFF: {active_handoff_path}\n"
    "HANDOFF_SHA: {active_handoff_sha}\n"
    "BLOCK_ID: {active_handoff_sha}:<short_reason>"
)

DEFAULT_ADVISORY_PROMPT = (
    "ROLE: advisory\n"
    "OWNER: {runtime_advisory_owner}\n"
    "REQUEST: {gemini_request_mention}\n"
    "WORK: {latest_work_mention}\n"
    "VERIFY: {latest_verify_mention}\n"
    "NEXT_CONTROL_SEQ: {next_control_seq}\n"
    "GOAL:\n"
    "- leave one advisory log and one `.pipeline/gemini_advice.md`\n"
    "READ_FIRST:\n"
    "- {runtime_advisory_read_first_doc}\n"
    "- {gemini_request_mention}\n"
    "- {latest_work_mention}\n"
    "- {latest_verify_mention}\n"
    "OUTPUTS:\n"
    "- log: {gemini_report_path}\n"
    "- advice slot: {gemini_advice_path} (STATUS: advice_ready, CONTROL_SEQ: {next_control_seq})\n"
    "RULES:\n"
    "- keep `READ_FIRST` to the listed advisory-owner root doc only\n"
    "- if the request cites exact shipped docs or a current runtime-doc family, inspect those first\n"
    "- do not widen to `docs/superpowers/**`, `plandoc/**`, or historical planning docs unless the request, latest `/work`, or latest `/verify` cites them as current evidence\n"
    "- pane-only answer is not completion\n"
    "- use edit/write tools only; no shell heredoc or redirection\n"
    "- do not modify other repo files\n"
    "- keep the recommendation short and exact"
)

DEFAULT_FOLLOWUP_PROMPT = (
    "ROLE: followup\n"
    "OWNER: {runtime_verify_owner}\n"
    "NEXT_CONTROL_SEQ: {next_control_seq}\n"
    "REQUEST: .pipeline/gemini_request.md\n"
    "ADVICE: .pipeline/gemini_advice.md\n"
    "WORK: {latest_work_path}\n"
    "VERIFY: {latest_verify_path}\n"
    "GOAL:\n"
    "- turn the advisory into exactly one next control\n"
    "READ_FIRST:\n"
    "- {runtime_verify_read_first_doc}\n"
    "- .pipeline/gemini_request.md\n"
    "- .pipeline/gemini_advice.md\n"
    "OUTPUTS:\n"
    "- next control (CONTROL_SEQ: {next_control_seq}): .pipeline/claude_handoff.md [implement] | .pipeline/operator_request.md [needs_operator]\n"
    "RULES:\n"
    "- keep `READ_FIRST` to the listed verify-owner root doc only\n"
    "- write exactly one next control\n"
    "- do not route commit/push publish work to `.pipeline/claude_handoff.md`; keep it in verify/handoff or advisory because implement prompts forbid commit, push, branch/PR publish\n"
    "- if you write `.pipeline/claude_handoff.md`, keep its `READ_FIRST` to the implement-owner root doc only\n"
    "- operator stop header must include STATUS, CONTROL_SEQ, REASON_CODE, OPERATOR_POLICY, DECISION_CLASS, DECISION_REQUIRED, BASED_ON_WORK, BASED_ON_VERIFY\n"
    "- after Gemini advice, use .pipeline/operator_request.md only if it recommends a real operator decision or no truthful exact slice remains"
)

DEFAULT_CONTROL_RECOVERY_PROMPT = (
    "ROLE: control_recovery\n"
    "OWNER: {runtime_verify_owner}\n"
    "STALE_CONTROL: {stale_control_path}\n"
    "STALE_CONTROL_SEQ: {stale_control_seq}\n"
    "REASON: {stale_control_reason}\n"
    "RESOLVED_BLOCKERS:\n"
    "{stale_control_resolved_work_paths}\n"
    "WORK: {latest_work_path}\n"
    "VERIFY: {latest_verify_path}\n"
    "GOAL:\n"
    "- its blocker work is already VERIFY_DONE; write exactly one next control so runtime does not sit idle on stale control\n"
    "READ_FIRST:\n"
    "- {runtime_verify_read_first_doc}\n"
    "- {stale_control_path}\n"
    "- {latest_work_path}\n"
    "- {latest_verify_path}\n"
    "OUTPUTS:\n"
    "- next control (CONTROL_SEQ: {next_control_seq}): .pipeline/claude_handoff.md [implement] | .pipeline/gemini_request.md [request_open] | .pipeline/operator_request.md [needs_operator]\n"
    "RULES:\n"
    "- keep `READ_FIRST` to the listed verify-owner root doc only\n"
    "- write exactly one next control\n"
    "- do not route commit/push publish work to `.pipeline/claude_handoff.md`; keep it in verify/handoff or advisory because implement prompts forbid commit, push, branch/PR publish\n"
    "- if you write `.pipeline/claude_handoff.md`, keep its `READ_FIRST` to the implement-owner root doc only\n"
    "- operator stop header must include STATUS, CONTROL_SEQ, REASON_CODE, OPERATOR_POLICY, DECISION_CLASS, DECISION_REQUIRED, BASED_ON_WORK, BASED_ON_VERIFY\n"
    "- for next-slice ambiguity / overlap / low-confidence prioritization, write .pipeline/gemini_request.md before .pipeline/operator_request.md\n"
    "- do not leave runtime idle on stale control alone\n"
    "- skip Gemini only for a real operator-only decision, approval/truth-sync, immediate safety, or unavailable/inconclusive Gemini"
)

DEFAULT_OPERATOR_RETRIAGE_PROMPT = (
    "ROLE: operator_retriage\n"
    "OWNER: {runtime_verify_owner}\n"
    "ACTIVE_CONTROL: {operator_request_path}\n"
    "ACTIVE_CONTROL_SEQ: {stale_control_seq}\n"
    "PENDING_AGE_SEC: {operator_wait_age_sec}\n"
    "REASON: {stale_control_reason}\n"
    "WORK: {latest_work_path}\n"
    "VERIFY: {latest_verify_path}\n"
    "GOAL:\n"
    "- re-triage the pending or gated operator stop before publishing operator wait\n"
    "- decide whether self-heal / triage / hibernate cleared the real operator-only decision\n"
    "- then either execute an allowed publish follow-up or write exactly one next control\n"
    "READ_FIRST:\n"
    "- {runtime_verify_read_first_doc}\n"
    "- {operator_request_path}\n"
    "- {latest_work_path}\n"
    "- {latest_verify_path}\n"
    "OUTPUTS:\n"
    "- next control (CONTROL_SEQ: {next_control_seq}): .pipeline/claude_handoff.md [implement] | .pipeline/gemini_request.md [request_open] | .pipeline/operator_request.md [needs_operator]\n"
    "- for `commit_push_bundle_authorization + internal_only`: perform the scoped commit/push in this verify/handoff round, write a `/work` closeout with commit SHA and push result, then write the next control\n"
    "RULES:\n"
    "- keep `READ_FIRST` to the listed verify-owner root doc only\n"
    "- write exactly one next control\n"
    "- do not hand commit/push work to the implement lane; implement prompts forbid commit, push, branch/PR publish\n"
    "- if you write `.pipeline/claude_handoff.md`, keep its `READ_FIRST` to the implement-owner root doc only\n"
    "- operator stop header must include STATUS, CONTROL_SEQ, REASON_CODE, OPERATOR_POLICY, DECISION_CLASS, DECISION_REQUIRED, BASED_ON_WORK, BASED_ON_VERIFY\n"
    "- prefer .pipeline/gemini_request.md before .pipeline/operator_request.md when the only blocker is next-slice ambiguity\n"
    "- only keep STATUS: needs_operator if a real operator-only decision, approval/truth-sync blocker, or immediate safety stop still remains right now"
)

DEFAULT_VERIFY_TRIAGE_PROMPT = (
    "ROLE: verify_triage\n"
    "OWNER: {runtime_verify_owner}\n"
    "HANDOFF: {active_handoff_path}\n"
    "HANDOFF_SHA: {active_handoff_sha}\n"
    "BLOCK_SOURCE: {blocked_source}\n"
    "BLOCK_REASON: {blocked_reason}\n"
    "BLOCK_REASON_CODE: {blocked_reason_code}\n"
    "ESCALATION_CLASS: {blocked_escalation_class}\n"
    "BLOCK_ID: {blocked_fingerprint}\n"
    "NEXT_CONTROL_SEQ: {next_control_seq}\n"
    "WORK: {latest_work_path}\n"
    "VERIFY: {latest_verify_path}\n"
    "GOAL:\n"
    "- recover from implement_blocked with exactly one next control\n"
    "- if the block says commit/push is forbidden by implement-lane rules, keep publish work in verify/handoff ownership instead of reissuing an implement handoff\n"
    "BLOCK_EXCERPT:\n"
    "{blocked_excerpt}\n"
    "READ_FIRST:\n"
    "- {runtime_verify_read_first_doc}\n"
    "- {active_handoff_path}\n"
    "- {latest_work_path}\n"
    "- {latest_verify_path}\n"
    "OUTPUTS:\n"
    "- next control (CONTROL_SEQ: {next_control_seq}): .pipeline/claude_handoff.md [implement] | .pipeline/gemini_request.md [request_open] | .pipeline/operator_request.md [needs_operator]\n"
    "RULES:\n"
    "- keep `READ_FIRST` to the listed verify-owner root doc only\n"
    "- write exactly one next control\n"
    "- do not reissue commit/push as `.pipeline/claude_handoff.md`; implement prompts forbid commit, push, branch/PR publish\n"
    "- if you write `.pipeline/claude_handoff.md`, keep its `READ_FIRST` to the implement-owner root doc only\n"
    "- do not leave the implement owner waiting on an operator-choice menu\n"
    "- operator stop header must include STATUS, CONTROL_SEQ, REASON_CODE, OPERATOR_POLICY, DECISION_CLASS, DECISION_REQUIRED, BASED_ON_WORK, BASED_ON_VERIFY\n"
    "- for next-slice ambiguity / overlap / low-confidence prioritization, write .pipeline/gemini_request.md before .pipeline/operator_request.md\n"
    "- skip Gemini only for a real operator-only decision, approval/truth-sync, immediate safety, or unavailable/inconclusive Gemini"
)

DEFAULT_VERIFY_PROMPT_TEMPLATE = (
    "ROLE: verify\n"
    "OWNER: {runtime_verify_owner}\n"
    "WORK: {latest_work_path}\n"
    "VERIFY: {latest_verify_path}\n"
    "NEXT_CONTROL_SEQ: {next_control_seq}\n"
    "GOAL:\n"
    "- verify the latest `/work`, update `/verify`, then write exactly one next control\n"
    "SCOPE_HINT:\n"
    "{verify_scope_hint}\n"
    "READ_FIRST:\n"
    "- {runtime_verify_read_first_doc}\n"
    "- {latest_work_path}\n"
    "- {latest_verify_path}\n"
    "OUTPUTS:\n"
    "- /verify note first\n"
    "- next control (CONTROL_SEQ: {next_control_seq}): .pipeline/claude_handoff.md [implement] | .pipeline/gemini_request.md [request_open] | .pipeline/operator_request.md [needs_operator]\n"
    "RULES:\n"
    "- keep `READ_FIRST` to the listed verify-owner root doc only\n"
    "- choose one exact next slice or one exact operator decision\n"
    "- do not route commit/push publish work to `.pipeline/claude_handoff.md`; keep it in verify/handoff or advisory because implement prompts forbid commit, push, branch/PR publish\n"
    "- if you write `.pipeline/claude_handoff.md`, keep its `READ_FIRST` to the implement-owner root doc only\n"
    "- operator stop header must include STATUS, CONTROL_SEQ, REASON_CODE, OPERATOR_POLICY, DECISION_CLASS, DECISION_REQUIRED, BASED_ON_WORK, BASED_ON_VERIFY\n"
    "- for next-slice ambiguity / overlap / low-confidence prioritization, open .pipeline/gemini_request.md before .pipeline/operator_request.md\n"
    "- skip Gemini only for a real operator-only decision, approval/truth-sync, immediate safety, or unavailable/inconclusive Gemini\n"
    "- after 3+ same-day same-family docs-only truth-sync rounds, choose one bounded docs bundle or escalate"
)


@dataclass(frozen=True)
class PromptDispatchSpec:
    pending_key: str
    notify_kind: str
    lane_role: str
    prompt: str
    prompt_path: Path
    functional_role: str = ""
    lane_id: str = ""
    agent_kind: str = ""
    model_alias: str | None = None
    notify_label: str = ""
    raw_event: str = ""
    raw_payload: dict[str, object] = field(default_factory=dict)
    control_seq: int = -1
    expected_status: str = ""
    expected_control_path: str = ""
    expected_control_seq: int = -1
    require_active_control: bool = False


class WatcherPromptAssembler:
    def __init__(
        self,
        *,
        report_gemini_dir: Path,
        claude_handoff_path: Path,
        gemini_request_path: Path,
        gemini_advice_path: Path,
        operator_request_path: Path,
        runtime_enabled_lanes: list[str],
        runtime_controls: Mapping[str, Any],
        implement_prompt: str,
        advisory_prompt: str,
        followup_prompt: str,
        control_recovery_prompt: str,
        operator_retriage_prompt: str,
        verify_triage_prompt: str,
        normalize_prompt_text: Callable[[str], str],
        get_latest_work_path: Callable[[], Optional[Path]],
        get_latest_same_day_verify_path_for_work: Callable[[Optional[Path]], Optional[Path]],
        get_latest_same_day_verify_path: Callable[[Optional[Path]], Optional[Path]],
        infer_gemini_report_hint: Callable[[Optional[Path]], str],
        get_active_control_signal: Callable[[], Any],
        get_next_control_seq: Callable[[], int],
        read_control_seq_from_path: Callable[[Path], int],
        role_owner: Callable[[str], str | None],
        role_read_first_doc: Callable[[str], str],
        path_mention: Callable[[Optional[Path]], str],
        repo_relative: Callable[[Optional[Path]], str],
        get_path_sha256: Callable[[Path], str],
        extract_changed_file_paths_from_round_note: Callable[[Optional[Path]], list[str]],
    ) -> None:
        self.report_gemini_dir = report_gemini_dir
        self.claude_handoff_path = claude_handoff_path
        self.gemini_request_path = gemini_request_path
        self.gemini_advice_path = gemini_advice_path
        self.operator_request_path = operator_request_path
        self.runtime_enabled_lanes = runtime_enabled_lanes
        self.runtime_controls = runtime_controls
        self.implement_prompt = implement_prompt
        self.advisory_prompt = advisory_prompt
        self.followup_prompt = followup_prompt
        self.control_recovery_prompt = control_recovery_prompt
        self.operator_retriage_prompt = operator_retriage_prompt
        self.verify_triage_prompt = verify_triage_prompt
        self._normalize_prompt_text = normalize_prompt_text
        self._get_latest_work_path = get_latest_work_path
        self._get_latest_same_day_verify_path_for_work = get_latest_same_day_verify_path_for_work
        self._get_latest_same_day_verify_path = get_latest_same_day_verify_path
        self._infer_gemini_report_hint = infer_gemini_report_hint
        self._get_active_control_signal = get_active_control_signal
        self._get_next_control_seq = get_next_control_seq
        self._read_control_seq_from_path = read_control_seq_from_path
        self._role_owner = role_owner
        self._role_read_first_doc = role_read_first_doc
        self._path_mention = path_mention
        self._repo_relative = repo_relative
        self._get_path_sha256 = get_path_sha256
        self._extract_changed_file_paths_from_round_note = extract_changed_file_paths_from_round_note

    def _finalize_prompt_text(self, text: str) -> str:
        normalized = self._normalize_prompt_text(text)
        drop_exact = {
            "WORK: 없음",
            "WORK: (없음)",
            "VERIFY: 없음",
            "VERIFY: (없음)",
            "- 없음",
            "- (없음)",
        }
        kept_lines: list[str] = []
        blank_run = 0
        for line in normalized.splitlines():
            stripped = line.strip()
            if stripped in drop_exact:
                continue
            if not stripped:
                blank_run += 1
                if blank_run > 1:
                    continue
            else:
                blank_run = 0
            kept_lines.append(line)
        return "\n".join(kept_lines).strip()

    def finalize_prompt_text(self, text: str) -> str:
        return self._finalize_prompt_text(text)

    def _lane_identity(
        self,
        *,
        functional_role: str,
        notify_kind: str,
        control_seq: int,
    ) -> dict[str, object]:
        owner = str(self._role_owner(functional_role) or functional_role).strip()
        agent_kind = owner.lower() if owner else functional_role
        lane_id = f"{agent_kind}_{functional_role}"
        seq_suffix = str(control_seq) if control_seq >= 0 else "na"
        return {
            "functional_role": functional_role,
            "lane_id": lane_id,
            "agent_kind": agent_kind,
            "model_alias": None,
            "pending_key": f"{lane_id}:{notify_kind}:{seq_suffix}",
        }

    def _identity_payload(
        self,
        *,
        functional_role: str,
        lane_id: str,
        agent_kind: str,
        model_alias: str | None,
    ) -> dict[str, object]:
        return {
            "functional_role": functional_role,
            "lane_id": lane_id,
            "agent_kind": agent_kind,
            "model_alias": model_alias,
            "lane_role": functional_role,
        }

    def verify_scope_hint_for_work(self, work_path: Optional[Path]) -> tuple[str, str]:
        changed_paths = self._extract_changed_file_paths_from_round_note(work_path)
        if changed_paths and all(path.endswith(".md") for path in changed_paths):
            return (
                "docs_only",
                "- docs-only truth-sync from `## 변경 파일`; check markdown truth first with `git diff --check`, and do not widen into unit or Playwright unless code/test/runtime changed",
            )
        return (
            "standard",
            "- standard verification; rerun only the narrowest checks needed for the claimed changes",
        )

    def build_runtime_prompt_context(self, work_path: Optional[Path] = None) -> dict[str, str]:
        latest_work = work_path or self._get_latest_work_path()
        latest_verify = (
            self._get_latest_same_day_verify_path_for_work(latest_work)
            or self._get_latest_same_day_verify_path(latest_work)
        )
        gemini_report_hint = self._infer_gemini_report_hint(latest_work)
        gemini_report_path = self.report_gemini_dir / gemini_report_hint
        active_control = self._get_active_control_signal()
        return {
            "latest_work_path": self._repo_relative(latest_work),
            "latest_verify_path": self._repo_relative(latest_verify),
            "gemini_report_dir": self._repo_relative(self.report_gemini_dir) + "/",
            "gemini_report_hint": gemini_report_hint,
            "gemini_report_path": self._repo_relative(gemini_report_path),
            "claude_handoff_path": self._repo_relative(self.claude_handoff_path),
            "gemini_request_path": self._repo_relative(self.gemini_request_path),
            "gemini_advice_path": self._repo_relative(self.gemini_advice_path),
            "operator_request_path": self._repo_relative(self.operator_request_path),
            "latest_work_mention": self._path_mention(latest_work),
            "latest_verify_mention": self._path_mention(latest_verify),
            "gemini_request_mention": self._path_mention(self.gemini_request_path),
            "gemini_advice_mention": self._path_mention(self.gemini_advice_path),
            "active_control_path": self._repo_relative(active_control.path if active_control else None),
            "active_control_status": active_control.status if active_control else "none",
            "active_control_sig": active_control.sig if active_control else "",
            "active_control_seq": str(active_control.control_seq if active_control and active_control.control_seq >= 0 else "none"),
            "next_control_seq": str(self._get_next_control_seq()),
            "runtime_enabled_lanes": ",".join(self.runtime_enabled_lanes or []),
            "runtime_implement_owner": self._role_owner("implement") or "none",
            "runtime_verify_owner": self._role_owner("verify") or "none",
            "runtime_advisory_owner": self._role_owner("advisory") or "none",
            "runtime_implement_read_first_doc": self._role_read_first_doc("implement"),
            "runtime_verify_read_first_doc": self._role_read_first_doc("verify"),
            "runtime_advisory_read_first_doc": self._role_read_first_doc("advisory"),
            "runtime_advisory_enabled": "true" if self.runtime_controls.get("advisory_enabled") else "false",
            "runtime_operator_stop_enabled": "true" if self.runtime_controls.get("operator_stop_enabled") else "false",
            "runtime_session_arbitration_enabled": "true" if self.runtime_controls.get("session_arbitration_enabled") else "false",
        }

    def build_verify_prompt_context(self, artifact_path: str) -> dict[str, str]:
        artifact = Path(artifact_path)
        verify_scope_label, verify_scope_hint = self.verify_scope_hint_for_work(artifact)
        return {
            "artifact_path": artifact_path,
            "verify_scope_label": verify_scope_label,
            "verify_scope_hint": verify_scope_hint,
            **self.build_runtime_prompt_context(artifact),
        }

    def build_implement_prompt_context(self, handoff_path: Optional[Path] = None) -> dict[str, str]:
        handoff = handoff_path or self.claude_handoff_path
        return {
            **self.build_runtime_prompt_context(),
            "active_handoff_path": self._repo_relative(handoff),
            "active_handoff_sha": self._get_path_sha256(handoff),
        }

    def format_runtime_prompt(self, template: str, work_path: Optional[Path] = None) -> str:
        return self._finalize_prompt_text(template.format(**self.build_runtime_prompt_context(work_path)))

    def format_implement_prompt(self, handoff_path: Optional[Path] = None) -> str:
        return self._finalize_prompt_text(
            self.implement_prompt.format(**self.build_implement_prompt_context(handoff_path))
        )

    def format_verify_triage_prompt(self, signal: Mapping[str, object]) -> str:
        context = {
            **self.build_implement_prompt_context(self.claude_handoff_path),
            "blocked_source": str(signal.get("source", "sentinel")),
            "blocked_reason": str(signal.get("reason", "implement_blocked")),
            "blocked_reason_code": str(signal.get("reason_code", "")),
            "blocked_escalation_class": str(signal.get("escalation_class", "codex_triage")),
            "blocked_fingerprint": str(signal.get("fingerprint", "")),
            "blocked_excerpt": "\n".join(
                f"- {line}" for line in signal.get("excerpt_lines", [])
            ) or "- (없음)",
        }
        return self._finalize_prompt_text(self.verify_triage_prompt.format(**context))

    def format_control_recovery_prompt(self, marker: Mapping[str, object]) -> str:
        resolved_paths = list(marker.get("resolved_work_paths") or [])
        context = {
            **self.build_runtime_prompt_context(),
            "stale_control_path": ".pipeline/operator_request.md",
            "stale_control_seq": str(marker.get("control_seq") or "none"),
            "stale_control_reason": str(marker.get("reason") or "verified_blockers_resolved"),
            "stale_control_resolved_work_paths": "\n".join(f"- {path}" for path in resolved_paths) or "- (없음)",
        }
        return self._finalize_prompt_text(self.control_recovery_prompt.format(**context))

    def format_operator_retriage_prompt(self, marker: Mapping[str, object]) -> str:
        context = {
            **self.build_runtime_prompt_context(),
            "stale_control_seq": str(marker.get("control_seq") or "none"),
            "stale_control_reason": str(marker.get("reason") or "operator_wait_idle_retriage"),
            "operator_wait_age_sec": str(marker.get("operator_wait_age_sec") or "0"),
        }
        return self._finalize_prompt_text(self.operator_retriage_prompt.format(**context))

    def format_session_arbitration_draft(self, signal: Mapping[str, object]) -> str:
        context = self.build_runtime_prompt_context()
        reasons = [str(reason) for reason in signal.get("reasons", [])]
        excerpt_lines = [str(line) for line in signal.get("excerpt_lines", [])]
        reason_lines = "\n".join(f"- {reason}" for reason in reasons) or "- (없음)"
        excerpt_block = "\n".join(f"> {line}" for line in excerpt_lines) or "> (없음)"
        return (
            "STATUS: draft_only\n\n"
            "역할:\n"
            "- watcher가 active Claude session의 live side question 신호를 감지해 남긴 non-canonical draft\n"
            "- 이 파일은 자동 실행 슬롯이 아니며 watcher와 Claude/Gemini는 이 파일만으로 dispatch하지 않음\n"
            "- Codex가 보고 short lane reply로 끝낼지, `.pipeline/gemini_request.md`로 승격할지 결정해야 함\n\n"
            "감지 이유:\n"
            f"{reason_lines}\n\n"
            "현재 round-start contract:\n"
            f"- `.pipeline/claude_handoff.md`: {context['claude_handoff_path']}\n"
            f"- latest `/work`: {context['latest_work_path']}\n"
            f"- latest `/verify`: {context['latest_verify_path']}\n\n"
            "관찰 excerpt:\n"
            f"{excerpt_block}\n\n"
            "Codex next step:\n"
            "- active session을 mid-session handoff rewrite 없이 처리할지 먼저 판단\n"
            "- 필요하면 Gemini arbitration request를 사람이 검토 가능한 canonical 슬롯으로만 승격\n"
            "- 그렇지 않으면 Claude에게 short lane reply만 전달\n"
        )

    def build_implement_dispatch_spec(
        self,
        reason: str,
        handoff_path: Optional[Path] = None,
    ) -> PromptDispatchSpec:
        prompt_path = handoff_path or self.claude_handoff_path
        control_seq = self._read_control_seq_from_path(prompt_path)
        identity = self._lane_identity(
            functional_role="implement",
            notify_kind="claude_handoff",
            control_seq=control_seq,
        )
        return PromptDispatchSpec(
            pending_key=str(identity["pending_key"]),
            notify_kind="claude_handoff",
            lane_role="implement",
            functional_role="implement",
            lane_id=str(identity["lane_id"]),
            agent_kind=str(identity["agent_kind"]),
            model_alias=None,
            prompt=self.format_implement_prompt(handoff_path),
            prompt_path=prompt_path,
            notify_label="notify_implement_owner",
            raw_event="implement_notify",
            raw_payload={
                "reason": reason,
                **self._identity_payload(
                    functional_role="implement",
                    lane_id=str(identity["lane_id"]),
                    agent_kind=str(identity["agent_kind"]),
                    model_alias=None,
                ),
            },
            control_seq=control_seq,
            expected_status="implement",
            expected_control_path=str(prompt_path.name),
            expected_control_seq=control_seq,
            require_active_control=True,
        )

    def build_claude_dispatch_spec(
        self,
        reason: str,
        handoff_path: Optional[Path] = None,
    ) -> PromptDispatchSpec:
        return self.build_implement_dispatch_spec(reason, handoff_path)

    def build_gemini_dispatch_spec(self, reason: str) -> PromptDispatchSpec:
        control_seq = self._read_control_seq_from_path(self.gemini_request_path)
        identity = self._lane_identity(
            functional_role="advisory",
            notify_kind="gemini_request",
            control_seq=control_seq,
        )
        return PromptDispatchSpec(
            pending_key=str(identity["pending_key"]),
            notify_kind="gemini_request",
            lane_role="advisory",
            functional_role="advisory",
            lane_id=str(identity["lane_id"]),
            agent_kind=str(identity["agent_kind"]),
            model_alias=None,
            prompt=self.format_runtime_prompt(self.advisory_prompt),
            prompt_path=self.gemini_request_path,
            notify_label="notify_advisory_owner",
            raw_event="advisory_notify",
            raw_payload={
                "reason": reason,
                **self._identity_payload(
                    functional_role="advisory",
                    lane_id=str(identity["lane_id"]),
                    agent_kind=str(identity["agent_kind"]),
                    model_alias=None,
                ),
            },
            control_seq=control_seq,
            expected_status="request_open",
            expected_control_path=str(self.gemini_request_path.name),
            expected_control_seq=control_seq,
            require_active_control=True,
        )

    def build_verify_followup_dispatch_spec(self, reason: str) -> PromptDispatchSpec:
        control_seq = self._read_control_seq_from_path(self.gemini_advice_path)
        identity = self._lane_identity(
            functional_role="verify",
            notify_kind="gemini_advice_followup",
            control_seq=control_seq,
        )
        return PromptDispatchSpec(
            pending_key=str(identity["pending_key"]),
            notify_kind="gemini_advice_followup",
            lane_role="verify",
            functional_role="verify",
            lane_id=str(identity["lane_id"]),
            agent_kind=str(identity["agent_kind"]),
            model_alias=None,
            prompt=self.format_runtime_prompt(self.followup_prompt),
            prompt_path=self.gemini_advice_path,
            notify_label="notify_verify_followup",
            raw_event="verify_followup_notify",
            raw_payload={
                "reason": reason,
                **self._identity_payload(
                    functional_role="verify",
                    lane_id=str(identity["lane_id"]),
                    agent_kind=str(identity["agent_kind"]),
                    model_alias=None,
                ),
            },
            control_seq=control_seq,
            expected_status="advice_ready",
            expected_control_path=str(self.gemini_advice_path.name),
            expected_control_seq=control_seq,
            require_active_control=True,
        )

    def build_codex_followup_dispatch_spec(self, reason: str) -> PromptDispatchSpec:
        return self.build_verify_followup_dispatch_spec(reason)

    def build_control_recovery_dispatch_spec(
        self,
        marker: Mapping[str, object],
        reason: str,
    ) -> PromptDispatchSpec:
        control_seq = int(marker.get("control_seq") or -1)
        identity = self._lane_identity(
            functional_role="verify",
            notify_kind="codex_control_recovery",
            control_seq=control_seq,
        )
        return PromptDispatchSpec(
            pending_key=str(identity["pending_key"]),
            notify_kind="codex_control_recovery",
            lane_role="verify",
            functional_role="verify",
            lane_id=str(identity["lane_id"]),
            agent_kind=str(identity["agent_kind"]),
            model_alias=None,
            prompt=self.format_control_recovery_prompt(marker),
            prompt_path=self.operator_request_path,
            notify_label="notify_verify_control_recovery",
            raw_event="verify_control_recovery_notify",
            raw_payload={
                "reason": reason,
                **marker,
                **self._identity_payload(
                    functional_role="verify",
                    lane_id=str(identity["lane_id"]),
                    agent_kind=str(identity["agent_kind"]),
                    model_alias=None,
                ),
            },
            control_seq=control_seq,
            expected_control_path=str(self.operator_request_path.name),
            expected_control_seq=control_seq,
            expected_status="needs_operator",
        )

    def build_operator_retriage_dispatch_spec(
        self,
        marker: Mapping[str, object],
        reason: str,
    ) -> PromptDispatchSpec:
        control_seq = int(marker.get("control_seq") or -1)
        identity = self._lane_identity(
            functional_role="verify",
            notify_kind="codex_operator_retriage",
            control_seq=control_seq,
        )
        return PromptDispatchSpec(
            pending_key=str(identity["pending_key"]),
            notify_kind="codex_operator_retriage",
            lane_role="verify",
            functional_role="verify",
            lane_id=str(identity["lane_id"]),
            agent_kind=str(identity["agent_kind"]),
            model_alias=None,
            prompt=self.format_operator_retriage_prompt(marker),
            prompt_path=self.operator_request_path,
            notify_label="notify_verify_operator_retriage",
            raw_event="verify_operator_retriage_notify",
            raw_payload={
                "reason": reason,
                **marker,
                **self._identity_payload(
                    functional_role="verify",
                    lane_id=str(identity["lane_id"]),
                    agent_kind=str(identity["agent_kind"]),
                    model_alias=None,
                ),
            },
            control_seq=control_seq,
            expected_control_path=str(self.operator_request_path.name),
            expected_control_seq=control_seq,
            expected_status="needs_operator",
        )

    def build_blocked_triage_dispatch_spec(
        self,
        signal: Mapping[str, object],
        reason: str,
    ) -> PromptDispatchSpec:
        control_seq = self._read_control_seq_from_path(self.claude_handoff_path)
        handoff_sha = self._get_path_sha256(self.claude_handoff_path)
        identity = self._lane_identity(
            functional_role="verify",
            notify_kind="codex_blocked_triage",
            control_seq=control_seq,
        )
        return PromptDispatchSpec(
            pending_key=str(identity["pending_key"]),
            notify_kind="codex_blocked_triage",
            lane_role="verify",
            functional_role="verify",
            lane_id=str(identity["lane_id"]),
            agent_kind=str(identity["agent_kind"]),
            model_alias=None,
            prompt=self.format_verify_triage_prompt(signal),
            prompt_path=self.claude_handoff_path,
            notify_label="notify_verify_blocked_triage",
            raw_event="verify_blocked_triage_notify",
            raw_payload={
                "reason": reason,
                "blocked_reason": str(signal.get("reason", "implement_blocked")),
                "blocked_reason_code": str(signal.get("reason_code", "")),
                "blocked_source": str(signal.get("source", "sentinel")),
                "blocked_escalation_class": str(signal.get("escalation_class", "codex_triage")),
                "blocked_fingerprint": str(signal.get("fingerprint", "")),
                "handoff_sha": handoff_sha,
                **self._identity_payload(
                    functional_role="verify",
                    lane_id=str(identity["lane_id"]),
                    agent_kind=str(identity["agent_kind"]),
                    model_alias=None,
                ),
            },
            control_seq=control_seq,
            expected_control_path=str(self.claude_handoff_path.name),
            expected_control_seq=control_seq,
            expected_status="implement",
        )
