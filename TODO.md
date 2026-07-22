# TODO — voice-phishing-guardian

> 워크플로우: `[ ]` 대기 → `[🔄]` 진행 중 → `[x]` 완료
> 재시작 시: `docs/ref/session-state.md` 확인 후 `[🔄]` 항목부터 재개

---

## 시작 전

- [x] `/init-project` 실행 완료
- [ ] `docs/design-docs/architecture-v1.md` 검토 및 확정
- [ ] `docs/design-docs/ARD-v1.md` 비기능 요건 확정
- [ ] Phase 분할 후 `docs/exec-plans/active/`에 실행 계획 생성

---

## P0 — 기반 구축

- [x] LLM 배포 방식 결정 — **Groq API 무료 티어(Llama 3.3 70B)** (Gemini는 계정 단위 무료 한도 0 문제로 전환)
- [x] 배포 환경 결정 — **Streamlit Community Cloud**
- [x] 사기 대응절차 데이터 소스 조사 — **실시간 API 없음 확인, 수작업 큐레이션 확정**
  (경찰청 통합신고대응센터 counterscam112.go.kr, 금감원 보이스피싱지킴이 fss.or.kr 참고)
- [x] 레포 초기화 및 폴더 구조 생성 (`src/agents/`, `src/tools/`, `src/db/`, `src/ui/`, `tests/`, `scripts/`)
- [x] 법제처 Open API 키 발급 + `.env` 등록
- [x] Groq API 키 발급 (console.groq.com) + `.env` 등록
- [x] 사기 유형·대응절차 큐레이션 시드 데이터 10건 작성 (`scripts/seed_chroma.py`)
  (기관사칭형 4건 최우선 반영, 가족·지인 사칭형 2건, 대출빙자형 2건, 몸캠피싱형 1건, 기타 1건)
- [x] `law_search.py` / `scam_classifier.py` / `vector_store.py` / 3-Agent 파이프라인 / `app.py` 작성
- [x] 의존성 설치 완료 확인 + Hello World: 의심 상황 입력 → 법령 검색 → Groq 응답 → 로컬 벡터 저장소 저장 전체 흐름 확인 (스모크 테스트 3/3 통과)
- [x] Streamlit Community Cloud 배포 완료 — https://finaichallenge.streamlit.app

---

## P1 — MVP 핵심 기능

> P0에서 3-Agent 파이프라인을 만들며 아래 항목 대부분이 이미 실질적으로 구현됨.
> 재점검 결과 반영 (2026-07-22).

- [x] 위험 신호(red flag) 탐지 — 매체·요청유형·본인확인 여부 등 키워드/규칙 기반 (`scam_classifier.py`)
  (RED_FLAG_RULES 5종: 비대면 매체 / 급전·이체 요구 / 개인정보·인증 요구 / 원격·설치 유도 / 긴급성 강조)
- [x] Retrieval Agent — 법제처 API 실시간 법령 검색 + 큐레이션 사기유형 DB 대조 (Top-3) (`retrieval_agent.py`)
- [x] Analysis Agent — 위험도(주의 수준) 판단 + 근거 조문 인용 + 환각 검증(재분석 루프) + 안전 행동요령 생성
  (`analysis_agent.py`) ※ 사기 여부 단정 금지 — 항상 "위험도 + 안전 행동요령" 형태로만 출력
- [x] Feedback Agent — 사용자 피드백(도움됐는지) 수집 → 품질 필터링 → 로컬 벡터 저장소 저장 (`feedback_agent.py`)
- [x] Streamlit UI — 상황 입력 → 위험도/근거/행동요령 스트리밍 출력 → 피드백 입력창 (`app.py`)
- [x] 시나리오별 E2E 테스트 (`tests/test_e2e_scenarios.py`) — 7개 시나리오(기관사칭형/가족지인사칭형/
  대출빙자형/몸캠피싱형) 분류·유사사례 검색 로컬 테스트 5/5 통과 + 환각 인용 탐지 단위 테스트 포함
  ※ 테스트 작성 중 실제 버그 2건 발견해 수정: (1) 한국어 조사 결합으로 키워드 매칭이 깨지던
  `scam_classifier.py` 규칙 보강, (2) 테스트 파일 import 순서에 따라 벡터 저장소 경로가
  서로 덮어써지던 `vector_store.py` 격리 문제(환경변수 → 명시적 `store_path` 인자로 전환)
- [x] 환각 검증 강제 트리거 테스트 — `_detect_hallucinated_citations` 단위 테스트로 확인 완료
  (Groq API 호출 없이 검증됨)
- [ ] "사기 단정 금지" 프롬프트 강건성 — `--with-api` E2E 실행 중 Groq가 드물게 "사기 의심 정황"이
  아닌 단정적 표현을 낸 사례 1건 발견. 프롬프트에 금지 문구 명시 후 재현 안 됨(7회 중 0회)이나
  LLM 출력이 확률적이라 100% 보장은 아님 — 반복 관찰 필요, 심하면 출력 후검증 단계 추가 고려

---

## P2 — 검증 및 배포

- [ ] 배포 (Phase 0에서 결정한 방식) — 상시 접근 가능한 공개 URL 확보
  ※ P0 골격 배포는 완료(https://finaichallenge.streamlit.app, GitHub push 시 자동 재배포) —
    제출 마감(2026-09-07) 전 최종 기능으로 재확인 필요
- [ ] 기획서(PDF) / 기능명세서(PDF) 작성
- [ ] 시연 영상 (가점)
- [ ] 대회 제출 (~2026-09-07 10:00) — 기획서 + 기능명세서 + 웹서비스 URL
- [ ] (발표 심사 진출 시) 최종 소스코드(ZIP) + 발표자료(PDF) 준비 (~2026-10-08)

---

## 대회 일정 메모

- 기획서·MVP 제출 마감: 2026-09-07 10:00
- 웹서비스 URL 접근 가능 유지 기간: 2026-09-07 11:00 ~ 09-11 23:59
- 발표 심사 대상 명단 발표: 2026-09-22
- 발표 심사(오프라인): 2026-10-13
