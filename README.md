# 🛡️ voice-phishing-guardian

> 보이스피싱·이상금융거래 의심 상황을 입력하면 위험 신호를 분석하고, 법령 근거와 실전 대응절차를
> 안내하는 AI 금융보안비서.
> **2026 금융 AI Challenge**(금융보안원 주최) 제출용 프로젝트입니다.

**배포 URL**: https://finaichallenge.streamlit.app

---

## 무엇을 하는 서비스인가

보이스피싱·메신저피싱 피해는 대부분 "판단이 필요한 순간"에 발생합니다. 문자·전화·메신저로
의심스러운 요청을 받았을 때, 이것이 실제 위험인지 즉시 판단하기 어렵고 관련 법적 보호장치나
지금 해야 할 행동도 바로 알기 어렵습니다.

이 서비스는 사용자가 겪은 상황을 텍스트로 입력하면:

1. 위험 신호(red flag)를 자동 탐지하고
2. 법제처 Open API로 관련 법령 조문을 실시간 검색해 근거로 제시하고
3. 큐레이션된 사기 유형 사례와 대조해 유사 패턴을 안내하고
4. **사기 여부를 단정하지 않고** 위험도와 함께 언제나 유효한 안전 행동요령(직접 재확인, 112/1332
   신고 등)을 제공합니다.

> ⚠️ 이 서비스는 위험 신호를 안내하는 보조 도구이며 사기 여부를 확정하지 않습니다. 실제 판단은
> 사용자와 공식 기관 확인을 통해 이루어져야 합니다.

---

## 아키텍처

```
상황 입력 (Streamlit UI)
    │
    ▼
[Retrieval Agent]  ← 법제처 Open API (실시간 법령 검색)
  위험 신호(red flag) 패턴 탐지 → 적용 법령 키워드 결정
  ← 로컬 벡터 저장소 (큐레이션 사기 유형·대응절차 Top-3)
    │
    ▼
[Analysis Agent]   ← Groq API (무료 티어, Llama 3.3 70B)
  위험도(주의 수준) 판단 + 법령 조항 인용 + 안전 행동요령 생성
  [검증 단계] 인용 조문 환각 탐지 → 미제공 법령 인용 시 자동 재분석
    │
    ▼
[Feedback Agent]   ← 사용자 피드백(도움됐는지) 입력
  품질 필터링 → 유효 피드백만 로컬 벡터 저장소 저장
```

## 기술 스택

- **Python 3.12** + **LangChain**
- **로컬 벡터 저장소**: numpy + JSON (ChromaDB의 네이티브 빌드 의존성 없이 Windows에서도 설치 가능)
- **법제처 Open API**: 법적 근거 실시간 검색 (환각 방지 검증 포함)
- **Groq API 무료 티어**(Llama 3.3 70B): 위험도 분석 + 행동요령 생성
- **Streamlit**: UI + Streamlit Community Cloud 배포

## 프로젝트 구조

```
src/
├── agents/
│   ├── retrieval_agent.py    # 법령 검색 + 위험 신호 탐지 + 유사 유형 조회
│   ├── analysis_agent.py     # 위험도 판단 + 행동요령 생성(LLM) + 환각 검증
│   └── feedback_agent.py     # 피드백 품질 필터링 + 사례 저장
├── tools/
│   ├── law_search.py         # 법제처 Open API 래퍼
│   └── scam_classifier.py    # 위험 신호 패턴 + 사기 유형 매핑
├── db/
│   └── vector_store.py       # 로컬 벡터 저장소 (numpy+JSON)
└── ui/
    └── app.py                # Streamlit UI
scripts/
└── seed_chroma.py            # 사기 유형·대응절차 큐레이션 시드 데이터 적재
tests/
├── test_smoke.py             # P0 스모크 테스트
└── test_e2e_scenarios.py     # 사기 유형별 E2E 테스트
```

---

## 로컬 실행

### 1. 의존성 설치

```bash
python -m venv .venv
.venv/Scripts/activate   # Windows
# source .venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
```

### 2. API 키 설정

`.env.example`을 `.env`로 복사한 뒤 값을 채웁니다.

```bash
cp .env.example .env
```

| 변수 | 발급처 |
|------|--------|
| `LAW_API_KEY` | [법제처 Open API](https://open.law.go.kr) — OC 코드 발급 |
| `GROQ_API_KEY` | [Groq Console](https://console.groq.com/keys) — 무료 API 키 발급 |

### 3. 시드 데이터 적재

사기 유형별 큐레이션 시나리오 10건을 로컬 벡터 저장소에 적재합니다 (최초 1회, 이미
`src/db/store/cases.json`에 포함되어 있어 생략 가능).

```bash
python scripts/seed_chroma.py
```

### 4. 앱 실행

```bash
streamlit run src/ui/app.py
```

---

## 테스트

```bash
# 권장 — API 호출 없이 로컬 컴포넌트만 검증 (분류기, 벡터 저장소, 환각 탐지)
python tests/test_smoke.py
python tests/test_e2e_scenarios.py

# 법제처 API + Groq를 태우는 전체 파이프라인까지 검증 (무료 티어 한도를 아끼기 위해 opt-in)
python tests/test_smoke.py --with-api
python tests/test_e2e_scenarios.py --with-api
```

> `pytest tests/`를 직접 실행하면 `--with-api` 플래그와 무관하게 API 호출 테스트까지 전부
> 수집·실행됩니다. pytest로 돌리려면 반드시 제외 필터를 함께 쓰세요:
> `pytest tests/ -k "not law_api_and_groq and not full_pipeline"`

---

## MVP 범위 제한

아래 항목은 명시적 요청 없이 구현하지 않습니다.

- 실시간 은행/통신사 시스템 연동을 통한 실제 이상거래 탐지
- 신고 자동 접수(경찰청/금융감독원 시스템 직접 연동)
- 다국어(i18n) 지원
- 사기 여부에 대한 단정적(예/아니오) 판정 제공

## 제약사항

- 이전 대회(JB금융그룹 Fin:AI Challenge) 제출작 JB_LLM의 코드·문서·프롬프트 문구를 재사용하지
  않습니다. 재사용 범위는 "RAG + 환각 검증 + 피드백 루프"라는 범용 아키텍처 패턴으로 제한하며,
  프롬프트·법령 카테고리·비즈니스 로직 문구는 모두 이 프로젝트에서 새로 작성했습니다.
- 이 저장소는 JB_LLM 저장소의 포크가 아닙니다.

## 대회 일정

- 기획서·MVP 제출 마감: 2026-09-07 10:00
- 웹서비스 URL 접근 가능 유지 기간: 2026-09-07 11:00 ~ 09-11 23:59
- 발표 심사 대상 명단 발표: 2026-09-22
- 발표 심사(오프라인): 2026-10-13
