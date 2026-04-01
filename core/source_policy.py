from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlparse


SourceType = Literal["official", "database", "news", "wiki", "community", "general"]
AnswerMode = Literal["general", "entity_card", "latest_update"]
FreshnessRisk = Literal["low", "high"]


@dataclass(frozen=True, slots=True)
class SourcePolicyDecision:
    source_type: SourceType
    role_label: str
    entity_score: int
    latest_score: int
    general_score: int


def classify_source_type(url: str) -> SourceType:
    hostname = urlparse(str(url or "").strip()).netloc.lower()
    if not hostname:
        return "general"
    if any(
        hostname == host or hostname.endswith(f".{host}")
        for host in ("namu.wiki", "wikipedia.org", "encykorea.aks.ac.kr", "britannica.com")
    ):
        return "wiki"
    if any(
        hostname == host or hostname.endswith(f".{host}")
        for host in (
            "store.steampowered.com",
            "play.google.com",
            "apps.apple.com",
            "fandom.com",
            "imdb.com",
            "thetvdb.com",
        )
    ):
        return "database"
    news_domain_hosts = (
        "chosun.com",
        "joongang.co.kr",
        "donga.com",
        "yna.co.kr",
        "dt.co.kr",
        "edaily.co.kr",
        "etoday.co.kr",
        "hani.co.kr",
        "hankyung.com",
        "heraldcorp.com",
        "khan.co.kr",
        "mk.co.kr",
        "moneytoday.co.kr",
        "newdaily.co.kr",
        "sedaily.com",
        "seoul.co.kr",
        "mt.co.kr",
        "sportsseoul.com",
        "sportschosun.com",
        "newsen.com",
        "xportsnews.com",
        "zdnet.co.kr",
        "dispatch.co.kr",
        "segye.com",
        "sisajournal.com",
        "kyeonggi.com",
        "sisafocus.co.kr",
        "ikbc.co.kr",
        "kado.net",
        "ggilbo.com",
        "idaegu.com",
        "kyeongin.com",
        "yeongnam.com",
        "jemin.com",
        "jeonmae.co.kr",
        "gndomin.com",
        "kwangju.co.kr",
        "ksilbo.co.kr",
        "imaeil.com",
        "kookje.co.kr",
        "jnilbo.com",
        "jjan.kr",
        "iusm.co.kr",
        "mdilbo.com",
        "idaebae.com",
        "kbsm.net",
        "incheonilbo.com",
        "daejonilbo.com",
        "kihoilbo.co.kr",
        "kyeongbuk.co.kr",
        "goodmorningcc.com",
        "cctoday.co.kr",
        "chungnamilbo.co.kr",
        "daejeonilbo.com",
        "joongdo.co.kr",
        "dynews.co.kr",
        "ccdailynews.com",
        "jbnews.com",
        "gjdream.com",
        "jejunews.com",
        "headlinejeju.co.kr",
        "ohmynews.com",
        "pressian.com",
        "nocutnews.co.kr",
        "newsis.com",
        "news1.kr",
        "mbn.co.kr",
        "sbs.co.kr",
        "kbs.co.kr",
        "ytn.co.kr",
        "jtbc.co.kr",
        "ichannela.com",
        "tvchosun.com",
        "etnews.com",
        "bloter.net",
        "news.naver.com",
        "v.daum.net",
        "news.daum.net",
        "news.nate.com",
        "news.zum.com",
    )
    if any(
        hostname == host or hostname.endswith(f".{host}")
        for host in news_domain_hosts
    ):
        return "news"
    community_hosts = (
        "naver.com",
        "daum.net",
        "inven.co.kr",
        "arca.live",
        "ruliweb.com",
        "dcinside.com",
        "thisisgame.com",
        "youtube.com",
        "youtu.be",
        "instagram.com",
        "facebook.com",
        "x.com",
        "twitter.com",
        "tiktok.com",
        "tistory.com",
        "blog.naver.com",
        "velog.io",
        "brunch.co.kr",
        "medium.com",
    )
    if any(hostname == host or hostname.endswith(f".{host}") for host in community_hosts):
        return "community"
    return "general"


def build_source_policy(
    *,
    url: str,
    descriptive_source: bool,
    official_domain: bool,
    opinion_or_blog: bool,
    event_or_campaign: bool,
    operational_noise: bool,
    community_domain: bool,
) -> SourcePolicyDecision:
    source_type = "official" if official_domain else classify_source_type(url)

    if source_type == "wiki":
        role_label = "백과 기반"
        entity_score = 12
        latest_score = 2
        general_score = 5
    elif source_type == "official":
        role_label = "공식 기반"
        entity_score = 10 if descriptive_source else 6
        latest_score = 11
        general_score = 7
    elif source_type == "database":
        role_label = "데이터 기반"
        entity_score = 9
        latest_score = 6
        general_score = 6
    elif source_type == "news":
        role_label = "보조 기사"
        entity_score = 1
        latest_score = 9
        general_score = 4
    elif source_type == "community":
        role_label = "보조 커뮤니티"
        entity_score = -5
        latest_score = -3
        general_score = -2
    else:
        role_label = "설명형 출처" if descriptive_source else "보조 출처"
        entity_score = 7 if descriptive_source else 4
        latest_score = 4 if descriptive_source else 2
        general_score = 4 if descriptive_source else 2

    if opinion_or_blog:
        entity_score -= 6
        latest_score -= 4
        general_score -= 5
    if event_or_campaign:
        entity_score -= 5
        latest_score -= 1
        general_score -= 3
    if operational_noise:
        entity_score -= 4
        latest_score -= 3
        general_score -= 3
    if community_domain and source_type != "community":
        entity_score -= 2
        latest_score -= 2
        general_score -= 1

    return SourcePolicyDecision(
        source_type=source_type,
        role_label=role_label,
        entity_score=entity_score,
        latest_score=latest_score,
        general_score=general_score,
    )


def score_source_for_mode(
    decision: SourcePolicyDecision,
    *,
    answer_mode: AnswerMode,
    freshness_risk: FreshnessRisk = "low",
) -> int:
    if answer_mode == "entity_card":
        score = decision.entity_score
    elif answer_mode == "latest_update":
        score = decision.latest_score
    else:
        score = decision.general_score

    if freshness_risk == "high" and decision.source_type == "wiki":
        score -= 3
    return score
