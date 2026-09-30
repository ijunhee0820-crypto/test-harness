---
description: 허들링 디자인 하네스 판정 에이전트 실행 (S5 게이트 체크, review-report.md 작성)
argument-hint: <request-slug>
---

`CLAUDE.md`에 정의된 하네스 오케스트레이터의 `/harness-review` 트리거다.

인자(`$ARGUMENTS`): request-slug 하나.

1. `harness-judge` 서브에이전트를 Agent 도구로 호출한다 (`subagent_type: "harness-judge"`).
   전달할 내용: request-slug.
2. `harness-judge`는 `harness/scripts/check_gates.py <slug>`를 실행해 게이트를 판정하고
   `harness/<slug>/S5-review-report.md`를 만든다(스크립트가 직접 씀 — 에이전트는 읽기 전용).
3. 결과(PASS/FAIL)와 위반 항목을 사용자에게 요약해서 보여준다. `★ story-service.md` 표시가
   붙은 항목(개인정보/기밀, 판매 검수 상태)은 반드시 강조한다.
4. FAIL이면 `harness/harness-pipeline.md`의 복귀 규칙(S4로 복귀)을 안내한다.

이 커맨드 자신과 `harness-judge` 모두 `S5-review-report.md` 외의 어떤 파일도 만들거나
고치지 않는다.
