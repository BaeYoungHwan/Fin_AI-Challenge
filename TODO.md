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
- [ ] Streamlit Community Cloud 배포 테스트 (URL 확보 먼저 확인)

---

## P1 — MVP 핵심 기능

- [ ] 위험 신호(red flag) 탐지 — 매체·요청유형·본인확인 여부 등 키워드/규칙 기반 (`scam_classifier.py`)
- [ ] Retrieval Agent — 법제처 API 실시간 법령 검색 + 큐레이션 사기유형 DB 대조 (Top-3)
- [ ] Analysis Agent — 위험도(주의 수준) 판단 + 근거 조문 인용 + 환각 검증(재분석 루프) + 안전 행동요령 생성
  ※ 사기 여부 단정 금지 — 항상 "위험도 + 안전 행동요령" 형태로만 출력
- [ ] Feedback Agent — 사용자 피드백(도움됐는지) 수집 → 품질 필터링 → 로컬 벡터 저장소 저장
- [ ] Streamlit UI — 상황 입력 → 위험도/근거/행동요령 스트리밍 출력 → 피드백 입력창
- [ ] 시나리오별 E2E 테스트 (가족·지인 사칭형/기관 사칭형/대출빙자형 등 5개 이상)

---

## P2 — 검증 및 배포

- [ ] 배포 (Phase 0에서 결정한 방식) — 상시 접근 가능한 공개 URL 확보
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
