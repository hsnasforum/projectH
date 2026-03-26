from __future__ import annotations

import argparse

from app.localization import localize_text
from config.settings import AppSettings
from core.agent_loop import AgentLoop, UserRequest
from model_adapter.base import ModelAdapter, ModelAdapterError, ModelRuntimeStatus
from model_adapter.factory import build_model_adapter
from storage.session_store import SessionStore
from storage.task_log import TaskLogger
from tools.file_reader import FileReaderTool
from tools.file_search import FileSearchTool
from tools.write_note import WriteNoteTool


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="첫 번째 요약/저장 세로 흐름을 실행합니다.")
    parser.add_argument("source_path", nargs="?", default="README.md", help="요약할 파일 경로입니다.")
    parser.add_argument(
        "--search-root",
        help="일치하는 파일을 요약하기 전에 검색할 디렉터리 루트입니다.",
    )
    parser.add_argument(
        "--search-query",
        help="--search-root와 함께 사용할 검색어입니다.",
    )
    parser.add_argument(
        "--search-limit",
        type=int,
        default=3,
        help="검색 기반 요약에서 읽을 최대 파일 수입니다.",
    )
    parser.add_argument(
        "--search-only",
        action="store_true",
        help="요약하지 않고 번호가 붙은 검색 결과와 발췌만 보여줍니다.",
    )
    parser.add_argument(
        "--select",
        help="요약할 검색 결과 번호입니다. 예: 1,3",
    )
    parser.add_argument(
        "--select-path",
        action="append",
        help="요약할 검색 결과 경로 또는 고유한 경로 suffix입니다. 반복 지정하거나 쉼표로 구분해 사용할 수 있습니다.",
    )
    parser.add_argument("--save", action="store_true", help="생성된 요약 노트 저장을 요청합니다.")
    parser.add_argument(
        "--approved",
        action="store_true",
        help="노트 저장 승인을 확정합니다.",
    )
    parser.add_argument(
        "--approved-approval-id",
        help="기존 승인 대기 중인 저장 요청을 승인할 때 사용할 approval_id입니다.",
    )
    parser.add_argument(
        "--rejected-approval-id",
        help="기존 승인 대기 중인 저장 요청을 취소할 때 사용할 approval_id입니다.",
    )
    parser.add_argument(
        "--session-id",
        default="demo-session",
        help="세션 식별자입니다. 승인 재실행 시 같은 세션 ID를 사용해야 합니다.",
    )
    parser.add_argument(
        "--note-path",
        help="선택적 노트 출력 경로입니다. 기본값은 data/notes/<source>-summary.md 입니다.",
    )
    parser.add_argument(
        "--provider",
        choices=["mock", "ollama"],
        help="사용할 모델 프로바이더입니다. 기본값은 LOCAL_AI_MODEL_PROVIDER 또는 mock입니다.",
    )
    parser.add_argument(
        "--model",
        help="로컬 런타임 모델 이름입니다. provider=ollama일 때 사용합니다.",
    )
    parser.add_argument(
        "--base-url",
        help="로컬 런타임 기본 URL입니다. provider=ollama일 때 사용합니다.",
    )
    parser.add_argument(
        "--skip-preflight",
        action="store_true",
        help="요청 처리 전 런타임 상태와 모델 설치 여부 확인을 건너뜁니다.",
    )
    parser.add_argument(
        "--show-preview",
        action="store_true",
        help="노트 미리보기가 있으면 함께 출력합니다.",
    )
    return parser


def parse_selected_indices(raw_value: str | None) -> list[int] | None:
    if raw_value is None or not raw_value.strip():
        return None

    indices: list[int] = []
    for part in raw_value.split(","):
        value = part.strip()
        if not value:
            continue
        if not value.isdigit():
            raise ValueError(f"선택 값 '{value}'이 올바르지 않습니다. 쉼표로 구분된 양의 정수를 사용해 주세요.")
        parsed = int(value)
        if parsed <= 0:
            raise ValueError(f"선택 값 '{value}'이 올바르지 않습니다. 번호는 1 이상의 정수여야 합니다.")
        indices.append(parsed)
    return indices or None


