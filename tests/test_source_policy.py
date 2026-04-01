from __future__ import annotations

import unittest

from core.source_policy import build_source_policy, classify_source_type, score_source_for_mode


class SourcePolicyTest(unittest.TestCase):
    def test_classify_source_type_maps_known_domains(self) -> None:
        self.assertEqual(classify_source_type("https://namu.wiki/w/붉은사막"), "wiki")
        self.assertEqual(classify_source_type("https://store.steampowered.com/app/123"), "database")
        # news. 서브도메인 false-positive 제거: arbitrary news.* host는 general
        self.assertEqual(classify_source_type("https://news.example.com/article"), "general")
        # explicit domain의 news. 서브도메인은 explicit hint로 계속 news
        self.assertEqual(classify_source_type("https://news.sbs.co.kr/news/endPage.do?news_id=N1001"), "news")
        # news.naver.com은 news로 복구 (community naver.com 예외)
        self.assertEqual(classify_source_type("https://news.naver.com/main/read.naver?oid=001&aid=0000001"), "news")
        # blog.naver.com은 여전히 community
        self.assertEqual(classify_source_type("https://blog.naver.com/example/1"), "community")
        # v.daum.net은 news로 복구 (community daum.net 예외)
        self.assertEqual(classify_source_type("https://v.daum.net/v/20260401120000001"), "news")
        # news.daum.net은 news로 복구 (community daum.net 예외)
        self.assertEqual(classify_source_type("https://news.daum.net/v/20260401120000001"), "news")
        # cafe.daum.net은 여전히 community
        self.assertEqual(classify_source_type("https://cafe.daum.net/example/1"), "community")
        # news.nate.com은 news로 복구
        self.assertEqual(classify_source_type("https://news.nate.com/view/20260401n00123"), "news")
        # news.zum.com은 news로 복구
        self.assertEqual(classify_source_type("https://news.zum.com/articles/97600001"), "news")
        # portal news host의 실제 하위 서브도메인도 news 유지
        self.assertEqual(classify_source_type("https://m.news.nate.com/view/20260401n00123"), "news")
        self.assertEqual(classify_source_type("https://m.news.zum.com/articles/97600001"), "news")
        # portal news host boundary: suffix-like 가짜 host는 news로 오인되면 안 됨
        self.assertEqual(classify_source_type("https://notnews.nate.com/view/1"), "general")
        self.assertEqual(classify_source_type("https://notnews.zum.com/articles/1"), "general")
        # dotted news host boundary: exact-or-subdomain만 news
        self.assertEqual(classify_source_type("https://m.yna.co.kr/view/AKR20260401"), "news")
        self.assertEqual(classify_source_type("https://m.mk.co.kr/economy/2025"), "news")
        self.assertEqual(classify_source_type("https://foo-yna.co.kr/article/1"), "general")
        self.assertEqual(classify_source_type("https://notmk.co.kr/article/1"), "general")
        # fragment hint → explicit domain boundary
        self.assertEqual(classify_source_type("https://www.chosun.com/economy/2025"), "news")
        self.assertEqual(classify_source_type("https://www.joongang.co.kr/article/1"), "news")
        self.assertEqual(classify_source_type("https://www.donga.com/news/article/1"), "news")
        self.assertEqual(classify_source_type("https://mychosun.com/article/1"), "general")
        self.assertEqual(classify_source_type("https://fakejoongang.example/article/1"), "general")
        self.assertEqual(classify_source_type("https://notdonga.example/article/1"), "general")
        self.assertEqual(classify_source_type("https://www.hankyung.com/economy/2025"), "news")
        self.assertEqual(classify_source_type("https://www.edaily.co.kr/news/2025"), "news")
        self.assertEqual(classify_source_type("https://www.etoday.co.kr/news/2025"), "news")
        self.assertEqual(classify_source_type("https://news.heraldcorp.com/view/2025"), "news")
        self.assertEqual(classify_source_type("https://zdnet.co.kr/view/2025"), "news")
        self.assertEqual(classify_source_type("https://www.dt.co.kr/contents/2025"), "news")
        self.assertEqual(classify_source_type("https://www.seoul.co.kr/news/2025"), "news")
        self.assertEqual(classify_source_type("https://biz.newdaily.co.kr/news/2025"), "news")
        self.assertEqual(classify_source_type("https://www.moneytoday.co.kr/news/2025"), "news")
        self.assertEqual(classify_source_type("https://www.segye.com/newsView/202603310001"), "news")
        self.assertEqual(classify_source_type("https://www.sisajournal.com/news/articleView.html?idxno=123456"), "news")
        self.assertEqual(classify_source_type("https://www.kyeonggi.com/article/202603310001"), "news")
        self.assertEqual(classify_source_type("https://www.sisafocus.co.kr/news/articleView.html?idxno=123456"), "news")
        self.assertEqual(classify_source_type("https://www.ikbc.co.kr/article/view/kbc202603310001"), "news")
        self.assertEqual(classify_source_type("https://www.kado.net/news/articleView.html?idxno=123456"), "news")
        self.assertEqual(classify_source_type("https://www.ggilbo.com/news/articleView.html?idxno=1032100"), "news")
        self.assertEqual(classify_source_type("https://www.idaegu.com/news/articleView.html?idxno=123456"), "news")
        self.assertEqual(classify_source_type("https://www.kyeongin.com/article/1735821"), "news")
        self.assertEqual(classify_source_type("https://www.yeongnam.com/web/view.php?key=202603310001"), "news")
        self.assertEqual(classify_source_type("https://www.jemin.com/news/articleView.html?idxno=775221"), "news")
        self.assertEqual(classify_source_type("https://www.jeonmae.co.kr/news/articleView.html?idxno=1020304"), "news")
        self.assertEqual(classify_source_type("https://www.gndomin.com/news/articleView.html?idxno=123456"), "news")
        self.assertEqual(classify_source_type("https://www.kwangju.co.kr/article.php?aid=1711111111111"), "news")
        self.assertEqual(classify_source_type("https://www.ksilbo.co.kr/news/articleView.html?idxno=123456"), "news")
        self.assertEqual(classify_source_type("https://www.imaeil.com/page/view/2026033112000000000"), "news")
        self.assertEqual(classify_source_type("https://www.kookje.co.kr/news2011/asp/newsbody.asp?code=0300&key=20260331.99099009999"), "news")
        self.assertEqual(classify_source_type("https://www.jnilbo.com/76543212345"), "news")
        self.assertEqual(classify_source_type("https://www.jjan.kr/article/20260331500001"), "news")
        self.assertEqual(classify_source_type("https://www.iusm.co.kr/news/articleView.html?idxno=987654"), "news")
        self.assertEqual(classify_source_type("https://www.mdilbo.com/detail/c3QycN/740000"), "news")
        self.assertEqual(classify_source_type("https://www.idaebae.com/news/articleView.html?idxno=123456"), "news")
        self.assertEqual(classify_source_type("https://www.kbsm.net/news/articleView.html?idxno=123456"), "news")
        self.assertEqual(classify_source_type("https://www.incheonilbo.com/news/articleView.html?idxno=123456"), "news")
        self.assertEqual(classify_source_type("https://www.daejonilbo.com/news/articleView.html?idxno=123456"), "news")
        self.assertEqual(classify_source_type("https://www.kihoilbo.co.kr/news/articleView.html?idxno=123456"), "news")
        self.assertEqual(classify_source_type("https://www.kyeongbuk.co.kr/news/articleView.html?idxno=123456"), "news")
        self.assertEqual(classify_source_type("https://www.goodmorningcc.com/news/articleView.html?idxno=123456"), "news")
        self.assertEqual(classify_source_type("https://www.cctoday.co.kr/news/articleView.html?idxno=123456"), "news")
        self.assertEqual(classify_source_type("https://www.chungnamilbo.co.kr/news/articleView.html?idxno=123456"), "news")
        self.assertEqual(classify_source_type("https://www.daejeonilbo.com/news/articleView.html?idxno=123456"), "news")
        self.assertEqual(classify_source_type("https://www.joongdo.co.kr/web/view.php?key=20260401010000123"), "news")
        self.assertEqual(classify_source_type("https://www.dynews.co.kr/news/articleView.html?idxno=123456"), "news")
        self.assertEqual(classify_source_type("https://www.ccdailynews.com/news/articleView.html?idxno=123456"), "news")
        self.assertEqual(classify_source_type("https://www.jbnews.com/news/articleView.html?idxno=123456"), "news")
        self.assertEqual(classify_source_type("https://www.gjdream.com/news/articleView.html?idxno=123456"), "news")
        self.assertEqual(classify_source_type("https://www.jejunews.com/news/articleView.html?idxno=123456"), "news")
        self.assertEqual(classify_source_type("https://www.headlinejeju.co.kr/news/articleView.html?idxno=123456"), "news")
        self.assertEqual(classify_source_type("https://www.ohmynews.com/NWS_Web/View/at_pg.aspx?CNTN_CD=A0001"), "news")
        self.assertEqual(classify_source_type("https://www.pressian.com/pages/articles/2026040100001"), "news")
        self.assertEqual(classify_source_type("https://www.nocutnews.co.kr/news/6100001"), "news")
        self.assertEqual(classify_source_type("https://www.newsis.com/view/NISX20260401_0001"), "news")
        self.assertEqual(classify_source_type("https://www.news1.kr/articles/?5000001"), "news")
        self.assertEqual(classify_source_type("https://www.mbn.co.kr/news/economy/5000001"), "news")
        self.assertEqual(classify_source_type("https://news.sbs.co.kr/news/endPage.do?news_id=N1001"), "news")
        self.assertEqual(classify_source_type("https://news.kbs.co.kr/news/pc/view/view.do?ncd=8000001"), "news")
        self.assertEqual(classify_source_type("https://www.ytn.co.kr/_ln/0102_202604010001"), "news")
        self.assertEqual(classify_source_type("https://news.jtbc.co.kr/article/article.aspx?news_id=NB12100001"), "news")
        self.assertEqual(classify_source_type("https://www.ichannela.com/news/main/news_detail.do?publishId=000000001"), "news")
        self.assertEqual(classify_source_type("https://news.tvchosun.com/site/data/html_dir/2026/04/01/2026040100001.html"), "news")
        self.assertEqual(classify_source_type("https://www.etnews.com/20260401000001"), "news")
        self.assertEqual(classify_source_type("https://www.bloter.net/news/articleView.html?idxno=123456"), "news")
        # false-positive regression: "news" substring이 arbitrary host를 news로 오인하면 안 됨
        self.assertEqual(classify_source_type("https://www.unknownlocalnews.kr/article/1"), "general")
        self.assertEqual(classify_source_type("https://fakenews.co.kr/article/1"), "general")
        self.assertEqual(classify_source_type("https://mynewssite.com/article/1"), "general")
        self.assertEqual(classify_source_type("https://www.inven.co.kr/webzine/news/?news=1"), "community")

    def test_entity_card_prefers_wiki_over_news(self) -> None:
        wiki_policy = build_source_policy(
            url="https://namu.wiki/w/붉은사막",
            descriptive_source=True,
            official_domain=False,
            opinion_or_blog=False,
            event_or_campaign=False,
            operational_noise=False,
            community_domain=False,
        )
        news_policy = build_source_policy(
            url="https://www.yna.co.kr/view/AKR20260326000100017",
            descriptive_source=True,
            official_domain=False,
            opinion_or_blog=False,
            event_or_campaign=False,
            operational_noise=False,
            community_domain=False,
        )

        self.assertGreater(
            score_source_for_mode(wiki_policy, answer_mode="entity_card"),
            score_source_for_mode(news_policy, answer_mode="entity_card"),
        )

    def test_latest_update_prefers_official_and_news_over_wiki(self) -> None:
        official_policy = build_source_policy(
            url="https://maplestory.nexon.com/News/Update",
            descriptive_source=True,
            official_domain=True,
            opinion_or_blog=False,
            event_or_campaign=False,
            operational_noise=False,
            community_domain=False,
        )
        news_policy = build_source_policy(
            url="https://www.yna.co.kr/view/AKR20260326000100017",
            descriptive_source=True,
            official_domain=False,
            opinion_or_blog=False,
            event_or_campaign=False,
            operational_noise=False,
            community_domain=False,
        )
        wiki_policy = build_source_policy(
            url="https://namu.wiki/w/메이플스토리",
            descriptive_source=True,
            official_domain=False,
            opinion_or_blog=False,
            event_or_campaign=False,
            operational_noise=False,
            community_domain=False,
        )

        self.assertGreater(
            score_source_for_mode(official_policy, answer_mode="latest_update", freshness_risk="high"),
            score_source_for_mode(wiki_policy, answer_mode="latest_update", freshness_risk="high"),
        )
        self.assertGreater(
            score_source_for_mode(news_policy, answer_mode="latest_update", freshness_risk="high"),
            score_source_for_mode(wiki_policy, answer_mode="latest_update", freshness_risk="high"),
        )


if __name__ == "__main__":
    unittest.main()
