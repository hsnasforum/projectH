from __future__ import annotations

import unittest

from core.source_policy import build_source_policy, classify_source_type, score_source_for_mode


class SourcePolicyTest(unittest.TestCase):
    def test_classify_source_type_maps_known_domains(self) -> None:
        self.assertEqual(classify_source_type("https://namu.wiki/w/붉은사막"), "wiki")
        self.assertEqual(classify_source_type("https://store.steampowered.com/app/123"), "database")
        self.assertEqual(classify_source_type("https://news.example.com/article"), "news")
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
