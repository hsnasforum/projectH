from __future__ import annotations

from dataclasses import dataclass
import importlib
from pathlib import Path

from tools.base import Tool
from tools.path_utils import normalize_local_path_input


@dataclass(slots=True)
class FileReadResult:
    requested_path: str
    resolved_path: str
    text: str
    size_bytes: int
    content_format: str
    extraction_method: str
    encoding_used: str | None = None


class UnsupportedFileError(RuntimeError):
    pass


class OcrRequiredError(RuntimeError):
    pass


class FileReaderTool(Tool):
    name = "read_file"
    _TEXT_ENCODINGS = (
        "utf-8",
        "utf-8-sig",
        "cp949",
        "euc-kr",
    )

    def run(self, *, path: str) -> FileReadResult:
        file_path = normalize_local_path_input(path)
        resolved_path = file_path.resolve(strict=True)
        if not resolved_path.is_file():
            raise IsADirectoryError(f"Expected a file path, got: {resolved_path}")

        return self._build_result_from_bytes(
            requested_path=str(file_path),
            resolved_path=str(resolved_path),
            raw_bytes=resolved_path.read_bytes(),
            suffix=resolved_path.suffix.lower(),
        )

    def run_uploaded(
        self,
        *,
        name: str,
        content_bytes: bytes,
        mime_type: str | None = None,
    ) -> FileReadResult:
        normalized_name = Path(name or "selected-file.txt").name or "selected-file.txt"
        normalized_mime = (mime_type or "").strip().lower()
        synthetic_path = normalized_name
        suffix = Path(normalized_name).suffix.lower()
        if normalized_mime == "application/pdf" and suffix != ".pdf":
            suffix = ".pdf"

        return self._build_result_from_bytes(
            requested_path=synthetic_path,
            resolved_path=synthetic_path,
            raw_bytes=content_bytes,
            suffix=suffix,
            extraction_method_prefix="browser_upload",
        )

    def _build_result_from_bytes(
        self,
        *,
        requested_path: str,
        resolved_path: str,
        raw_bytes: bytes,
        suffix: str,
        extraction_method_prefix: str = "",
    ) -> FileReadResult:
        if suffix == ".pdf":
            text = self._read_pdf_text_from_bytes(raw_bytes)
            extraction_method = "pypdf"
            if extraction_method_prefix:
                extraction_method = f"{extraction_method_prefix}_{extraction_method}"
            return FileReadResult(
                requested_path=requested_path,
                resolved_path=resolved_path,
                text=text,
                size_bytes=len(raw_bytes),
                content_format="pdf",
                extraction_method=extraction_method,
            )

        text, encoding_used = self._decode_text_bytes(raw_bytes)
        extraction_method = "decode"
        if extraction_method_prefix:
            extraction_method = f"{extraction_method_prefix}_{extraction_method}"
        return FileReadResult(
            requested_path=requested_path,
            resolved_path=resolved_path,
            text=text,
            size_bytes=len(raw_bytes),
            content_format="text",
            extraction_method=extraction_method,
            encoding_used=encoding_used,
        )

    def _decode_text_bytes(self, raw_bytes: bytes) -> tuple[str, str]:
        if not raw_bytes:
            return "", "utf-8"

        if raw_bytes.startswith(b"\xff\xfe"):
            return raw_bytes.decode("utf-16-le"), "utf-16-le"
        if raw_bytes.startswith(b"\xfe\xff"):
            return raw_bytes.decode("utf-16-be"), "utf-16-be"

        for encoding in self._TEXT_ENCODINGS:
            try:
                return raw_bytes.decode(encoding), encoding
            except UnicodeDecodeError:
                continue

        if self._looks_like_binary(raw_bytes):
            raise UnsupportedFileError("Unsupported binary file. Only text-like files and PDFs are supported.")

        return raw_bytes.decode("utf-8", errors="replace"), "utf-8-replace"

    def _looks_like_binary(self, raw_bytes: bytes) -> bool:
        if not raw_bytes:
            return False
        sample = raw_bytes[:2048]
        if b"\x00" in sample:
            return True

        control_bytes = sum(1 for value in sample if value < 9 or 13 < value < 32)
        return control_bytes > max(8, len(sample) // 10)

    def _read_pdf_text(self, resolved_path: Path) -> str:
        try:
            raw_bytes = resolved_path.read_bytes()
        except Exception as exc:
            raise RuntimeError(f"Unable to open PDF file: {resolved_path}") from exc
        return self._read_pdf_text_from_bytes(raw_bytes, path_hint=str(resolved_path))

    def _read_pdf_text_from_bytes(self, raw_bytes: bytes, *, path_hint: str = "(uploaded pdf)") -> str:
        try:
            pypdf = importlib.import_module("pypdf")
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "PDF reading requires the optional 'pypdf' dependency. Install project dependencies first."
            ) from exc

        try:
            from io import BytesIO

            reader = pypdf.PdfReader(BytesIO(raw_bytes))
        except Exception as exc:
            raise RuntimeError(f"Unable to open PDF file: {path_hint}") from exc

        pages: list[str] = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            normalized = page_text.strip()
            if normalized:
                pages.append(normalized)

        if not pages:
            raise OcrRequiredError(
                "PDF 안에 추출 가능한 텍스트가 없습니다. 스캔본 또는 이미지형 PDF일 수 있으며, 이 MVP에서는 OCR을 지원하지 않습니다."
            )
        return "\n\n".join(pages)
