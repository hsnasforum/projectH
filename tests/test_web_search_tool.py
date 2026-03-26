import unittest
from unittest.mock import patch

from tools.web_search import WebSearchTool


class WebSearchToolTest(unittest.TestCase):
    def test_parse_duckduckgo_results_extracts_titles_urls_and_snippets(self) -> None:
        html = """
        <div class="result">
          <a class="result__a" href="https://example.com/wiki">체인소 맨 - 위키백과</a>
          <div class="result__snippet">체인소 맨은 일본의 다크 판타지 만화입니다.</div>
        </div>
        <div class="result">
          <a class="result__a" href="https://duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fanime">체인소맨 애니메이션</a>
          <div class="result__snippet">애니메이션과 원작 정보가 함께 정리된 페이지입니다.</div>
        </div>
        """
        tool = WebSearchTool()

        results = tool._parse_duckduckgo_results(html, max_results=5)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].title, "체인소 맨 - 위키백과")
        self.assertEqual(results[0].url, "https://example.com/wiki")
        self.assertIn("다크 판타지 만화", results[0].snippet)
        self.assertEqual(results[1].url, "https://example.com/anime")

    def test_fetch_page_extracts_visible_text(self) -> None:
        html = """
        <html>
          <head>
            <title>아이유 최신 소식</title>
            <style>.hidden { display:none; }</style>
            <script>console.log('ignore');</script>
          </head>
          <body>
            <article>
              <h1>아이유 최신 소식</h1>
              <p>아이유의 새 앨범 일정과 최근 공연 소식을 정리했습니다.</p>
              <p>팬미팅 일정과 공개된 티저 정보도 함께 확인할 수 있습니다.</p>
            </article>
          </body>
        </html>
        """.encode("utf-8")

        class _FakeHeaders:
            def get(self, key: str, default=None):
                if key.lower() == "content-type":
                    return "text/html; charset=utf-8"
                return default

            def get_content_charset(self):
                return "utf-8"

        class _FakeResponse:
            headers = _FakeHeaders()

            def read(self):
                return html

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        tool = WebSearchTool()

        with patch("tools.web_search.urlopen", return_value=_FakeResponse()):
            page = tool.fetch_page(url="https://example.com/iu-news")

        self.assertEqual(page.title, "아이유 최신 소식")
        self.assertIn("새 앨범 일정", page.text)
        self.assertNotIn("console.log", page.text)
        self.assertNotIn("display:none", page.text)

    def test_fetch_page_normalizes_non_ascii_url_path_before_request(self) -> None:
        requested_urls: list[str] = []

        class _FakeHeaders:
            def get(self, key: str, default=None):
                if key.lower() == "content-type":
                    return "text/html; charset=utf-8"
                return default

            def get_content_charset(self):
                return "utf-8"

        class _FakeResponse:
            headers = _FakeHeaders()

            def read(self):
                return "<html><body><p>본문</p></body></html>".encode("utf-8")

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        def _capture_request(request, timeout=None):
            requested_urls.append(str(getattr(request, "full_url", "")))
            return _FakeResponse()

        tool = WebSearchTool()

        with patch("tools.web_search.urlopen", side_effect=_capture_request):
            page = tool.fetch_page(url="https://ko.wikipedia.org/wiki/이재용")

        self.assertEqual(page.title, "https://ko.wikipedia.org/wiki/이재용")
        self.assertTrue(requested_urls)
        self.assertIn("%EC%9D%B4%EC%9E%AC%EC%9A%A9", requested_urls[0])

    def test_fetch_page_filters_official_game_site_cta_and_footer_noise(self) -> None:
        html = """
        <html>
          <head><title>메이플스토리</title></head>
          <body>
            <main>
              <p>메이플스토리는 넥슨이 서비스하는 온라인 액션 RPG 게임이다.</p>
              <p>지금 바로 다운로드하고 함께 이용해 보세요!</p>
              <p>대표이사 강대현 · 김정욱 / 사업자등록번호 220-87-17483 / 전화 1588-7701</p>
            </main>
          </body>
        </html>
        """.encode("utf-8")

        class _FakeHeaders:
            def get(self, key: str, default=None):
                if key.lower() == "content-type":
                    return "text/html; charset=utf-8"
                return default

            def get_content_charset(self):
                return "utf-8"

        class _FakeResponse:
            headers = _FakeHeaders()

            def read(self):
                return html

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        tool = WebSearchTool()

        with patch("tools.web_search.urlopen", return_value=_FakeResponse()):
            page = tool.fetch_page(url="https://maplestory.nexon.com/Home/Main")

        self.assertIn("메이플스토리는 넥슨이 서비스하는 온라인 액션 RPG 게임이다.", page.text)
        self.assertNotIn("함께 이용해 보세요", page.text)
        self.assertNotIn("사업자등록번호", page.text)
        self.assertNotIn("1588-7701", page.text)

    def test_fetch_page_filters_game_portal_menu_noise(self) -> None:
        html = """
        <html>
          <head><title>붉은사막 - 네이버 게임</title></head>
          <body>
            <div>게시판 길드 친구 찾기 갤러리 공식 카페 동영상 스크린샷 팬아트</div>
            <article>
              <p>붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.</p>
            </article>
          </body>
        </html>
        """.encode("utf-8")

        class _FakeHeaders:
            def get(self, key: str, default=None):
                if key.lower() == "content-type":
                    return "text/html; charset=utf-8"
                return default

            def get_content_charset(self):
                return "utf-8"

        class _FakeResponse:
            headers = _FakeHeaders()

            def read(self):
                return html

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        tool = WebSearchTool()

        with patch("tools.web_search.urlopen", return_value=_FakeResponse()):
            page = tool.fetch_page(url="https://game.naver.com/MapleStory")

        self.assertIn("붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.", page.text)
        self.assertNotIn("게시판", page.text)
        self.assertNotIn("팬아트", page.text)

    def test_fetch_page_filters_wiki_metadata_noise(self) -> None:
        html = """
        <html>
          <head><title>붉은사막 - 나무위키</title></head>
          <body>
            <div>최근 수정 시각: 2026-03-26 12:00:00</div>
            <div>역링크 토론 편집 역사 ACL</div>
            <div>분류: 펄어비스 게임</div>
            <article>
              <p>붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.</p>
            </article>
          </body>
        </html>
        """.encode("utf-8")

        class _FakeHeaders:
            def get(self, key: str, default=None):
                if key.lower() == "content-type":
                    return "text/html; charset=utf-8"
                return default

            def get_content_charset(self):
                return "utf-8"

        class _FakeResponse:
            headers = _FakeHeaders()

            def read(self):
                return html

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        tool = WebSearchTool()

        with patch("tools.web_search.urlopen", return_value=_FakeResponse()):
            page = tool.fetch_page(url="https://namu.wiki/w/%EB%B6%89%EC%9D%80%EC%82%AC%EB%A7%89")

        self.assertIn("붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임이다.", page.text)
        self.assertNotIn("최근 수정 시각", page.text)
        self.assertNotIn("역링크", page.text)
        self.assertNotIn("분류:", page.text)

    def test_fetch_page_filters_news_metadata_noise(self) -> None:
        html = """
        <html>
          <head><title>붉은사막 출시 일정</title></head>
          <body>
            <div>입력 2026.03.26 09:00 수정 2026.03.26 09:30</div>
            <div>김철수 기자</div>
            <article>
              <p>붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임으로 알려져 있다.</p>
            </article>
            <div>무단전재 및 재배포 금지</div>
          </body>
        </html>
        """.encode("utf-8")

        class _FakeHeaders:
            def get(self, key: str, default=None):
                if key.lower() == "content-type":
                    return "text/html; charset=utf-8"
                return default

            def get_content_charset(self):
                return "utf-8"

        class _FakeResponse:
            headers = _FakeHeaders()

            def read(self):
                return html

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        tool = WebSearchTool()

        with patch("tools.web_search.urlopen", return_value=_FakeResponse()):
            page = tool.fetch_page(url="https://sportsseoul.com/news/read/123456")

        self.assertIn("붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임으로 알려져 있다.", page.text)
        self.assertNotIn("입력 2026.03.26", page.text)
        self.assertNotIn("김철수 기자", page.text)
        self.assertNotIn("무단전재", page.text)

    def test_fetch_page_filters_blog_metadata_noise(self) -> None:
        html = """
        <html>
          <head><title>붉은사막 정리</title></head>
          <body>
            <div>본문 기타 기능</div>
            <div>카테고리 게임 / 태그 붉은사막</div>
            <article>
              <p>붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임으로 소개된다.</p>
            </article>
            <div>공감 댓글 공유하기</div>
          </body>
        </html>
        """.encode("utf-8")

        class _FakeHeaders:
            def get(self, key: str, default=None):
                if key.lower() == "content-type":
                    return "text/html; charset=utf-8"
                return default

            def get_content_charset(self):
                return "utf-8"

        class _FakeResponse:
            headers = _FakeHeaders()

            def read(self):
                return html

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        tool = WebSearchTool()

        with patch("tools.web_search.urlopen", return_value=_FakeResponse()):
            page = tool.fetch_page(url="https://example.tistory.com/123")

        self.assertIn("붉은사막은 펄어비스가 개발 중인 오픈월드 액션 어드벤처 게임으로 소개된다.", page.text)
        self.assertNotIn("본문 기타 기능", page.text)
        self.assertNotIn("카테고리", page.text)
        self.assertNotIn("공감", page.text)


if __name__ == "__main__":
    unittest.main()
