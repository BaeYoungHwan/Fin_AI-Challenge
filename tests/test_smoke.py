"""P0 스모크 테스트 — 로컬 컴포넌트(위험신호 탐지, 벡터 저장소)와 외부 연동(법제처 API, Groq)을
분리해서 확인한다. 외부 연동 테스트는 API 호출을 발생시키므로 필요할 때만 수동 실행한다.

실행: PYTHONPATH=. python tests/test_smoke.py
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 실제 시드/피드백 데이터 파일을 건드리지 않도록 벡터 저장소 경로를 임시 파일로 격리한다.
# 매 실행마다 깨끗한 상태로 시작하도록 이전 실행의 잔여 파일은 지운다.
_TEST_STORE_PATH = os.path.join(tempfile.gettempdir(), "vpg_test_store.json")
if os.path.exists(_TEST_STORE_PATH):
    os.remove(_TEST_STORE_PATH)
os.environ["VECTOR_STORE_PATH"] = _TEST_STORE_PATH

from src.tools.scam_classifier import classify


def test_scam_classifier() -> bool:
    result = classify("검찰청 수사관이라며 계좌를 동결해야 하니 안전계좌로 이체하라고 함")
    ok = "기관사칭형" in result.candidate_types and len(result.red_flags) > 0
    print(f"[scam_classifier] candidate_types={result.candidate_types} red_flags={result.red_flags} -> "
          f"{'PASS' if ok else 'FAIL'}")
    return ok


def test_vector_store_round_trip() -> bool:
    from src.db.vector_store import add_case, query_similar_cases

    dummy_embedding = [0.1] * 384
    add_case("test-case", "테스트 상황", dummy_embedding, {"scam_type": "테스트"})
    results = query_similar_cases(dummy_embedding, n_results=1)
    ok = len(results) > 0
    print(f"[vector_store] round-trip -> {'PASS' if ok else 'FAIL'}")
    return ok


def test_law_api_and_groq() -> bool:
    """외부 API 호출 발생 — Groq 무료 티어 요청 한도를 아끼려면 자주 실행하지 않는다."""
    from src.agents import analysis_agent, retrieval_agent

    retrieval = retrieval_agent.run("가족이 메신저로 100만원을 급하게 빌려달라고 함")
    law_ok = len(retrieval["law_articles"]) > 0
    print(f"[law_search] articles={len(retrieval['law_articles'])} -> {'PASS' if law_ok else 'FAIL'}")

    full_text = "".join(analysis_agent.run(retrieval))
    groq_ok = "위험도" in full_text
    print(f"[groq] response length={len(full_text)} -> {'PASS' if groq_ok else 'FAIL'}")
    return law_ok and groq_ok


if __name__ == "__main__":
    results = [test_scam_classifier(), test_vector_store_round_trip()]

    # 임베딩 차원이 다른 더미 데이터가 다음 테스트(실제 768차원 임베딩)와 섞이지 않도록 정리
    if os.path.exists(_TEST_STORE_PATH):
        os.remove(_TEST_STORE_PATH)

    if "--with-api" in sys.argv:
        results.append(test_law_api_and_groq())
    else:
        print("[law_search + groq] 건너뜀 — 실행하려면 `--with-api` 플래그 추가")

    print(f"\n{sum(results)}/{len(results)} 통과")
