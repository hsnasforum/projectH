import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
README_PATH = REPO_ROOT / "README.md"
ACCEPTANCE_PATH = REPO_ROOT / "docs" / "ACCEPTANCE_CRITERIA.md"
MILESTONES_PATH = REPO_ROOT / "docs" / "MILESTONES.md"
NEXT_STEPS_PATH = REPO_ROOT / "docs" / "NEXT_STEPS.md"
TASK_BACKLOG_PATH = REPO_ROOT / "docs" / "TASK_BACKLOG.md"

ROOT_DOC_PATHS: tuple[Path, ...] = (
    README_PATH,
    ACCEPTANCE_PATH,
    MILESTONES_PATH,
    NEXT_STEPS_PATH,
    TASK_BACKLOG_PATH,
)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_inventory_count(text: str, pattern: re.Pattern[str], *, source: str) -> int:
    matches = pattern.findall(text)
    if not matches:
        raise AssertionError(
            f"{source}: could not locate a `<N> core browser scenarios` inventory header"
        )
    if len(matches) > 1:
        raise AssertionError(
            f"{source}: expected exactly one inventory header, found {len(matches)}: {matches}"
        )
    return int(matches[0])


_MARKDOWN_ITEM_START_PATTERN = re.compile(r"^\s*(?:\d+\.|[-*+])\s")
_MARKDOWN_HEADING_PATTERN = re.compile(r"^#+\s")
_FENCED_CODE_PATTERN = re.compile(r"^(`{3,}|~{3,})")
_BLOCK_QUOTE_PATTERN = re.compile(r"^>\s?")
_HTML_BLOCK_PATTERN = re.compile(
    r"^\s*</?(?:div|table|thead|tbody|tr|th|td|pre|blockquote|details|summary"
    r"|section|article|nav|aside|header|footer|main|figure|figcaption"
    r"|ol|ul|li|dl|dt|dd|p|hr|br)[\s>/]",
    re.IGNORECASE,
)


def _split_into_markdown_items(text: str) -> list[tuple[int, str]]:
    """Split `text` into lightweight markdown items for pair matching.

    An item is a numbered list item, a bullet list item, a heading, a
    block quote run, or a standalone prose paragraph. Item boundaries
    open when:
    - a numbered list marker (`\\s*\\d+\\.\\s`) starts a line
    - a bullet list marker (`\\s*[-*+]\\s`) starts a line
    - a heading (`#+\\s`) starts a line (heading becomes its own item and
      does not absorb the following list/prose item)
    - a block quote marker (`>`) starts a line — the consecutive run of
      ``>``-prefixed lines becomes one item so a block quote does not
      silently merge into a surrounding prose paragraph
    - a block-level HTML tag starts a line — prevents two distinct pair
      mentions from collapsing into one over-broad item
    - a non-empty line follows a blank line without a marker (new prose
      paragraph)

    Fenced code blocks (delimited by ``` or ~~~) are collected as a
    single opaque item so markers inside code do not create false
    matches.

    Continuation lines that do not start with a marker append to the
    current item so wrapped content is still covered. Blank lines close
    the current item. The returned tuples are `(start_line_number,
    joined_item_text)` with 1-based line numbers, and the joined item
    text preserves physical newlines so substring matching can still see
    the full item content.

    This matcher is intentionally lightweight and stable-fragment based;
    it does not aim to be a faithful CommonMark parser.
    """
    items: list[tuple[int, str]] = []
    current_start: int | None = None
    current_lines: list[str] = []

    # Fenced code block state.
    in_fence: bool = False
    fence_marker: str = ""

    def _flush() -> None:
        nonlocal current_start, current_lines
        if current_lines:
            assert current_start is not None
            items.append((current_start, "\n".join(current_lines)))
        current_start = None
        current_lines = []

    for index, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()

        # --- fenced code block handling ---
        fence_match = _FENCED_CODE_PATTERN.match(stripped)
        if fence_match:
            marker = fence_match.group(1)[0]  # '`' or '~'
            min_len = len(fence_match.group(1))
            if in_fence:
                # Closing fence: same char, at least as many repetitions.
                if marker == fence_marker[0] and len(fence_match.group(1)) >= len(fence_marker):
                    current_lines.append(line)
                    in_fence = False
                    fence_marker = ""
                    _flush()
                    continue
                # Not a valid close — just content inside the fence.
                current_lines.append(line)
                continue
            else:
                # Opening fence — start a new opaque item.
                _flush()
                in_fence = True
                fence_marker = fence_match.group(1)
                current_start = index
                current_lines.append(line)
                continue

        if in_fence:
            # All lines inside the fence belong to the same opaque item.
            current_lines.append(line)
            continue

        # --- normal markdown handling ---
        if stripped == "":
            _flush()
            continue
        if _MARKDOWN_HEADING_PATTERN.match(line):
            _flush()
            items.append((index, line))
            continue
        if _MARKDOWN_ITEM_START_PATTERN.match(line):
            _flush()
            current_start = index
            current_lines.append(line)
            continue
        if _BLOCK_QUOTE_PATTERN.match(line):
            # Consecutive block-quote lines stay in the same item; a
            # block-quote line after non-quote content opens a new item.
            if current_lines and not _BLOCK_QUOTE_PATTERN.match(current_lines[-1]):
                _flush()
            if current_start is None:
                current_start = index
            current_lines.append(line)
            continue
        if _HTML_BLOCK_PATTERN.match(line):
            _flush()
            current_start = index
            current_lines.append(line)
            continue
        # If current item is a block-quote run, a non-quote line ends it.
        if current_lines and _BLOCK_QUOTE_PATTERN.match(current_lines[-1]):
            _flush()
        # Continuation or new prose paragraph.
        if current_start is None:
            current_start = index
        current_lines.append(line)

    # Flush remaining (including unclosed fences — treat as one item).
    _flush()
    return items


