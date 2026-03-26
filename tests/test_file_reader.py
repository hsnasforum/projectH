import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from tools.file_reader import FileReaderTool, OcrRequiredError
from tools.file_search import FileSearchTool


class _FakePdfPage:
    def __init__(self, text: str) -> None:
        self._text = text

    def extract_text(self) -> str:
        return self._text


class _FakePdfReader:
    def __init__(self, path: str) -> None:
        self.path = path
        self.pages = [
            _FakePdfPage("First PDF page"),
            _FakePdfPage("Second PDF page"),
        ]


class _FakeEmptyPdfReader:
    def __init__(self, path: str) -> None:
        self.path = path
        self.pages = [
            _FakePdfPage(""),
            _FakePdfPage("   "),
        ]


def _build_simple_pdf_bytes(text: str) -> bytes:
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode("latin-1")
    objects = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        (
            b"3 0 obj\n"
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\n"
            b"endobj\n"
        ),
        b"4 0 obj\n<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream\nendobj\n",
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf.extend(obj)
    xref_start = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(b"trailer\n<< /Size " + str(len(objects) + 1).encode("ascii") + b" /Root 1 0 R >>\n")
    pdf.extend(b"startxref\n")
    pdf.extend(str(xref_start).encode("ascii") + b"\n%%EOF\n")
    return bytes(pdf)


class FileReaderTest(unittest.TestCase):
    def test_reads_cp949_text_file(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "korean-note.txt"
            korean_text = "\uc608\uc0b0 \uc694\uc57d \ubb38\uc11c"
            source_path.write_bytes(korean_text.encode("cp949"))

            result = FileReaderTool().run(path=str(source_path))

            self.assertEqual(result.text, korean_text)
            self.assertEqual(result.encoding_used, "cp949")
            self.assertEqual(result.content_format, "text")
            self.assertEqual(result.extraction_method, "decode")

    def test_reads_pdf_via_pypdf_when_available(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "sample.pdf"
            source_path.write_bytes(b"%PDF-1.4\n%stub pdf bytes\n")

            with patch(
                "tools.file_reader.importlib.import_module",
                return_value=SimpleNamespace(PdfReader=_FakePdfReader),
            ):
                result = FileReaderTool().run(path=str(source_path))

            self.assertEqual(result.content_format, "pdf")
            self.assertEqual(result.extraction_method, "pypdf")
            self.assertEqual(result.text, "First PDF page\n\nSecond PDF page")
            self.assertIsNone(result.encoding_used)

    def test_reads_real_pdf_file_with_installed_pypdf(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "real-sample.pdf"
            source_path.write_bytes(_build_simple_pdf_bytes("Budget summary"))

            result = FileReaderTool().run(path=str(source_path))

            self.assertEqual(result.content_format, "pdf")
            self.assertEqual(result.extraction_method, "pypdf")
            self.assertIn("Budget summary", result.text)

    def test_pdf_without_text_layer_raises_ocr_required_error(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "scan.pdf"
            source_path.write_bytes(b"%PDF-1.4\n%stub pdf bytes\n")

            with patch(
                "tools.file_reader.importlib.import_module",
                return_value=SimpleNamespace(PdfReader=_FakeEmptyPdfReader),
            ):
                with self.assertRaises(OcrRequiredError) as ctx:
                    FileReaderTool().run(path=str(source_path))

            self.assertIn("OCR", str(ctx.exception))
            self.assertIn("이미지형 PDF", str(ctx.exception))

    def test_pdf_without_dependency_raises_helpful_error(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source_path = tmp_path / "sample.pdf"
            source_path.write_bytes(b"%PDF-1.4\n%stub pdf bytes\n")

            with patch("tools.file_reader.importlib.import_module", side_effect=ModuleNotFoundError()):
                with self.assertRaises(RuntimeError) as ctx:
                    FileReaderTool().run(path=str(source_path))

            self.assertIn("pypdf", str(ctx.exception))

    def test_search_finds_cp949_text_content(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            docs_dir = tmp_path / "docs"
            docs_dir.mkdir()
            korean_query = "\uc608\uc0b0"
            korean_text = "\uc608\uc0b0 \uacc4\ud68d \uba54\ubaa8"

            (docs_dir / "english.txt").write_text("hello world", encoding="utf-8")
            (docs_dir / "budget-korean.txt").write_bytes(korean_text.encode("cp949"))

            results = FileSearchTool().run(root=str(docs_dir), query=korean_query, max_results=5)

            self.assertEqual(len(results), 1)
            self.assertIn("budget-korean.txt", results[0].path)
            self.assertEqual(results[0].matched_on, "content")
            self.assertIn(korean_text, results[0].snippet)

    def test_search_finds_pdf_text_content(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            docs_dir = tmp_path / "docs"
            docs_dir.mkdir()
            (docs_dir / "budget.pdf").write_bytes(_build_simple_pdf_bytes("Budget summary"))

            results = FileSearchTool().run(root=str(docs_dir), query="summary", max_results=5)

            self.assertEqual(len(results), 1)
            self.assertIn("budget.pdf", results[0].path)
            self.assertEqual(results[0].matched_on, "content")
            self.assertIn("Budget summary", results[0].snippet)

    def test_search_skips_scanned_pdf_without_text_layer(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            docs_dir = tmp_path / "docs"
            docs_dir.mkdir()
            (docs_dir / "scan.pdf").write_bytes(b"%PDF-1.4\n%stub pdf bytes\n")
            (docs_dir / "notes.txt").write_text("summary from text file", encoding="utf-8")

            with patch(
                "tools.file_reader.importlib.import_module",
                return_value=SimpleNamespace(PdfReader=_FakeEmptyPdfReader),
            ):
                results = FileSearchTool().run(root=str(docs_dir), query="summary", max_results=5)

            self.assertEqual(len(results), 1)
            self.assertIn("notes.txt", results[0].path)


if __name__ == "__main__":
    unittest.main()
