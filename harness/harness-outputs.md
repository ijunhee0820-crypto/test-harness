# 허들링 화면 설계 하네스 — 산출물 (R4)

## 단계별 산출물 경로

`harness/` 폴더 하위에 요청 단위 폴더를 만들고, 단계 접두사(S1~S5)로 정렬합니다.

```
harness/<request-slug>/
  S1-reference-analysis.md
  S2-screen-spec.md
  S3-keyscreens/           # Figma 키스크린 2~3개, 390×844
  S4-design-output/        # 디자인 토큰/컴포넌트 + 화면 디자인 파일
  S5-review-report.md
```

## 규칙 SSOT

새 파일을 만들지 않고 기존 `docs/design.md`를 그대로 규칙 단일 소스(SSOT)로 사용합니다.
(색상/타이포/라운드 스케일·Do's and Don'ts가 이미 표로 정리되어 있어 판정 스크립트가 직접 참조 가능)

## 재개 가능 여부

가능합니다. 각 단계 산출물 파일이 이미 존재하면 해당 단계는 건너뛰고 다음 단계부터 재개합니다.