def _extract_readme_max_smoke_scenario_number() -> int:
    text = _read_text(README_PATH)
    lines = text.splitlines()

    start_index: int | None = None
    for index, line in enumerate(lines):
        if line.strip() == "Current smoke scenarios:":
            start_index = index + 1
            break
    if start_index is None:
        raise AssertionError(
            "README.md: could not find `Current smoke scenarios:` marker"
        )

    end_index = len(lines)
    for index in range(start_index, len(lines)):
        stripped = lines[index].strip()
        if stripped.startswith("## "):
            end_index = index
            break

    item_pattern = re.compile(r"^(\d+)\.\s")
    numbers: list[int] = []
    for line in lines[start_index:end_index]:
        match = item_pattern.match(line)
        if match:
            numbers.append(int(match.group(1)))

    if not numbers:
        raise AssertionError(
            "README.md: `Current smoke scenarios:` section has no numbered items"
        )
    return max(numbers)


class BrowserSmokeInventoryDocsParityTest(unittest.TestCase):
    """Guard the browser smoke inventory count and reference shape across root docs.

    Why: repeated same-day truth-sync loops landed because root docs drifted apart
    on the smoke inventory count and on a brittle `docs/ACCEPTANCE_CRITERIA.md:<line>`
    anchor. This regression catches the next mismatch before another docs-only
    round starts.
    """

    ACCEPTANCE_PATTERN = re.compile(
        r"Playwright smoke covers (\d+) core browser scenarios"
    )
    NEXT_STEPS_PATTERN = re.compile(
        r"Playwright smoke currently covers (\d+) core browser scenarios"
    )
    ACCEPTANCE_LINE_ANCHOR_PATTERN = re.compile(
        r"docs/ACCEPTANCE_CRITERIA\.md:\d+"
    )

    def test_acceptance_and_next_steps_inventory_counts_match(self) -> None:
        acceptance_count = _extract_inventory_count(
            _read_text(ACCEPTANCE_PATH),
            self.ACCEPTANCE_PATTERN,
            source="docs/ACCEPTANCE_CRITERIA.md",
        )
        next_steps_count = _extract_inventory_count(
            _read_text(NEXT_STEPS_PATH),
            self.NEXT_STEPS_PATTERN,
            source="docs/NEXT_STEPS.md",
        )
        self.assertEqual(
            acceptance_count,
            next_steps_count,
            (
                "docs/ACCEPTANCE_CRITERIA.md inventory count "
                f"({acceptance_count}) and docs/NEXT_STEPS.md inventory count "
                f"({next_steps_count}) must match. Update both together when the "
                "browser smoke inventory changes."
            ),
        )

    def test_readme_numbered_smoke_list_closes_at_inventory_count(self) -> None:
        acceptance_count = _extract_inventory_count(
            _read_text(ACCEPTANCE_PATH),
            self.ACCEPTANCE_PATTERN,
            source="docs/ACCEPTANCE_CRITERIA.md",
        )
        readme_max = _extract_readme_max_smoke_scenario_number()
        self.assertEqual(
            readme_max,
            acceptance_count,
            (
                "README.md `Current smoke scenarios:` numbered list closes at "
                f"{readme_max}, but docs/ACCEPTANCE_CRITERIA.md inventory count "
                f"is {acceptance_count}. Update both together when the browser "
                "smoke inventory changes."
            ),
        )

    def test_next_steps_does_not_hard_code_acceptance_line_anchor(self) -> None:
        text = _read_text(NEXT_STEPS_PATH)
        match = self.ACCEPTANCE_LINE_ANCHOR_PATTERN.search(text)
        self.assertIsNone(
            match,
            (
                "docs/NEXT_STEPS.md must not hard-code a "
                "`docs/ACCEPTANCE_CRITERIA.md:<line>` anchor for the browser "
                "smoke inventory reference. Prefer a stable section anchor "
                "(for example, `### Current Gates` bullet under `## Test Gates` "
                "in `docs/ACCEPTANCE_CRITERIA.md`). Found: "
                f"{match.group(0) if match else ''}"
            ),
        )


