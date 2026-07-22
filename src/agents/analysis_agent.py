from __future__ import annotations

import os
import re
import logging
from typing import Generator

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from src.tools import usage_guard
from src.tools.law_search import LawArticle
from src.tools.scam_classifier import SCAM_TYPES

load_dotenv()
logger = logging.getLogger(__name__)

_llm = None

KNOWN_LAW_NAMES = sorted({kw for spec in SCAM_TYPES.values() for kw in spec["law_keywords"]})


def _get_llm() -> ChatGroq:
    global _llm
    if _llm is None:
        _llm = ChatGroq(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            api_key=os.getenv("GROQ_API_KEY"),
        )
    return _llm


def _format_articles(articles: list[LawArticle], max_articles: int = 10) -> str:
    if not articles:
        return "(검색된 법령 조문 없음)"
    parts = []
    for a in articles[:max_articles]:
        parts.append(f"[{a.law_name}] 제{a.article_no}조({a.article_title})\n{a.content[:300]}")
    return "\n\n".join(parts)


def _format_cases(cases: list[dict], max_len: int = 150) -> str:
    if not cases:
        return "(유사 과거 사례 없음)"
    parts = []
    for c in cases:
        meta = c.get("metadata", {})
        sim = c.get("similarity", 0)
        scam_type = meta.get("scam_type", "미분류")
        actions = meta.get("safe_actions", "")
        text = c.get("content", "")[:max_len]
        parts.append(f"유사도 {sim:.0%} | 유형: {scam_type}\n내용: {text}\n권장 행동: {actions}")
    return "\n\n".join(parts)


def _extract_section(text: str, name: str) -> str:
    m = re.search(rf"##\s*{re.escape(name)}(.*?)(?=##|\Z)", text, re.DOTALL)
    return m.group(1).strip() if m else ""


def _detect_hallucinated_citations(analysis_text: str, articles: list[LawArticle]) -> list[str]:
    section = _extract_section(analysis_text, "관련 법령 근거")
    if not section or any(kw in section for kw in ("해당 없음", "해당없음", "없음")):
        return []
    retrieved_names = {a.law_name for a in articles}
    return [law for law in KNOWN_LAW_NAMES if law in section and law not in retrieved_names]


def _build_prompt(retrieval: dict, law_text: str, case_text: str) -> str:
    red_flags = ", ".join(retrieval.get("red_flags", [])) or "탐지된 위험 신호 없음"
    candidates = ", ".join(retrieval.get("candidate_types", [])) or "특정 유형 패턴 미검출"

    return (
        "당신은 보이스피싱·이상금융거래 대응을 안내하는 금융보안비서입니다. "
        "아래 정보를 근거로 위험 신호를 안내하세요.\n\n"
        "**중요**: 이것이 실제 사기인지 아닌지 절대 단정하지 마세요. 진짜 가족·기관일 수도 있습니다. "
        "'사기입니다', '사기가 맞습니다', '명백한 사기', '100% 사기' 같은 단정적 표현은 어떤 경우에도 "
        "사용하지 말고, 항상 '사기 의심 정황', '~일 가능성이 있습니다', '~와 유사한 패턴입니다'처럼 "
        "가능성으로만 표현하세요. "
        "항상 '위험도 + 판단 근거 + 안전 행동요령' 형태로만 답하고, 안전 행동요령은 사기 여부와 "
        "무관하게 항상 유효한 내용(직접 재확인, 공식 신고처 안내 등)으로 작성하세요.\n\n"
        f"[사용자 입력 상황]\n{retrieval.get('situation', '')}\n\n"
        f"[자동 탐지된 위험 신호]\n{red_flags}\n\n"
        f"[유형 후보 (참고용, 확정 아님)]\n{candidates}\n\n"
        f"[관련 법령 조문 - 법제처 API]\n{law_text}\n\n"
        f"[유사 과거 사례]\n{case_text}\n\n"
        "다음 형식으로만 답하세요:\n"
        "## 위험도: 높음 / 주의 / 낮음\n\n"
        "## 판단 근거\n(위 위험 신호·유형 후보·유사 사례를 바탕으로 2~3문장)\n\n"
        "## 관련 법령 근거\n(위 [관련 법령 조문]에서 직접 인용. 없으면 '해당 없음')\n\n"
        "## 안전 행동요령\n(사기 여부와 무관하게 항상 유효한 행동 1~3개. "
        "예: 직접 전화로 재확인, 112/1332 신고, 링크·앱 설치 금지 등)\n\n"
        "위 [관련 법령 근거]는 [관련 법령 조문]에 실제로 존재하는 조문만 인용해야 합니다."
    )


