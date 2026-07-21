# Phase 0 — 기반 구축 실행 계획

> 프로젝트: voice-phishing-guardian | 작성일: 2026-07-14
> 참조: `docs/product-specs/PRD-v1.md`, `docs/design-docs/ARD-v1.md`, `docs/design-docs/architecture-v1.md`

---

## 목표

법제처 API + Groq API + 로컬 벡터 저장소 연동 골격을 만들고, "의심 상황 입력 → 법령 검색 →
LLM 응답 → 저장" 전체 흐름이 한 번 동작하는 것을 확인한다. 배포 골격(Streamlit Community
Cloud)도 이 단계에서 먼저 확보해 제출 마감 직전에 배포 이슈가 터지는 것을 방지한다.

## 선행 결정 (완료)

- LLM: Groq API 무료 티어 (Llama 3.3 70B) — Gemini는 계정 단위로 무료 티어 한도 0 문제가 있어 전환
- 배포: Streamlit Community Cloud
- 대응절차 데이터: 수작업 큐레이션 (경찰청 통합신고대응센터, 금감원 보이스피싱지킴이 참고)

## 작업 순서

### 1. 폴더 구조 + 의존성

- `src/agents/`, `src/tools/`, `src/db/`, `src/ui/`, `scripts/`, `tests/` 생성
- `requirements.txt` 작성: langchain, langchain-google-genai, numpy, sentence-transformers,
  streamlit, requests, python-dotenv
- `.env.example` 작성: `LAW_API_KEY`, `GOOGLE_API_KEY`

### 2. API 키 발급 (사용자 작업)

- 법제처 Open API: OC 코드 발급 (https://open.law.go.kr)
- Groq API: https://console.groq.com/keys 에서 무료 API 키 발급

### 3. 법령 검색 도구 (`src/tools/law_search.py`)

- 법제처 Open API 래퍼: 키워드 검색 → 법령 목록 → 조문 조회
- 대상 법령 카테고리: 통신사기피해환급법, 전자금융거래법, 개인정보보호법, 특정경제범죄가중처벌법,
  형법(사기죄) 등

### 4. 위험 신호 탐지 도구 (`src/tools/scam_classifier.py`)

- 매체(문자/메신저/전화), 요청유형(급전/개인정보/원격제어앱/링크클릭), 본인확인 절차 언급 여부 등
  키워드/패턴 기반 red flag 탐지
- 사기 유형 카테고리 정의: 가족·지인 사칭형, 기관 사칭형(최우선), 대출빙자형, 몸캠피싱형 등

### 5. 로컬 벡터 저장소 시드 데이터 (`scripts/seed_chroma.py`, `src/db/vector_store.py`)

- 사기 유형별 큐레이션 시나리오 10~20건 작성 (기관사칭형 우선순위 반영)
- 각 시나리오에 유형, 위험신호 패턴, 관련 법령 태그, 안전 행동요령 포함

### 6. Retrieval + Analysis Agent 최소 구현

- `src/agents/retrieval_agent.py`: 위험 신호 탐지 → 법령 검색 → 유사 유형 조회
- `src/agents/analysis_agent.py`: Groq 호출 → 위험도 + 근거 인용 + 행동요령 생성 →
  환각 인용 검증(재분석 루프)
- 프롬프트는 JB_LLM 문구를 복사하지 않고 신규 작성 (CLAUDE.md 제약 준수)

### 7. Hello World 검증

- 터미널에서 시나리오 1건("가족이 메신저로 100만원 급전 요청") 입력 → 전체 흐름 통과 확인

### 8. Streamlit Community Cloud 배포 골격

- 최소 동작하는 `src/ui/app.py`로 먼저 배포해 URL을 조기 확보
- 이후 기능을 이 배포 위에 점진적으로 추가

## 완료 기준

- [x] Hello World 시나리오 1건이 법령 인용 + 행동요령을 정상 출력 (스모크 테스트 3/3 통과)
- [ ] 환각 검증(미제공 법령 인용 시 재분석) 동작 확인
  — 로직(`_detect_hallucinated_citations` + 재분석 프롬프트)은 구현 완료, 단 미제공 법령을
    강제로 인용시켜 재분석 루프가 실제로 발동하는지 확인하는 테스트는 아직 없음 (P1로 이월)
- [x] Streamlit Community Cloud 배포 URL 확보 및 접속 확인 — https://finaichallenge.streamlit.app

## 결과

P0 목표(법령 검색 → 위험 신호 탐지 → LLM 분석 → 로컬 저장 골격 + 배포 URL 확보)는 달성.
환각 검증 로직의 동작 확인만 P1의 E2E 테스트 항목으로 이월한다.