class ClickReloadComposerPlainFollowUpRootDocPairTest(unittest.TestCase):
    """Guard the shipped click-reload composer plain-follow-up pair across root docs.

    Why: the shipped browser smoke now covers a click-reload followed by a
    composer plain follow-up that omits `load_web_search_record_id` for both
    entity-card and latest-update records. Repeated same-day loops have shown
    that a new browser pair can silently drop out of one or more root docs
    while remaining in others, or get duplicated after copy/paste or merge
    drift. This regression locks the minimum stable fragment set for each
    doc so any drop-out or duplicate fails loudly before another docs-only
    round starts. The scan unit is a lightweight markdown item (numbered
    list item, bullet list item, heading, block quote run, or standalone
    prose paragraph), not a raw blank-line paragraph block, so adjacent
    list items keep separate pair boundaries and duplicates inside one
    over-broad block cannot hide as a single blank-line paragraph match.
    Fenced code blocks are treated as single opaque items so markers
    inside code do not create false matches. Block quotes and block-level
    HTML tags open new item boundaries so they do not silently merge into
    surrounding prose. Wrapped continuation lines inside the same item
    are still covered.
    """

    ENTITY_FRAGMENTS: tuple[str, ...] = (
        "history-card entity-card",
        "plain follow-up",
        "load_web_search_record_id",
        "#claim-coverage-box",
        "visible",
    )
    LATEST_UPDATE_FRAGMENTS: tuple[str, ...] = (
        "history-card latest-update",
        "plain follow-up",
        "load_web_search_record_id",
        "#claim-coverage-box",
        "hidden",
    )

    @staticmethod
    def _item_contains_all(item_text: str, fragments: tuple[str, ...]) -> bool:
        lowered = item_text.lower()
        return all(fragment.lower() in lowered for fragment in fragments)

    def _count_pair_matches(
        self,
        doc_path: Path,
        *,
        fragments: tuple[str, ...],
    ) -> list[tuple[int, str]]:
        text = _read_text(doc_path)
        matches: list[tuple[int, str]] = []
        for start_line, item_text in _split_into_markdown_items(text):
            if self._item_contains_all(item_text, fragments):
                matches.append((start_line, item_text))
        return matches

    def _assert_pair_unique(
        self,
        doc_path: Path,
        *,
        fragments: tuple[str, ...],
        pair_label: str,
    ) -> None:
        matches = self._count_pair_matches(doc_path, fragments=fragments)
        relative_path = doc_path.relative_to(REPO_ROOT)
        if len(matches) == 1:
            return
        if not matches:
            self.fail(
                f"{relative_path}: could not find a markdown item covering "
                f"the {pair_label} click-reload composer plain-follow-up pair. "
                f"Expected exactly one markdown item (numbered list item, "
                f"bullet list item, heading, or standalone prose paragraph) "
                f"to contain all of: {list(fragments)}. "
                "Keep the click-reload composer plain-follow-up pair in every "
                "required root doc (README.md, docs/ACCEPTANCE_CRITERIA.md, "
                "docs/MILESTONES.md, docs/NEXT_STEPS.md, docs/TASK_BACKLOG.md)."
            )
        duplicate_summary = ", ".join(
            f"item starting at line {start_line}" for start_line, _ in matches
        )
        self.fail(
            f"{relative_path}: found {len(matches)} markdown items matching "
            f"the {pair_label} click-reload composer plain-follow-up pair "
            f"({duplicate_summary}), but expected exactly one. Remove the "
            "duplicate so copy/paste or merge drift does not leave two "
            "entries for the same pair in one root doc."
        )

    def test_entity_card_pair_unique_in_all_root_docs(self) -> None:
        for doc_path in ROOT_DOC_PATHS:
            with self.subTest(doc=str(doc_path.relative_to(REPO_ROOT))):
                self._assert_pair_unique(
                    doc_path,
                    fragments=self.ENTITY_FRAGMENTS,
                    pair_label="entity-card",
                )

    def test_latest_update_pair_unique_in_all_root_docs(self) -> None:
        for doc_path in ROOT_DOC_PATHS:
            with self.subTest(doc=str(doc_path.relative_to(REPO_ROOT))):
                self._assert_pair_unique(
                    doc_path,
                    fragments=self.LATEST_UPDATE_FRAGMENTS,
                    pair_label="latest-update",
                )