def _build_correction_prompt(original_prompt: str, prior_analysis: str, hallucinated: list[str]) -> str:
    names = ", ".join(hallucinated)
    return (
        "이전 분석에서 제공된 조문 목록에 없는 법령이 '관련 법령 근거'에 인용되었습니다.\n"
        f"확인되지 않은 인용: {names}\n\n"
        "아래 규칙을 지켜 분석 전체를 재작성하세요:\n"
        "- '관련 법령 근거'는 반드시 제공된 법령 조문에 실제로 존재하는 조문만 인용할 것\n"
        "- 관련 조문이 없으면 '해당 없음'으로 명시할 것\n"
        "- 나머지 형식(위험도 / 판단 근거 / 안전 행동요령)은 동일하게 유지할 것\n\n"
        f"[이전 분석 (참고용)]\n{prior_analysis[:800]}\n\n"
        f"[원본 지시]\n{original_prompt}"
    )


def run(retrieval: dict) -> Generator[str, None, None]:
    if usage_guard.limit_reached():
        logger.warning("Groq 일일 사용량 여유 한도(%d) 도달 — 호출 차단", usage_guard.soft_cap())
        yield (
            "\n\n[안내] 오늘의 무료 API 사용량이 여유 한도에 도달해 지금은 분석할 수 없습니다. "
            "내일 다시 시도해 주세요. 급한 경우 112(경찰) 또는 1332(금융감독원)로 직접 문의하세요."
        )
        return

    articles = retrieval.get("law_articles", [])
    cases = retrieval.get("similar_cases", [])
    law_text = _format_articles(articles)
    case_text = _format_cases(cases)

    llm = _get_llm()
    prompt = _build_prompt(retrieval, law_text, case_text)

    chunks: list[str] = []
    usage_guard.record_request()
    try:
        for chunk in llm.stream(prompt):
            piece = chunk.content if hasattr(chunk, "content") else str(chunk)
            if piece:
                chunks.append(piece)
                yield piece
    except Exception as e:
        logger.error("Groq 호출 실패: %s", e)
        yield f"\n\n[오류] LLM 호출에 실패했습니다: {e}"
        return

    full_text = "".join(chunks)
    if not full_text.strip():
        yield "\n\n[오류] 빈 응답을 받았습니다. 잠시 후 다시 시도해 주세요."
        return

    hallucinated = _detect_hallucinated_citations(full_text, articles)
    if not hallucinated:
        return

    if usage_guard.limit_reached():
        logger.warning("재분석 직전 사용량 여유 한도 도달 — 재분석 건너뜀")
        return

    logger.info("환각 인용 탐지 — 재분석 트리거: %s", hallucinated)
    yield "\n\n[검증] 인용 근거 재확인 중...\n\n"

    correction_prompt = _build_correction_prompt(prompt, full_text, hallucinated)
    usage_guard.record_request()
    try:
        for chunk in llm.stream(correction_prompt):
            piece = chunk.content if hasattr(chunk, "content") else str(chunk)
            if piece:
                yield piece
    except Exception as e:
        logger.error("재분석 호출 실패: %s", e)
        yield f"\n\n[오류] 재분석에 실패했습니다: {e}"
