from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tools.base import Tool
from tools.file_reader import FileReaderTool, OcrRequiredError, UnsupportedFileError
from tools.path_utils import normalize_local_path_input


@dataclass(slots=True)
class FileSearchResult:
    path: str
    matched_on: str
    snippet: str


@dataclass(slots=True)
class FileSearchRunStats:
    skipped_ocr_paths: list[str]


class FileSearchTool(Tool):
    name = "search_files"

    def __init__(self, reader: FileReaderTool | None = None) -> None:
        self.reader = reader or FileReaderTool()
        self.last_run_stats = FileSearchRunStats(skipped_ocr_paths=[])

    def run(self, *, root: str, query: str, max_results: int = 10) -> list[FileSearchResult]:
        root_path = normalize_local_path_input(root).resolve(strict=True)
        if not root_path.is_dir():
            raise NotADirectoryError(f"Expected a directory root, got: {root_path}")

        matches: list[FileSearchResult] = []
        stats = FileSearchRunStats(skipped_ocr_paths=[])
        lowered_query = query.lower()
        for path in root_path.rglob("*"):
            if not path.is_file():
                continue

            resolved_path = str(path.resolve())
            if lowered_query in path.name.lower():
                matches.append(
                    FileSearchResult(
                        path=resolved_path,
                        matched_on="filename",
                        snippet=f"Filename matched query: {path.name}",
                    )
                )
            else:
                try:
                    text = self.reader.run(path=str(path)).text
                except OcrRequiredError:
                    stats.skipped_ocr_paths.append(resolved_path)
                    continue
                except (OSError, RuntimeError, UnsupportedFileError):
                    continue

                if lowered_query in text.lower():
                    matches.append(
                        FileSearchResult(
                            path=resolved_path,
                            matched_on="content",
                            snippet=self._extract_snippet(text=text, query=query),
                        )
                    )

            if len(matches) >= max_results:
                break

        self.last_run_stats = stats
        return sorted(matches, key=lambda item: item.path)

    def _extract_snippet(self, *, text: str, query: str, radius: int = 80) -> str:
        lowered = text.lower()
        index = lowered.find(query.lower())
        if index == -1:
            return ""

        start = max(0, index - radius)
        end = min(len(text), index + len(query) + radius)
        snippet = " ".join(text[start:end].split())
        if start > 0:
            snippet = f"...{snippet}"
        if end < len(text):
            snippet = f"{snippet}..."
        return snippet