class MarkdownItemSplitterDirectTest(unittest.TestCase):
    """Direct coverage for _split_into_markdown_items container-edge branches.

    Why: the fenced-code, block-quote, and HTML-tag branches were added to
    prevent false matches in the pair uniqueness guard, but the current 5
    root docs do not contain those structures. Without direct tests the
    branches could regress silently. Each test targets one branch with a
    small synthetic document.
    """

    @staticmethod
    def _texts(items: list[tuple[int, str]]) -> list[str]:
        return [text for _, text in items]

    # -- fenced code block ------------------------------------------------

    def test_fenced_code_block_is_one_opaque_item(self) -> None:
        doc = (
            "prose before\n"
            "\n"
            "```python\n"
            "# heading inside fence\n"
            "- bullet inside fence\n"
            "1. numbered inside fence\n"
            "```\n"
            "\n"
            "prose after\n"
        )
        items = _split_into_markdown_items(doc)
        texts = self._texts(items)
        self.assertEqual(len(items), 3, f"expected 3 items, got {len(items)}: {texts}")
        self.assertEqual(texts[0], "prose before")
        self.assertIn("# heading inside fence", texts[1])
        self.assertIn("- bullet inside fence", texts[1])
        self.assertIn("1. numbered inside fence", texts[1])
        self.assertEqual(texts[2], "prose after")

    def test_tilde_fence_with_inner_backticks(self) -> None:
        doc = (
            "~~~\n"
            "```\n"
            "still inside\n"
            "~~~\n"
        )
        items = _split_into_markdown_items(doc)
        self.assertEqual(len(items), 1, f"expected 1 item, got {len(items)}")
        self.assertIn("```", items[0][1])
        self.assertIn("still inside", items[0][1])

    def test_longer_fence_not_closed_by_shorter(self) -> None:
        doc = (
            "````\n"
            "```\n"
            "content\n"
            "````\n"
            "outside\n"
        )
        items = _split_into_markdown_items(doc)
        texts = self._texts(items)
        self.assertEqual(len(items), 2, f"expected 2 items, got {len(items)}: {texts}")
        fence_item = texts[0]
        self.assertIn("```", fence_item)
        self.assertIn("content", fence_item)
        self.assertEqual(texts[1], "outside")

    def test_unclosed_fence_becomes_single_item(self) -> None:
        doc = (
            "```\n"
            "- bullet inside\n"
            "# heading inside\n"
        )
        items = _split_into_markdown_items(doc)
        self.assertEqual(len(items), 1)
        self.assertIn("- bullet inside", items[0][1])
        self.assertIn("# heading inside", items[0][1])

    # -- block quote ------------------------------------------------------

    def test_block_quote_splits_from_surrounding_prose(self) -> None:
        doc = (
            "prose before\n"
            "> quote line one\n"
            "> quote line two\n"
            "prose after\n"
        )
        items = _split_into_markdown_items(doc)
        texts = self._texts(items)
        self.assertEqual(len(items), 3, f"expected 3 items, got {len(items)}: {texts}")
        self.assertEqual(texts[0], "prose before")
        self.assertIn("> quote line one", texts[1])
        self.assertIn("> quote line two", texts[1])
        self.assertEqual(texts[2], "prose after")

    def test_consecutive_block_quote_lines_stay_together(self) -> None:
        doc = (
            "> line A\n"
            "> line B\n"
            "> line C\n"
        )
        items = _split_into_markdown_items(doc)
        self.assertEqual(len(items), 1)
        self.assertIn("> line A", items[0][1])
        self.assertIn("> line C", items[0][1])

    # -- HTML block tag ---------------------------------------------------

    def test_html_block_tag_opens_new_boundary(self) -> None:
        doc = (
            "- item one\n"
            "<div>\n"
            "- item two\n"
            "</div>\n"
        )
        items = _split_into_markdown_items(doc)
        texts = self._texts(items)
        self.assertGreaterEqual(len(items), 3,
                                f"expected >=3 items, got {len(items)}: {texts}")
        # item one and item two must be in separate items
        item_one_idx = next(i for i, t in enumerate(texts) if "item one" in t)
        item_two_idx = next(i for i, t in enumerate(texts) if "item two" in t)
        self.assertNotEqual(item_one_idx, item_two_idx,
                            "HTML tag should prevent merging two list items")

    def test_html_closing_tag_opens_boundary(self) -> None:
        doc = (
            "<details>\n"
            "inner content\n"
            "</details>\n"
        )
        items = _split_into_markdown_items(doc)
        texts = self._texts(items)
        # <details> and </details> each open a boundary
        self.assertGreaterEqual(len(items), 2,
                                f"expected >=2 items, got {len(items)}: {texts}")


if __name__ == "__main__":
    unittest.main()
