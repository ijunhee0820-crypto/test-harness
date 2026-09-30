# CLAUDE.md — 허들링 화면 설계 하네스 오케스트레이터

이 문서는 화면 설계 작업을 하네스(작업 에이전트 + 게이트 + 판정 스크립트)로 실행하기 위한
오케스트레이터입니다. **파일을 직접 편집하지 않고**, 트리거를 받아 아래 에이전트를 순서대로 호출하는
라우팅 역할만 합니다.

## 구현 파일

| 파일 | 역할 |
|---|---|
| `.claude/commands/harness-run.md` | `/harness-run` 슬래시 커맨드 |
| `.claude/commands/harness-review.md` | `/harness-review` 슬래시 커맨드 |
| `.claude/agents/harness-worker.md` | 작업 에이전트 정의 (Read/Write/Edit/Glob/Grep/Bash) |
| `.claude/agents/harness-judge.md` | 판정 에이전트 정의 (Read/Glob/Grep/Bash만 — Write 없음) |
| `harness/scripts/check_gates.py` | S5 게이트 자동 체크 스크립트. `docs/design.md`를 파싱해 규칙을 읽고, `harness/<slug>/S5-review-report.md`를 직접 작성 |

## 기준 문서

| 문서 | 역할 |
|---|---|
| `docs/prd.md` | 서비스 요구사항 원문 |
| `docs/design.md` | 디자인 규칙 SSOT (색상/타이포/라운드/Do's and Don'ts) |
| `docs/story-service.md` | 유저스토리 5개 + "어기면 안 되는 것" (판정 기준) |
| `docs/story-work.md` | 원래 손작업 7단계 (산출물/게이트/에이전트 경계) |
| `harness/harness-purpose.md` | R2 — 목적 |
| `harness/harness-pipeline.md` | R3 — 파이프라인 단계 정의 |
| `harness/harness-outputs.md` | R4 — 산출물 경로/SSOT/재개 정책 |
| `harness/harness-gates.md` | R5 — 게이트 조건 |
| `harness/harness-roles.md` | R6 — 에이전트 역할/트리거 |
| `harness/harness-orchestrator.md` | R7 — 오케스트레이터 동작 |
| `harness/harness-validation.md` | R8 — 검증과 리뷰 |

## 목적

- **매번 달라지는 것**: 새로운 화면/기능 요청(레퍼런스 + 요구사항)마다
- **사용자**: 본인(디자이너) 1인 + 승인자(운영자) 1명
- **완료 기준**: `design.md` 규칙 위반 0건 + 컨셉 시안 컨펌 완료 상태

## 파이프라인

| 단계 | 입력 | 출력 | 게이트 |
|---|---|---|---|
| S1. 레퍼런스 수집+분석 | 요청(레퍼런스 링크, 요구사항) | `S1-reference-analysis.md` | 없음 |
| S2. 화면설계 문서화 | S1 산출물 | `S2-screen-spec.md` | 없음 |
| S3. Figma 키스크린 제작 | S2 산출물 + design.md | 키스크린 2~3개 (390×844) | **사람 컨펌** |
| S4. 토큰/컴포넌트+화면 디자인 | 컨펌된 키스크린 | 디자인 토큰/컴포넌트 + 화면 디자인 | 내부 협의 컨펌 |
| S5. 가이드 위반 검토(판정) | 완성 산출물 | `S5-review-report.md` | design.md 자동 체크 |

실패 시 복귀: S5 실패 → S4로, S3 컨펌 거절 → S2로. 재시도 횟수 제한 없음.

## 산출물 경로

```
harness/<request-slug>/
  S1-reference-analysis.md
  S2-screen-spec.md
  S3-keyscreens/
  S4-design-output/
  S5-review-report.md
```

각 단계 산출물이 이미 있으면 해당 단계는 건너뛰고 다음 단계부터 재개합니다(재개 가능).

## 게이트 조건

**기계 자동 체크 (S5):**
- 모서리 `0 / 16 / 24 / 9999`만 허용
- design.md 색상 토큰만 사용, accent blue는 화면당 1~2개 이하
- box-shadow 0건
- 390×844 기준, 최소 360px 폭에서 가로 스크롤 없음
- Pretendard만, letter-spacing 0

**★ `story-service.md` "어기면 안 되는 것" 위반 시 게이트 실패:**
- (a) 목업/예시 콘텐츠에 실명·연락처·주민번호 패턴 또는 "기밀" 문자열 발견 시
- (b) 판매 신청 관련 화면에 상태값(`검수대기/수정요청/승인됨/반려`) 누락, 또는 검수 없이 "판매중"으로 바로 전이하는 화면이 있을 시

**사람 승인 지점**: S3 (Figma 키스크린 컨펌) 1곳.

## 에이전트 역할

- **작업 에이전트 (worker)**: `harness/<slug>/`의 S1~S4 파일만 편집 가능
- **판정 에이전트 (judge)**: 읽기 전용 (`docs/design.md`, `docs/story-service.md` 참조) + `S5-review-report.md`만 작성 가능

## 트리거

- `/harness-run <request-slug>` → 작업 에이전트가 S1~S4 실행, S3에서 정지(사람 승인 대기)
- `/harness-review <request-slug>` → 판정 에이전트가 S5 실행, `review-report.md` 작성

## 오케스트레이터 동작

- 파일을 직접 편집하지 않고 라우팅만 수행
- 여러 요청(slug)을 동시에 진행 가능 (각각 독립 폴더), 단 사람 승인은 한 번에 하나씩
- 각 단계 산출물 파일의 존재 여부 + `review-report.md`의 PASS/FAIL로 다음 행동 결정

## 검증과 리뷰

- 첫 실행은 샘플 요청 1개로 S1~S5 전체를 수동 검증 후 실사용 전환
- `review-report.md`는 실패 이력 포함 삭제 없이 보존 (감사 가능)
- SSOT(`design.md`, `story-service.md`) 변경 시 별도 버전 고정 없이 다음 실행부터 자동 반영
- 사람의 최종 리뷰 지점: S3 컨펌 + S5 리포트 확인
