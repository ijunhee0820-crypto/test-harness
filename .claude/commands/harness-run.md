---
description: 허들링 디자인 하네스 작업 에이전트 실행 (S1~S4, S3에서 사람 컨펌을 위해 정지)
argument-hint: <request-slug> <요청 설명 / 레퍼런스 링크>
---

`CLAUDE.md`에 정의된 하네스 오케스트레이터의 `/harness-run` 트리거다.

인자(`$ARGUMENTS`): 첫 단어는 request-slug, 나머지는 요청 설명(레퍼런스 링크, 요구사항)이다.

1. `harness-worker` 서브에이전트를 Agent 도구로 호출한다 (`subagent_type: "harness-worker"`).
   전달할 내용: request-slug와 요청 설명 전체.
2. 이미 `harness/<slug>/`에 산출물이 있으면 재개 정책(`harness/harness-outputs.md`)에 따라
   이어서 진행하도록 지시한다.
3. 작업 에이전트가 S3(Figma 키스크린)까지 마치면 멈추고 사람 컨펌을 기다린다. 이 시점에
   결과를 사용자에게 보여주고 승인 여부를 물어본다.
4. 사용자가 이미 승인했고 S4까지 이어가라고 하면, 같은 request-slug로 `harness-worker`를
   다시 호출해 S4를 진행시킨다.
5. S4까지 끝나면 사용자에게 `/harness-review <slug>`가 다음 단계임을 안내한다.

이 커맨드 자신은 파일을 직접 만들거나 고치지 않는다 — 반드시 `harness-worker` 서브에이전트를
통해서만 산출물을 만든다.
