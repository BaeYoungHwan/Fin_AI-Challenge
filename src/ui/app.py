from __future__ import annotations

import os
import sys
from pathlib import Path

# `streamlit run src/ui/app.py`로 실행하면 스크립트가 위치한 src/ui/ 디렉터리만
# sys.path에 잡혀 저장소 루트가 빠진다 — Streamlit Community Cloud에서 이 때문에
# `from src.agents import ...`가 ModuleNotFoundError로 실패했다.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st

# Streamlit Community Cloud의 Secrets는 st.secrets로만 노출되고 os.environ에는
# 자동 반영되지 않는다. law_search.py가 모듈 import 시점에 os.getenv로 키를 읽으므로,
# 아래에서 agents/tools를 import하기 전에 명시적으로 os.environ에 복사해야 한다.
# 로컬 실행 시(.env + python-dotenv 사용)는 secrets.toml이 없어 예외가 나므로 무시한다.
try:
    for _key, _value in st.secrets.items():
        os.environ.setdefault(_key, str(_value))
except Exception:
    pass

from src.agents import analysis_agent, feedback_agent, retrieval_agent

st.set_page_config(page_title="보이스피싱 대응 AI 금융보안비서", page_icon="🛡️")

st.title("🛡️ 보이스피싱 대응 AI 금융보안비서")
st.caption(
    "의심스러운 상황을 입력하면 위험 신호와 법령 근거, 안전 행동요령을 안내합니다. "
    "사기 여부를 단정하지 않으며, 최종 판단은 사용자와 공식 기관 확인을 통해 이루어져야 합니다."
)

situation = st.text_area(
    "어떤 상황인지 설명해 주세요",
    placeholder="예: 가족이 메신저로 갑자기 100만원을 급하게 빌려달라고 함",
    height=120,
)

if st.button("분석하기", type="primary", disabled=not situation.strip()):
    with st.spinner("위험 신호와 관련 법령을 검색하는 중..."):
        retrieval = retrieval_agent.run(situation)

    if retrieval["red_flags"]:
        st.warning("탐지된 위험 신호: " + ", ".join(retrieval["red_flags"]))

    response_area = st.empty()
    full_text = ""
    for chunk in analysis_agent.run(retrieval):
        full_text += chunk
        response_area.markdown(full_text)

    st.session_state["last_retrieval"] = retrieval
    st.session_state["last_analysis"] = full_text

if "last_analysis" in st.session_state:
    st.divider()
    st.subheader("이 답변이 도움이 되었나요?")
    col1, col2 = st.columns(2)
    note = st.text_input("의견을 남겨주시면 다음 답변 품질 개선에 반영됩니다 (선택)")

    if col1.button("도움됨"):
        feedback_agent.run(st.session_state["last_retrieval"], st.session_state["last_analysis"], True, note)
        st.success("피드백이 저장되었습니다. 감사합니다.")

    if col2.button("도움 안됨"):
        case_id = feedback_agent.run(
            st.session_state["last_retrieval"], st.session_state["last_analysis"], False, note
        )
        if case_id:
            st.success("피드백이 저장되었습니다. 감사합니다.")
        else:
            st.info("어떤 점이 부족했는지 조금 더 구체적으로 적어주시면 저장됩니다 (5자 이상).")

st.divider()
st.caption(
    "⚠️ 이 서비스는 위험 신호를 안내하는 보조 도구이며, 사기 여부를 확정하지 않습니다. "
    "의심되는 상황에서는 반드시 112(경찰) 또는 1332(금융감독원)로 직접 확인하세요."
)