def parse_selected_paths(raw_values: list[str] | None) -> list[str] | None:
    if not raw_values:
        return None

    selected_paths: list[str] = []
    for raw_value in raw_values:
        if not raw_value.strip():
            continue
        for part in raw_value.split(","):
            value = part.strip()
            if value:
                selected_paths.append(value)
    return selected_paths or None


def preflight_model(model: ModelAdapter) -> ModelRuntimeStatus:
    status = model.health_check()
    if not status.reachable:
        raise ModelAdapterError(status.detail)
    if not status.configured_model_available:
        raise ModelAdapterError(status.detail)
    return status


def main() -> int:
    args = build_parser().parse_args()
    settings = AppSettings.from_env()
    provider = args.provider or settings.model_provider
    try:
        selected_indices = parse_selected_indices(args.select)
        selected_paths = parse_selected_paths(args.select_path)
        if args.approved_approval_id and args.rejected_approval_id:
            raise ValueError("승인과 취소 approval_id는 동시에 사용할 수 없습니다.")

        model_name = args.model or settings.ollama_model
        if provider == "ollama" and not model_name:
            raise ValueError("Ollama를 사용할 때는 --model 또는 LOCAL_AI_OLLAMA_MODEL 값을 지정해야 합니다.")

        model = build_model_adapter(
            provider=provider,
            ollama_base_url=args.base_url or settings.ollama_base_url,
            ollama_model=model_name,
            ollama_timeout_seconds=settings.ollama_timeout_seconds,
        )
        runtime_status = None
        approval_only = bool(args.approved_approval_id or args.rejected_approval_id)
        needs_model = not approval_only and not (args.search_root and args.search_query and args.search_only)
        if not args.skip_preflight and needs_model:
            runtime_status = preflight_model(model)

        session_store = SessionStore(base_dir=settings.sessions_dir)
        task_logger = TaskLogger(path=settings.task_log_path)
        tools = {
            "read_file": FileReaderTool(),
            "search_files": FileSearchTool(),
            "write_note": WriteNoteTool(allowed_roots=[".", settings.notes_dir]),
        }

        user_text = ""
        metadata: dict[str, object] = {}
        if args.approved_approval_id or args.rejected_approval_id:
            user_text = ""
            metadata = {}
        elif args.search_root and args.search_query:
            user_text = f"{args.search_root}에서 '{args.search_query}'를 검색하고 결과를 요약해 주세요."
            metadata = {
                "search_root": args.search_root,
                "search_query": args.search_query,
                "search_result_limit": args.search_limit,
                "search_only": args.search_only,
                "search_selected_indices": selected_indices,
                "search_selected_paths": selected_paths,
                "save_summary": args.save,
                "note_path": args.note_path,
            }
        else:
            user_text = f"{args.source_path} 파일을 요약해 주세요."
            metadata = {
                "source_path": args.source_path,
                "save_summary": args.save,
                "note_path": args.note_path,
            }

        loop = AgentLoop(
            model=model,
            session_store=session_store,
            task_logger=task_logger,
            tools=tools,
            notes_dir=settings.notes_dir,
        )
        request = UserRequest(
            user_text=user_text,
            session_id=args.session_id,
            approved=args.approved,
            approved_approval_id=args.approved_approval_id,
            rejected_approval_id=args.rejected_approval_id,
            metadata=metadata,
        )
        response = loop.handle(request)
        print(f"모델 프로바이더: {provider}")
        if runtime_status:
            print(localize_text(runtime_status.detail))
            if runtime_status.version:
                print(f"런타임 버전: {runtime_status.version}")
        print(localize_text(response.text))
        if response.note_preview and (args.show_preview or response.requires_approval):
            print("노트 미리보기:")
            print(localize_text(response.note_preview))
        if response.requires_approval and response.proposed_note_path:
            print(f"승인 필요 경로: {response.proposed_note_path}")
        if response.approval:
            approval_id = response.approval.get("approval_id")
            if approval_id:
                print(f"approval_id: {approval_id}")
        if response.saved_note_path:
            print(f"저장된 노트: {response.saved_note_path}")
        return 0
    except ValueError as exc:
        print(f"CLI 입력 오류: {exc}")
        return 2
    except ModelAdapterError as exc:
        print(f"모델 초기화 실패: {localize_text(str(exc))}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
