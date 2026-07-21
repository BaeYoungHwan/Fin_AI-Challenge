# Claude Code 하네스 템플릿 — 지침 지도

> 이 파일은 ~100줄 지도입니다. 세부 규칙은 `docs/`에 있습니다.

---

## 핵심 규칙 (항상 적용)

- 코드·변수명: **영어** / 주석·커밋·소통: **한국어**
- 민감정보(API 키 등): `.env` 관리, 절대 커밋 금지
- CLAUDE.md는 핵심 규칙만 유지 — 특정 상황 규칙은 `docs/ref/`에 배치
- AI 행동 원칙 (코딩 전 사고, 단순함, 수술적 변경, 목표 중심) → [`docs/ref/behavioral-principles.md`](docs/ref/behavioral-principles.md)
- 브랜치 생성 금지: 사용자 명시 지시 없이 `git checkout -b`, `git switch -c` 실행 불가

---

## 모델 사용 규칙

| 작업 유형 | 모델 |
|-----------|------|
| 탐색 / grep / 파일 검색 | Haiku |
| 개발 (코딩, 디버깅, 리팩터링) | Sonnet |
| 설계 / 계획 (Plan 모드) | Opus |

자세한 기준 → [`docs/ref/agent-model-routing.md`](docs/ref/agent-model-routing.md)

---

## 보안 규칙

- `--no-verify`, `curl | sh`, 자격증명 직접 입력 금지 (훅이 차단)
- 모든 Bash 명령은 `logs/claude-audit.log`에 자동 기록됨
- 자세한 보안 정책 → [`docs/SECURITY.md`](docs/SECURITY.md)

---

## 에이전트 사용 규칙

- `agents/` 폴더 에이전트: **병렬 처리 서브태스크** 전용
- Plan 모드로 설계 후 독립적으로 분리 가능한 작업은 반드시 에이전트로 병렬 실행
- 에이전트 분류 기준 → [`agents/LANES.md`](agents/LANES.md)

**Plan 모드 실행 흐름**:
- 독립 태스크 3개+ → `/ultrawork`
- 독립 태스크 1~2개 → `/ralph`
- 단순 작업 → 직접 실행

**Plan 모드 실행 규칙** → [`docs/ref/plan-mode-workflow.md`](docs/ref/plan-mode-workflow.md):
- ExitPlanMode 승인 = 플랜 전체 일괄 승인 → 실행 단계 파일별 재확인 없음
- ExitPlanMode 직후 `docs/exec-plans/active/` Phase 문서 없으면 자동 생성
- Phase 2 설계 출력: 섹션형 리포트 형식 (코드 블록 아님)

---

## 작업 흐름

| 상황 | 참조 문서 |
|------|-----------|
| 새 프로젝트 시작 | [`docs/ref/project-setup.md`](docs/ref/project-setup.md) → `/init-project` |
| TODO 작업 진행 | [`docs/ref/todo-workflow.md`](docs/ref/todo-workflow.md) |
| 커밋 작성 | [`docs/ref/commit-convention.md`](docs/ref/commit-convention.md) |
| 테스트 전략 | [`docs/ref/testing-patterns.md`](docs/ref/testing-patterns.md) |
| 검증 전략 | [`docs/ref/verification-protocol.md`](docs/ref/verification-protocol.md) |
| PRD / 설계 문서 | [`docs/ref/PRD-template.md`](docs/ref/PRD-template.md) |
| Spec-driven 개발 | [`docs/ref/spec-driven-workflow.md`](docs/ref/spec-driven-workflow.md) |

---

## 컨텍스트 재시작 시 ("다음 작업 하자")

1. `docs/ref/session-state.md` 읽기 (git 상태)
2. `docs/exec-plans/active/` 읽기 (진행 중 작업 목록)
3. `[🔄]` 항목부터 이어서 진행

---

## 알림

- 1차: PC 토스트 알림 (`global-setup/` 설치 시 자동 동작)
- 세션 종료 시 git 상태 자동 저장 → `docs/ref/session-state.md`

---

## 프로젝트 구조

```
[프로젝트명]/
├── CLAUDE.md                  # 이 파일 (지침 지도)
├── TODO.md                    # 작업 목록
├── .claude/
│   ├── settings.json          # 권한 + 훅 등록
│   ├── hooks/                 # 보안·감사·세션 훅
│   ├── commands/              # 슬래시 스킬
│   └── skills/                # 하네스 내부 실행 스크립트 (score.py, analyze_sessions.py 등)
├── .claude-plugin/            # 마켓플레이스 플러그인 메타데이터
├── skills/                    # 마켓플레이스 배포용 — 다른 프로젝트가 설치 가능한 SKILL.md
├── agents/                    # 병렬 에이전트
├── docs/
│   ├── ref/                   # 참조 문서 (필요할 때만 로드)
│   ├── design-docs/           # 설계 문서
│   ├── exec-plans/            # 실행 계획 (active/completed)
│   └── product-specs/         # PRD / 기획 문서
├── src/
├── tests/
├── logs/                      # gitignore 대상
└── .env                       # gitignore 대상
```

---

## 프로젝트 맞춤 규칙

> `/init-project`에서 자동 생성됨. 이 프로젝트에만 적용됩니다.

### 프로젝트: voice-phishing-guardian

보이스피싱·이상금융거래 의심 상황을 입력하면 위험 신호를 분석하고, 법령 근거와 실전 대응절차를
안내하는 AI 금융보안비서. 2026 금융 AI Challenge(금융보안원 주최) 제출용.

### Claude 행동 지침

- **이전 대회(JB금융그룹 Fin:AI Challenge) 제출작인 JB_LLM의 코드·문서·프롬프트 문구를 직접 복사하지 않는다.**
  재사용 가능한 것은 "RAG + 환각 검증 + 피드백 루프"라는 범용 아키텍처 패턴뿐이며, 프롬프트 텍스트·UI
  라벨·법령 카테고리·비즈니스 로직 문구는 반드시 이 프로젝트에서 새로 작성한다.
  (이유: 대회 규정상 "다른 대회·프로젝트에 제출한 결과물의 재이용"이 확인되면 수상 취소·상금 회수 대상)
- 사기 위험도는 절대 "확정 판정"하지 않는다 — 항상 위험 신호(red flag)와 근거를 제시하고,
  사기 여부와 무관하게 유효한 안전 행동요령을 함께 제공한다.
- 법령 인용은 법제처 Open API가 실제로 반환한 조문 범위 내에서만 수행한다 (환각 방지 검증 필수).
- 새 GitHub 저장소(`https://github.com/BaeYoungHwan/Fin_AI-Challenge`)를 사용하며 JB_LLM 저장소의
  포크가 아니다.

### MVP 범위 제한

> 아래 항목은 명시적 요청 없이 절대 구현하지 않습니다.

- 실시간 은행/통신사 시스템 연동을 통한 실제 이상거래 탐지
- 신고 자동 접수(경찰청/금융감독원 시스템 직접 연동)
- 다국어(i18n) 지원
- 사기 여부에 대한 단정적(예/아니오) 판정 제공

### 기술 스택 고정

Python 3.12 + LangChain + 로컬 벡터 저장소(numpy+JSON, 사기유형·대응절차 큐레이션 DB) + 법제처 Open API(법적 근거 인용) +
Streamlit UI. LLM은 Groq API 무료 티어(Llama 3.3 70B), 배포는 Streamlit Community Cloud로 확정
(다른 라이브러리·프레임워크·유료 API 임의 도입 금지).
