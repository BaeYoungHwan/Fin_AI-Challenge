"""P1 시나리오별 E2E 테스트 — 큐레이션 시드 데이터(scripts/seed_chroma.py)를 근거로
분류(classify) + 유사 사례 검색(retrieval)까지는 항상 검증하고, 법제처/Groq API를 태우는
전체 파이프라인 검증은 `--with-api` 플래그가 있을 때만 일부 시나리오로 제한해 실행한다
(Groq 무료 티어 요청 한도를 아끼기 위함).

실행:
  PYTHONPATH=. python tests/test_e2e_scenarios.py            # API 호출 없이 로컬 검증만
  PYTHONPATH=. python tests/test_e2e_scenarios.py --with-api  # 전체 파이프라인까지 검증
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 시드 데이터가 실제로 채워진 저장소를 대상으로 검증한다. query_similar_cases에 이 경로를
# 직접 넘긴다 — 환경변수를 공유하면 다른 테스트 파일의 import 순서에 따라 서로 경로를
# 덮어쓰는 문제가 있어 피한다.
_SEED_STORE_PATH = str(Path(__file__).resolve().parent.parent / "src" / "db" / "store" / "cases.json")

from src.db.vector_store import query_similar_cases  # noqa: E402
from src.tools.scam_classifier import classify  # noqa: E402

# (상황, 기대 유형, 최소 red flag 수) — scripts/seed_chroma.py의 유형 분포를 반영한다.
SCENARIOS = [
    ("검찰청 수사관이라며 전화로 계좌가 범죄에 연루되어 동결해야 하니 안전계좌로 이체하라고 함",
     "기관사칭형", 1),
    ("금융감독원 직원이라며 명의도용 확인을 위해 앱을 설치하고 계좌 비밀번호를 알려달라고 함",
     "기관사칭형", 1),
    ("자녀를 사칭한 사람이 메신저로 폰이 고장나서 문자로 연락한다며 급하게 100만원을 보내달라고 함",
     "가족지인사칭형", 1),
    ("지인이 카카오톡으로 갑자기 급하게 돈이 필요하다며 계좌로 조금만 빌려달라고 요청함",
     "가족지인사칭형", 1),
    ("정부지원 저금리 대환대출을 안내한다며 상환용으로 먼저 일부 금액을 입금해야 대출이 실행된다고 함",
     "대출빙자형", 1),
    ("신용등급이 낮아 대출이 어렵다며 등급을 높여주는 작업이 필요하니 앱을 설치하고 입금하라고 함",
     "대출빙자형", 1),
    ("영상통화 중 신체 노출을 유도한 뒤 영상을 유포하지 않으려면 돈을 보내라고 협박함",
     "몸캠피싱형", 1),
]

# 전체 파이프라인(법제처 API + Groq) 검증은 유형당 1건으로 제한한다.
API_SCENARIOS = [SCENARIOS[0], SCENARIOS[2], SCENARIOS[4], SCENARIOS[6]]

# MVP 제약: 사기 여부를 단정하는 표현이 출력에 섞이면 안 된다.
_FORBIDDEN_PATTERNS = [r"사기\s*(가|입니다|맞습니다|확실)", r"100%\s*사기", r"명백한\s*사기"]


def test_scenario_classification() -> bool:
    """분류기가 각 시나리오에서 기대 유형과 위험 신호를 탐지하는지 확인 (API 호출 없음)."""
    failures = []
    for situation, expected_type, min_flags in SCENARIOS:
        result = classify(situation)
        ok = expected_type in result.candidate_types and len(result.red_flags) >= min_flags
        print(f"[classify] {expected_type} -> candidates={result.candidate_types} "
              f"red_flags={result.red_flags} -> {'PASS' if ok else 'FAIL'}")
        if not ok:
            failures.append(f"{expected_type!r}: candidates={result.candidate_types} red_flags={result.red_flags}")
    assert not failures, "분류 실패:\n" + "\n".join(failures)
    return True


def test_scenario_similar_case_retrieval() -> bool:
    """시드 저장소에서 각 시나리오와 같은 유형의 유사 사례가 Top-3 안에 검색되는지 확인 (API 호출 없음)."""
    from src.agents.retrieval_agent import get_embedding

    failures = []
    for situation, expected_type, _ in SCENARIOS:
        embedding = get_embedding(situation)
        results = query_similar_cases(embedding, n_results=3, store_path=_SEED_STORE_PATH)
        found_types = [r["metadata"].get("scam_type") for r in results]
        ok = expected_type in found_types
        print(f"[retrieval] {expected_type} -> top3_types={found_types} -> {'PASS' if ok else 'FAIL'}")
        if not ok:
            failures.append(f"{expected_type!r}: top3_types={found_types}")
    assert not failures, "유사 사례 검색 실패:\n" + "\n".join(failures)
    return True


def test_hallucination_detection_forces_flag() -> bool:
    """제공되지 않은 법령이 '관련 법령 근거' 섹션에 인용되면 탐지되는지 확인 (API 호출 없음)."""
    from src.tools.law_search import LawArticle
    from src.agents.analysis_agent import _detect_hallucinated_citations

    provided = [LawArticle(law_name="통신사기피해환급법", article_no="2", article_title="정의", content="...")]

    hallucinated_text = (
        "## 위험도: 높음\n\n## 판단 근거\n급전 요청과 원격 앱 설치 유도가 확인됨\n\n"
        "## 관련 법령 근거\n[대부업법] 제9조에 따라...\n\n## 안전 행동요령\n직접 재확인, 112 신고"
    )
    clean_text = (
        "## 위험도: 높음\n\n## 판단 근거\n급전 요청과 원격 앱 설치 유도가 확인됨\n\n"
        "## 관련 법령 근거\n[통신사기피해환급법] 제2조에 따라...\n\n## 안전 행동요령\n직접 재확인, 112 신고"
    )

    flagged = _detect_hallucinated_citations(hallucinated_text, provided)
    clean = _detect_hallucinated_citations(clean_text, provided)

    ok = "대부업법" in flagged and clean == []
    print(f"[hallucination] flagged={flagged} clean_case={clean} -> {'PASS' if ok else 'FAIL'}")
    assert ok, f"환각 인용 탐지 실패: flagged={flagged} clean_case={clean}"
    return True


def test_full_pipeline_with_api() -> bool:
    """법제처 API + Groq를 태워 전체 파이프라인과 '단정 금지' 제약을 확인한다. 유형당 1건으로 제한."""
    from src.agents import analysis_agent, retrieval_agent

    failures = []
    for situation, expected_type, _ in API_SCENARIOS:
        retrieval = retrieval_agent.run(situation)
        full_text = "".join(analysis_agent.run(retrieval))

        has_sections = all(s in full_text for s in ("위험도", "판단 근거", "관련 법령 근거", "안전 행동요령"))
        no_forbidden = not any(re.search(p, full_text) for p in _FORBIDDEN_PATTERNS)
        ok = has_sections and no_forbidden
        print(f"[full_pipeline] {expected_type} -> sections={has_sections} "
              f"no_definitive_claim={no_forbidden} -> {'PASS' if ok else 'FAIL'}")
        if not ok:
            failures.append(f"{expected_type!r}: sections={has_sections} no_definitive_claim={no_forbidden}")
    assert not failures, "전체 파이프라인 검증 실패:\n" + "\n".join(failures)
    return True


if __name__ == "__main__":
    results = [
        test_scenario_classification(),
        test_scenario_similar_case_retrieval(),
        test_hallucination_detection_forces_flag(),
    ]

    if "--with-api" in sys.argv:
        results.append(test_full_pipeline_with_api())
    else:
        print("[full_pipeline] 건너뜀 — 실행하려면 `--with-api` 플래그 추가")

    print(f"\n{sum(results)}/{len(results)} 통과")
