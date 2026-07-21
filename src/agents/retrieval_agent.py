from __future__ import annotations

import logging
import os

from dotenv import load_dotenv

from src.db.vector_store import query_similar_cases
from src.tools.law_search import LawArticle, search_relevant_articles
from src.tools.scam_classifier import classify

load_dotenv()
logger = logging.getLogger(__name__)

_embedder = None


def _get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer

        model_name = os.getenv("EMBEDDING_MODEL", "jhgan/ko-sroberta-multitask")
        _embedder = SentenceTransformer(model_name)
    return _embedder


def get_embedding(text: str) -> list[float]:
    return _get_embedder().encode(text).tolist()


def run(situation: str) -> dict:
    """의심 상황 텍스트를 받아 위험 신호·유형 후보·법령 조문·유사 사례를 모아 반환한다."""
    try:
        embedding = get_embedding(situation)
    except Exception as e:
        logger.error("임베딩 실패: %s", e)
        raise RuntimeError(f"임베딩 모델 오류: {e}") from e

    classification = classify(situation)

    articles: list[LawArticle] = []
    if classification.law_keywords:
        try:
            articles = search_relevant_articles(classification.law_keywords, max_laws=2)
        except Exception as e:
            logger.warning("법제처 API 오류 (계속 진행): %s", e)

    similar_cases: list[dict] = []
    try:
        similar_cases = query_similar_cases(embedding, n_results=3)
    except Exception as e:
        logger.warning("벡터 저장소 조회 오류 (계속 진행): %s", e)

    return {
        "situation": situation,
        "red_flags": classification.red_flags,
        "candidate_types": classification.candidate_types,
        "law_articles": articles,
        "similar_cases": similar_cases,
        "embedding": embedding,
    }
