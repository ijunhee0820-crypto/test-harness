# 허들링 화면 설계 하네스 — 역할 (R6)

## 에이전트 구성과 편집 폴더

- **작업 에이전트(worker)**: `harness/<slug>/` 안의 S1~S4 파일만 편집 가능 (S5 리포트는 편집 불가)
- **판정 에이전트(judge)**: 읽기 전용 + `harness/<slug>/S5-review-report.md` 파일 하나만 쓸 수 있음

## 판정 에이전트가 읽는 기준 문서

- `docs/design.md` (시각 규칙)
- `docs/story-service.md` (어기면 안 되는 것)

두 파일 모두 읽기 전용으로 참조합니다.

## 자연어 트리거

- `/harness-run <request-slug>` → 작업 에이전트가 S1~S4까지 순서대로 실행, S3 컨펌 게이트에서 정지(사람 승인 대기)
- `/harness-review <request-slug>` → 판정 에이전트가 S5 실행, `review-report.md` 작성
