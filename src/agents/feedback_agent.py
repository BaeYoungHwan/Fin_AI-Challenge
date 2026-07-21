from __future__ import annotations

import logging
import uuid

from src.db.vector_store import add_case

logger = logging.getLogger(__name__)

_MIN_NOTE_LENGTH = 5
_DEFAULT_NOTES = {"도움됨", "도움 안됨", "확인"}


def _is_quality_feedback(helpful: bool, note: str) -> bool:
    """부정 피드백(도움 안됨)은 최소한의 설명이 있어야 저장한다. 기본값/공백만 입력된 경우는 거부."""
    if helpful:
        return True
    stripped = note.strip()
    if len(stripped) < _MIN_NOTE_LENGTH:
        return False
    if stripped in _DEFAULT_NOTES:
        return False
    return True


def run(retrieval: dict, analysis_text: str, helpful: bool, note: str) -> str | None:
    """피드백을 품질 필터링 후 ChromaDB에 저장한다. 저장 거부 시 None을 반환한다."""
    if not _is_quality_feedback(helpful, note):
        logger.info("피드백 품질 미달 — 저장 거부")
        return None

    case_id = str(uuid.uuid4())
    metadata = {
        "scam_type": ",".join(retrieval.get("candidate_types", [])) or "미분류",
        "red_flags": ",".join(retrieval.get("red_flags", [])),
        "helpful": helpful,
        "feedback_note": note.strip(),
        "safe_actions": analysis_text[:500],
    }

    add_case(
        case_id=case_id,
        text=retrieval.get("situation", ""),
        embedding=retrieval.get("embedding", []),
        metadata=metadata,
    )
    return case_id
