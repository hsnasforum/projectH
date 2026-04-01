from __future__ import annotations

from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
import re
from urllib.parse import parse_qs, parse_qsl, quote, unquote, urlencode, urlparse, urlunsplit, urlsplit
from urllib.request import Request, urlopen


class WebSearchError(RuntimeError):
    pass


@dataclass(slots=True)
class WebSearchResult:
    title: str
    url: str
    snippet: str
    source: str = "duckduckgo"


@dataclass(slots=True)
class WebPageContent:
    url: str
    title: str
    text: str
    excerpt: str
    content_type: str
    source: str = "web_page"


class _VisibleTextHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._hidden_stack: list[str] = []
        self._title_parts: list[str] = []
        self._text_parts: list[str] = []
        self._inside_title = False

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[override]
        lowered = tag.lower()
        if lowered in {"script", "style", "noscript", "svg"}:
            self._hidden_stack.append(lowered)
            return
        if lowered == "title":
            self._inside_title = True
            return
        if self._hidden_stack:
            return
        if lowered in {"p", "div", "section", "article", "li", "ul", "ol", "br", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self._text_parts.append("\n")

    def handle_endtag(self, tag: str) -> None:  # type: ignore[override]
        lowered = tag.lower()
        if self._hidden_stack and self._hidden_stack[-1] == lowered:
            self._hidden_stack.pop()
            return
        if lowered == "title":
            self._inside_title = False
            return
        if self._hidden_stack:
            return
        if lowered in {"p", "div", "section", "article", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self._text_parts.append("\n")

    def handle_data(self, data: str) -> None:  # type: ignore[override]
        if self._inside_title:
            cleaned = data.strip()
            if cleaned:
                self._title_parts.append(cleaned)
            return
        if self._hidden_stack:
            return
        cleaned = data.strip()
        if not cleaned:
            return
        self._text_parts.append(cleaned)
        self._text_parts.append(" ")

    def handle_comment(self, data: str) -> None:  # type: ignore[override]
        return

    @property
    def text(self) -> str:
        joined = "".join(self._text_parts)
        lines = [re.sub(r"\s+", " ", line).strip() for line in joined.splitlines()]
        return "\n".join(line for line in lines if line)

    @property
    def title_text(self) -> str:
        return re.sub(r"\s+", " ", " ".join(self._title_parts)).strip()


class WebSearchTool:
    def __init__(
        self,
        *,
        base_url: str = "https://html.duckduckgo.com/html/",
        timeout_seconds: float = 10.0,
        region: str = "kr-kr",
        user_agent: str = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        max_page_chars: int = 12000,
    ) -> None:
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds
        self.region = region
        self.user_agent = user_agent
        self.max_page_chars = max_page_chars

    def search(self, *, query: str, max_results: int = 5) -> list[WebSearchResult]:
        normalized_query = " ".join(query.strip().split())
        if not normalized_query:
            raise WebSearchError("웹 검색어가 비어 있습니다.")

        params = urlencode({"q": normalized_query, "kl": self.region})
        request = Request(
            f"{self.base_url}?{params}",
            headers={
                "User-Agent": self.user_agent,
                "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.6",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8", errors="replace")
        except Exception as exc:
            raise WebSearchError(f"웹 검색 요청에 실패했습니다: {exc}") from exc

        results = self._parse_duckduckgo_results(body, max_results=max_results)
        if not results:
            raise WebSearchError("웹 검색 결과를 찾지 못했습니다.")
        return results

    def fetch_page(self, *, url: str, max_chars: int | None = None) -> WebPageContent:
        normalized_url = str(url or "").strip()
        if not normalized_url:
            raise WebSearchError("원문 페이지 URL이 비어 있습니다.")
        request_url = self._normalize_request_url(normalized_url)

        request = Request(
            request_url,
            headers={
                "User-Agent": self.user_agent,
                "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.6",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw_body = response.read()
                content_type = str(response.headers.get("Content-Type") or "text/html")
                charset = response.headers.get_content_charset() or "utf-8"
        except Exception as exc:
            raise WebSearchError(f"원문 페이지를 읽지 못했습니다: {exc}") from exc

        try:
            body = raw_body.decode(charset, errors="replace")
        except LookupError:
            body = raw_body.decode("utf-8", errors="replace")

        title, text = self._extract_page_text(body, content_type=content_type)
        text = self._refine_page_text(url=normalized_url, title=title or normalized_url, text=text)
        if not text:
            raise WebSearchError("원문 페이지에서 읽을 수 있는 본문을 찾지 못했습니다.")

        limited_text = text[: (max_chars or self.max_page_chars)].strip()
        return WebPageContent(
            url=normalized_url,
            title=title or normalized_url,
            text=limited_text,
            excerpt=self._summarize_text(limited_text, max_chars=340),
            content_type=content_type,
        )

    def _normalize_request_url(self, url: str) -> str:
        parsed = urlsplit(url)
        if not parsed.scheme or not parsed.netloc:
            return url

        normalized_path = quote(unquote(parsed.path or ""), safe="/%:@-._~!$&'()*+,;=")
        if parsed.query:
            query_pairs = parse_qsl(parsed.query, keep_blank_values=True)
            normalized_query = urlencode(query_pairs, doseq=True) if query_pairs else quote(
                unquote(parsed.query),
                safe="=&%:@-._~!$'()*+,;/?",
            )
        else:
            normalized_query = ""
        normalized_fragment = quote(unquote(parsed.fragment or ""), safe="%:@-._~!$&'()*+,;=/?")
        return urlunsplit(
            (
                parsed.scheme,
                parsed.netloc,
                normalized_path,
                normalized_query,
                normalized_fragment,
            )
        )

    def _parse_duckduckgo_results(self, html: str, *, max_results: int) -> list[WebSearchResult]:
        title_matches = re.findall(
            r'<a[^>]*class="[^"]*(?:result__a|result-link)[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            html,
            flags=re.IGNORECASE | re.DOTALL,
        )
        snippet_matches = re.findall(
            r'<(?:a|div|span)[^>]*class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</(?:a|div|span)>',
            html,
            flags=re.IGNORECASE | re.DOTALL,
        )

        results: list[WebSearchResult] = []
        for index, (href, raw_title) in enumerate(title_matches):
            title = self._clean_fragment(raw_title)
            url = self._normalize_result_url(href)
            snippet = self._clean_fragment(snippet_matches[index]) if index < len(snippet_matches) else ""
            if not title or not url:
                continue
            results.append(
                WebSearchResult(
                    title=title,
                    url=url,
                    snippet=snippet,
                )
            )
            if len(results) >= max_results:
                break
        return results

    def _normalize_result_url(self, raw_href: str) -> str:
        href = unescape(raw_href).strip()
        if not href:
            return ""
        if href.startswith("//"):
            href = f"https:{href}"
        elif href.startswith("/"):
            href = f"https://duckduckgo.com{href}"

        parsed = urlparse(href)
        if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
            target = parse_qs(parsed.query).get("uddg", [""])[0]
            return unquote(target) if target else href
        return href

    def _clean_fragment(self, raw_html: str) -> str:
        text = re.sub(r"<[^>]+>", " ", raw_html)
        text = unescape(text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _extract_page_text(self, html: str, *, content_type: str) -> tuple[str, str]:
        lowered_content_type = content_type.lower()
        if "text/plain" in lowered_content_type:
            plain_text = self._clean_plain_text(html)
            return "", plain_text

        title_match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
        title = self._clean_fragment(title_match.group(1)) if title_match else ""

        parser = _VisibleTextHtmlParser()
        parser.feed(html)
        parser.close()
        text = parser.text
        return title or parser.title_text, self._clean_plain_text(text)

    def _refine_page_text(self, *, url: str, title: str, text: str) -> str:
        normalized = self._clean_plain_text(text)
        if not normalized:
            return normalized

        hostname = urlparse(str(url or "").strip()).netloc.lower()
        lines = [line for line in normalized.splitlines() if line.strip()]
        if not lines:
            return normalized

        filtered_lines = [
            line
            for line in lines
            if not self._looks_like_domain_specific_noise(hostname=hostname, title=title, line=line)
        ]
        if filtered_lines:
            return "\n".join(filtered_lines)
        return normalized

    def _looks_like_domain_specific_noise(self, *, hostname: str, title: str, line: str) -> bool:
        normalized = " ".join(str(line or "").split()).strip()
        lowered = normalized.lower()
        if not normalized:
            return True

        if any(hostname == host or hostname.endswith(f".{host}") for host in ("namu.wiki", "wikipedia.org")):
            wiki_markers = [
                "최근 수정 시각",
                "문서 조회수",
                "역링크",
                "기여",
                "토론",
                "편집",
                "역사",
                "분류:",
                "상위 문서",
                "하위 문서",
                "이 문서는",
                "cc by-nc-sa",
                "cc-by-sa",
                "나무위키는",
                "출처 필요",
                "이 토론은",
                "문단 토론",
                "목차",
                "관련 문서",
                "같이 보기",
                "분류",
                "틀:",
                "특수:",
            ]
            if any(marker in normalized or marker in lowered for marker in wiki_markers):
                return True
            if re.fullmatch(r"(토론|편집|역사|ACL|내 문서함|도구|인접 문서)", normalized):
                return True

        news_hosts = (
            "yna.co.kr",
            "chosun.com",
            "joongang.co.kr",
            "donga.com",
            "hani.co.kr",
            "khan.co.kr",
            "mk.co.kr",
            "sedaily.com",
            "mt.co.kr",
            "sportsseoul.com",
            "sportschosun.com",
            "newsen.com",
            "xportsnews.com",
            "dispatch.co.kr",
            "news.naver.com",
            "v.daum.net",
            "news.daum.net",
            "news.nate.com",
            "news.zum.com",
            "hankyung.com",
            "edaily.co.kr",
            "etoday.co.kr",
            "heraldcorp.com",
            "zdnet.co.kr",
            "dt.co.kr",
            "seoul.co.kr",
            "newdaily.co.kr",
            "moneytoday.co.kr",
            "segye.com",
            "newsis.com",
            "mbn.co.kr",
            "sbs.co.kr",
            "kbs.co.kr",
            "ytn.co.kr",
            "jtbc.co.kr",
            "ichannela.com",
            "tvchosun.com",
            "sisajournal.com",
            # IT/전문지
            "etnews.com",
            "bloter.net",
            # 독립/시사매체
            "ohmynews.com",
            "pressian.com",
            "nocutnews.co.kr",
            "news1.kr",
            # 지역신문 (가나다순)
            "ccdailynews.com",
            "cctoday.co.kr",
            "chungnamilbo.co.kr",
            "daejeonilbo.com",
            "daejonilbo.com",
            "dynews.co.kr",
            "ggilbo.com",
            "gjdream.com",
            "gndomin.com",
            "goodmorningcc.com",
            "headlinejeju.co.kr",
            "idaebae.com",
            "idaegu.com",
            "ikbc.co.kr",
            "imaeil.com",
            "incheonilbo.com",
            "iusm.co.kr",
            "jbnews.com",
            "jejunews.com",
            "jemin.com",
            "jeonmae.co.kr",
            "jjan.kr",
            "jnilbo.com",
            "joongdo.co.kr",
            "kado.net",
            "kbsm.net",
            "kihoilbo.co.kr",
            "kookje.co.kr",
            "ksilbo.co.kr",
            "kwangju.co.kr",
            "kyeongbuk.co.kr",
            "kyeonggi.com",
            "kyeongin.com",
            "mdilbo.com",
            "sisafocus.co.kr",
            "yeongnam.com",
        )
        if any(hostname == h or hostname.endswith(f".{h}") for h in news_hosts):
            news_markers = [
                "기사입력",
                "기사 수정",
                "입력",
                "수정",
                "기자",
                "특파원",
                "무단전재",
                "재배포",
                "기사제보",
                "기사원문",
                "저작권자",
                "오탈자 신고",
                "구독",
                "메일보내기",
                "기자 페이지",
                "관련기사",
                "추천기사",
                "댓글",
                "공유",
                "스크랩",
                "기사 본문",
            ]
            if any(marker in normalized or marker in lowered for marker in news_markers):
                return True
            if re.search(r"(입력|수정)\s*\d{4}[./-]\d{1,2}[./-]\d{1,2}", normalized):
                return True
            if re.search(r"\b\d{4}[./-]\d{1,2}[./-]\d{1,2}\b.*(기자|특파원)", normalized):
                return True

        if any(
            hostname == host or hostname.endswith(f".{host}")
            for host in ("blog.naver.com", "tistory.com", "velog.io", "brunch.co.kr")
        ):
            blog_markers = [
                "본문 기타 기능",
                "이웃추가",
                "구독하기",
                "공감",
                "스크랩",
                "카테고리",
                "태그",
                "댓글",
                "프로필",
                "좋아요",
                "공유하기",
                "목록열기",
            ]
            if any(marker in normalized or marker in lowered for marker in blog_markers):
                return True

        if any(
            hostname == host or hostname.endswith(f".{host}")
            for host in ("game.naver.com", "inven.co.kr", "m.inven.co.kr", "arca.live", "ruliweb.com", "dcinside.com")
        ):
            community_markers = [
                "게시판",
                "커뮤니티",
                "길드",
                "팬아트",
                "갤러리",
                "공략",
                "직업",
                "동영상",
                "영상",
                "스크린샷",
                "랭킹",
                "db",
                "사건/사고",
                "공식 카페",
                "인벤",
                "미디어",
                "댓글",
                "추천",
                "비추천",
            ]
            if any(marker in normalized or marker in lowered for marker in community_markers):
                return True

        if any(
            hostname == host or hostname.endswith(f".{host}")
            for host in (
                "nexon.com",
                "maplestory.nexon.com",
                "pearlabyss.com",
                "playblackdesert.com",
                "epicgames.com",
                "steampowered.com",
            )
        ):
            marketing_markers = [
                "함께 이용해 보세요",
                "지금 바로",
                "자세히 보기",
                "다운로드",
                "설치",
                "구매",
                "예약",
                "쿠폰",
                "이벤트",
                "공지사항",
                "업데이트",
                "패치",
                "사전예약",
                "권장 사양",
                "최소 사양",
                "play now",
                "download",
            ]
            if any(marker in normalized or marker in lowered for marker in marketing_markers):
                return True

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
        ]
        if any(marker in normalized or marker in lowered for marker in legal_markers):
            return True

        if title and title.strip() == normalized.strip() and len(normalized) < 40:
            return True

        return False

    def _clean_plain_text(self, text: str) -> str:
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        lines = [re.sub(r"\s+", " ", line).strip() for line in normalized.splitlines()]
        return "\n".join(line for line in lines if line)

    def _summarize_text(self, text: str, *, max_chars: int = 280) -> str:
        compact = re.sub(r"\s+", " ", text).strip()
        if len(compact) <= max_chars:
            return compact
        return compact[:max_chars].rstrip() + "..."
