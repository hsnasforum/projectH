from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Any
from uuid import uuid4


class WebSearchStore:
    def __init__(self, base_dir: str = "data/web-search") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _session_dir(self, session_id: str) -> Path:
        return self.base_dir / session_id

    def _normalize_loaded_record(self, *, path: Path, record: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(record)
        normalized["record_path"] = str(path)
        return normalized

    def _trim_preview(self, value: Any, *, max_chars: int = 240) -> str:
        text = " ".join(str(value or "").split())
        if len(text) <= max_chars:
            return text
        return text[: max_chars - 1].rstrip() + "…"

    def _looks_like_contact_or_legal_preview_text(self, value: Any) -> bool:
        normalized = " ".join(str(value or "").split()).strip()
        lowered = normalized.lower()
        if not normalized:
            return False
        legal_markers = [
            "대표이사",
            "사업자등록번호",
            "통신판매업",
            "고객센터",
            "개인정보처리방침",
            "청소년보호정책",
            "이메일무단수집거부",
            "e-mail",
            "email",
            "팩스",
            "fax",
            "전화",
            "tel",
            "contact",
            "corp.",
            "co., ltd",
            "(주)",
        ]
        marker_count = sum(1 for marker in legal_markers if marker in normalized or marker in lowered)
        has_email = bool(re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", normalized))
        has_phone = bool(re.search(r"\b\d{2,4}-\d{3,4}-\d{4}\b", normalized))
        has_business_number = bool(re.search(r"\b\d{3}-\d{2}-\d{5}\b", normalized))
        if marker_count >= 2:
            return True
        if marker_count >= 1 and (has_email or has_phone or has_business_number):
            return True
        if sum(1 for flag in [has_email, has_phone, has_business_number] if flag) >= 2:
            return True
        return False

    def _looks_like_noisy_preview_text(self, value: Any) -> bool:
        normalized = " ".join(str(value or "").split()).strip()
        lowered = normalized.lower()
        if not normalized:
            return False
        if len(normalized) < 14:
            return True
        if self._looks_like_contact_or_legal_preview_text(normalized):
            return True
        boilerplate_hints = [
            "로그인",
            "로그아웃",
            "회원가입",
            "구독",
            "광고",
            "전체메뉴",
            "기사제보",
            "pdf보기",
            "이용약관",
            "개인정보",
            "쿠키",
            "all rights reserved",
            "copyright",
            "facebook",
            "twitter",
            "instagram",
            "youtube",
            "threads",
            "line",
            "카카오톡",
            "네이버",
            "다음",
            "언론사",
            "rss",
            "english",
            "japanese",
            "deutsch",
            "русский",
            "tiếng",
            "nederlands",
            "italiano",
        ]
        marketing_hints = [
            "이용해 보세요",
            "지금 바로",
            "자세히 보기",
            "바로가기",
        ]
        hint_count = sum(1 for hint in boilerplate_hints if hint in normalized or hint in lowered)
        if hint_count >= 2:
            return True
        if any(hint in normalized or hint in lowered for hint in marketing_hints):
            return True
        if normalized.count("/") >= 5 or normalized.count("|") >= 3:
            return True
        if len(re.findall(r"[·|/]", normalized)) >= 6:
            return True
        return False

    def _result_snippet_lookup(self, record: dict[str, Any]) -> dict[str, str]:
        snippets_by_url: dict[str, str] = {}
        for result in record.get("results", []):
            if not isinstance(result, dict):
                continue
            url = str(result.get("url") or "").strip()
            snippet = " ".join(str(result.get("snippet") or "").split()).strip()
            if not url or not snippet or url in snippets_by_url:
                continue
            snippets_by_url[url] = snippet
        return snippets_by_url

    def _build_pages_preview(self, record: dict[str, Any], *, max_pages: int = 3) -> list[dict[str, Any]]:
        previews: list[dict[str, Any]] = []
        snippets_by_url = self._result_snippet_lookup(record)
        for page in record.get("pages", []):
            if not isinstance(page, dict):
                continue
            if str(page.get("fetch_status") or "") != "ok":
                continue

            url = str(page.get("url") or "").strip()
            title = str(page.get("title") or page.get("source_title") or url or "원문 페이지")
            focused_text = " ".join(str(page.get("focused_text") or "").split()).strip()
            excerpt = " ".join(str(page.get("excerpt") or "").split()).strip()
            result_snippet = snippets_by_url.get(url, "")
            text = str(page.get("text") or "")
            safe_focused_text = focused_text if focused_text and not self._looks_like_noisy_preview_text(focused_text) else ""
            safe_excerpt = excerpt if excerpt and not self._looks_like_noisy_preview_text(excerpt) else ""
            safe_result_snippet = (
                result_snippet
                if result_snippet and not self._looks_like_noisy_preview_text(result_snippet)
                else result_snippet
            )
            preview_excerpt_source = (
                safe_focused_text
                or safe_result_snippet
                or safe_excerpt
                or focused_text
                or result_snippet
                or excerpt
                or text
            )
            preview_text_source = (
                safe_focused_text
                or safe_result_snippet
                or safe_excerpt
                or focused_text
                or result_snippet
                or excerpt
                or text
            )
            char_count = int(page.get("char_count") or len(text))
            previews.append(
                {
                    "title": title,
                    "url": url,
                    "excerpt": self._trim_preview(preview_excerpt_source, max_chars=180),
                    "text_preview": self._trim_preview(preview_text_source, max_chars=260),
                    "char_count": char_count,
                }
            )
            if len(previews) >= max_pages:
                break
        return previews

    def _summarize_claim_coverage(self, claim_coverage: list[dict[str, Any]] | None) -> dict[str, int]:
        counts = {"strong": 0, "weak": 0, "missing": 0}
        for item in claim_coverage or []:
            if not isinstance(item, dict):
                continue
            status = str(item.get("status") or "").strip()
            if status in counts:
                counts[status] += 1
        return counts

    def save(
        self,
        *,
        session_id: str,
        query: str,
        permission: str,
        results: list[dict[str, Any]],
        summary_text: str,
        pages: list[dict[str, Any]] | None = None,
        response_origin: dict[str, Any] | None = None,
        claim_coverage: list[dict[str, Any]] | None = None,
        claim_coverage_progress_summary: str | None = None,
    ) -> dict[str, Any]:
        timestamp = datetime.now(timezone.utc).isoformat()
        slug = re.sub(r"[^a-zA-Z0-9가-힣]+", "-", query).strip("-").lower() or "search"
        record_id = f"websearch-{uuid4().hex[:12]}"
        session_dir = self._session_dir(session_id)
        session_dir.mkdir(parents=True, exist_ok=True)
        path = session_dir / f"{slug}-{record_id}.json"
        normalized_pages = list(pages or [])
        ok_page_count = len(
            [
                page
                for page in normalized_pages
                if isinstance(page, dict) and str(page.get("fetch_status") or "") == "ok"
            ]
        )
        record = {
            "record_id": record_id,
            "session_id": session_id,
            "query": query,
            "permission": permission,
            "created_at": timestamp,
            "result_count": len(results),
            "page_count": ok_page_count,
            "results": results,
            "pages": normalized_pages,
            "summary_text": summary_text,
            "response_origin": dict(response_origin or {}),
            "claim_coverage": [dict(item) for item in claim_coverage or [] if isinstance(item, dict)],
            "claim_coverage_progress_summary": str(claim_coverage_progress_summary or "").strip(),
        }
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "record_id": record_id,
            "record_path": str(path),
            "record": record,
        }

    def list_session_records(self, session_id: str, *, limit: int = 10) -> list[dict[str, Any]]:
        session_dir = self._session_dir(session_id)
        if not session_dir.exists():
            return []

        records: list[dict[str, Any]] = []
        for path in sorted(session_dir.glob("*.json"), reverse=True):
            try:
                loaded = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(loaded, dict):
                continue
            records.append(self._normalize_loaded_record(path=path, record=loaded))
            if len(records) >= limit:
                break
        return records

    def get_latest_session_record(self, session_id: str) -> dict[str, Any] | None:
        records = self.list_session_records(session_id, limit=1)
        if not records:
            return None
        return records[0]

    def get_session_record(self, session_id: str, record_id: str) -> dict[str, Any] | None:
        normalized_record_id = str(record_id or "").strip()
        if not normalized_record_id:
            return None

        session_dir = self._session_dir(session_id)
        if not session_dir.exists():
            return None

        for path in sorted(session_dir.glob("*.json"), reverse=True):
            try:
                loaded = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(loaded, dict):
                continue
            if str(loaded.get("record_id") or "").strip() != normalized_record_id:
                continue
            return self._normalize_loaded_record(path=path, record=loaded)
        return None

    def list_session_record_summaries(self, session_id: str, *, limit: int = 8) -> list[dict[str, Any]]:
        summaries: list[dict[str, Any]] = []
        for record in self.list_session_records(session_id, limit=limit):
            summary_text = str(record.get("summary_text") or "").strip()
            first_line = summary_text.splitlines()[0].strip() if summary_text else ""
            summaries.append(
                {
                    "record_id": str(record.get("record_id") or ""),
                    "query": str(record.get("query") or ""),
                    "created_at": str(record.get("created_at") or ""),
                    "result_count": int(record.get("result_count") or 0),
                    "page_count": int(record.get("page_count") or 0),
                    "record_path": str(record.get("record_path") or ""),
                    "summary_head": first_line,
                    "answer_mode": str((record.get("response_origin") or {}).get("answer_mode") or "general"),
                    "verification_label": str((record.get("response_origin") or {}).get("verification_label") or ""),
                    "source_roles": [
                        str(item)
                        for item in (record.get("response_origin") or {}).get("source_roles", [])
                        if str(item).strip()
                    ],
                    "claim_coverage_summary": self._summarize_claim_coverage(record.get("claim_coverage")),
                    "claim_coverage_progress_summary": str(record.get("claim_coverage_progress_summary") or "").strip(),
                    "pages_preview": self._build_pages_preview(record),
                }
            )
        return summaries
