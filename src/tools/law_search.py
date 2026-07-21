from __future__ import annotations

import os
import time
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("LAW_API_KEY")
BASE_URL = os.getenv("LAW_API_BASE_URL", "http://www.law.go.kr/DRF")


@dataclass
class LawItem:
    name: str
    mst: str
    department: str
    promulgation_date: str
    link: str


@dataclass
class LawArticle:
    law_name: str
    article_no: str
    article_title: str
    content: str


def _text(element: ET.Element, path: str) -> str:
    node = element.find(path)
    return (node.text or "").strip() if node is not None else ""


def search_laws(query: str, display: int = 5, page: int = 1) -> list[LawItem]:
    params = {
        "OC": API_KEY,
        "target": "law",
        "type": "XML",
        "query": query,
        "display": display,
        "page": page,
    }
    resp = requests.get(f"{BASE_URL}/lawSearch.do", params=params, timeout=10)
    resp.raise_for_status()

    root = ET.fromstring(resp.content)
    return [
        LawItem(
            name=_text(law, "법령명한글"),
            mst=_text(law, "법령일련번호"),
            department=_text(law, "소관부처명"),
            promulgation_date=_text(law, "공포일자"),
            link=_text(law, "법령상세링크"),
        )
        for law in root.findall(".//law")
    ]


def get_law_articles(mst: str) -> list[LawArticle]:
    url = f"{BASE_URL}/lawService.do?OC={API_KEY}&target=law&MST={mst}&type=XML"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = resp.read()

    root = ET.fromstring(data)
    law_name = _text(root, ".//법령명_한글")
    articles = []
    for jo in root.findall(".//조문단위"):
        if _text(jo, "조문여부") != "조문":
            continue
        content = _text(jo, "조문내용")
        if not content:
            continue
        articles.append(
            LawArticle(
                law_name=law_name,
                article_no=_text(jo, "조문번호"),
                article_title=_text(jo, "조문제목"),
                content=content,
            )
        )
    return articles


def search_relevant_articles(keywords: list[str], max_laws: int = 3, retries: int = 3) -> list[LawArticle]:
    """키워드별로 법령을 검색하고, 검색된 법령의 조문을 모아 반환한다. 중복 법령은 제외한다."""
    articles: list[LawArticle] = []
    seen_mst: set[str] = set()

    for keyword in keywords:
        laws = _retry(lambda: search_laws(keyword, display=max_laws), retries)
        for law in laws:
            if law.mst in seen_mst:
                continue
            seen_mst.add(law.mst)
            articles.extend(_retry(lambda: get_law_articles(law.mst), retries))

    return articles


def _retry(fn, retries: int):
    for attempt in range(retries):
        try:
            return fn()
        except Exception:
            if attempt == retries - 1:
                return []
            time.sleep(1)
    return []
