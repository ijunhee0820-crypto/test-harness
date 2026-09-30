#!/usr/bin/env python3
"""
S5 게이트 체크 스크립트 — 허들링 화면 설계 하네스.

harness/<slug>/ 의 S1~S4 산출물을 docs/design.md(디자인 규칙 SSOT)와
docs/story-service.md(어기면 안 되는 것)를 기준으로 점검하고,
harness/<slug>/S5-review-report.md 를 작성한다.

판정 에이전트(harness-judge)는 이 스크립트만 실행하고 그 외 파일은
읽기만 한다 — 실제 쓰기는 이 스크립트가 전담한다 (harness/harness-roles.md 참조).

Usage:
    python3 check_gates.py <request-slug> [--root <project-root>]
"""

from __future__ import annotations

import argparse
import datetime
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# 스캔 대상 확장자
# ---------------------------------------------------------------------------

CODE_EXTS = {".css", ".scss", ".less", ".ts", ".tsx", ".js", ".jsx", ".json", ".html"}
TEXT_EXTS = CODE_EXTS | {".md", ".txt"}

PII_PATTERNS = [
    (re.compile(r"\b01[016789]-?\d{3,4}-?\d{4}\b"), "전화번호로 보이는 패턴"),
    (re.compile(r"\b\d{6}-?[1-4]\d{6}\b"), "주민등록번호로 보이는 패턴"),
    (re.compile(r"기밀"), "'기밀' 표시 문자열"),
]

SALE_STATE_WORDS = ["검수대기", "수정요청", "승인됨", "반려"]


# ---------------------------------------------------------------------------
# SSOT 파싱 — docs/design.md 에서 직접 읽어온다 (하드코딩 금지)
# ---------------------------------------------------------------------------

def parse_allowed_radii(design_md: str) -> set[str]:
    # `| `{rounded.none}` | 0px | ... |` 형태의 표 행에서 px 값을 추출
    values = re.findall(r"`\{rounded\.[\w-]+\}`\s*\|\s*(\d+)px", design_md)
    return set(values) if values else {"0", "16", "24", "9999"}


def parse_allowed_colors(design_md: str) -> set[str]:
    hexes = re.findall(r"#[0-9a-fA-F]{6}\b", design_md)
    return {h.lower() for h in hexes}


# ---------------------------------------------------------------------------
# 파일 수집
# ---------------------------------------------------------------------------

def iter_text_files(slug_dir: Path):
    for path in sorted(slug_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in TEXT_EXTS and path.name != "S5-review-report.md":
            try:
                yield path, path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue


# ---------------------------------------------------------------------------
# 개별 체크
# ---------------------------------------------------------------------------

def check_border_radius(files, allowed_radii):
    violations = []
    pattern = re.compile(r"border-radius\s*[:=]\s*(\d+)px", re.IGNORECASE)
    for path, content in files:
        for m in pattern.finditer(content):
            if m.group(1) not in allowed_radii:
                violations.append(f"{path}: border-radius {m.group(1)}px (허용값 {sorted(allowed_radii, key=int)})")
    return violations


def check_box_shadow(files):
    violations = []
    pattern = re.compile(r"box-shadow\s*[:=]\s*([^;,\n]+)", re.IGNORECASE)
    for path, content in files:
        for m in pattern.finditer(content):
            value = m.group(1).strip().strip("'\"")
            if value.lower() not in ("none", "0"):
                violations.append(f"{path}: box-shadow 사용 감지 ({value})")
    return violations


def check_colors(files, allowed_colors):
    violations = []
    accent_pattern = re.compile(r"#0066ff", re.IGNORECASE)
    hex_pattern = re.compile(r"#[0-9a-fA-F]{6}\b")
    for path, content in files:
        for m in hex_pattern.finditer(content):
            if m.group(0).lower() not in allowed_colors:
                violations.append(f"{path}: design.md에 없는 색상 {m.group(0)}")
        accent_count = len(accent_pattern.findall(content))
        if accent_count > 2:
            violations.append(f"{path}: accent blue(#0066ff)가 {accent_count}회 사용됨 (화면당 1~2개 이하)")
    return violations


def check_font(files):
    violations = []
    family_pattern = re.compile(r"font-family\s*[:=]\s*([^;,\n]+)", re.IGNORECASE)
    spacing_pattern = re.compile(r"letter-spacing\s*[:=]\s*([^;,\n]+)", re.IGNORECASE)
    for path, content in files:
        for m in family_pattern.finditer(content):
            if "pretendard" not in m.group(1).lower():
                violations.append(f"{path}: font-family에 Pretendard가 아닌 값 사용 ({m.group(1).strip()})")
        for m in spacing_pattern.finditer(content):
            value = m.group(1).strip().strip("'\"").lower()
            if value not in ("0", "0px", "normal"):
                violations.append(f"{path}: letter-spacing이 0이 아님 ({value})")
    return violations


def check_pii(files):
    violations = []
    for path, content in files:
        for pattern, label in PII_PATTERNS:
            if pattern.search(content):
                violations.append(f"{path}: {label} 발견 — 개인정보/기밀 포함 금지 위반 (story-service.md)")
    return violations


def check_sale_flow_states(files):
    violations = []
    for path, content in files:
        if "판매" not in content:
            continue
        missing = [w for w in SALE_STATE_WORDS if w not in content]
        if "판매중" in content and missing:
            violations.append(
                f"{path}: '판매중' 상태가 있지만 검수 상태값 누락 {missing} — 운영자 검수 필수 위반 (story-service.md)"
            )
        elif missing and len(missing) == len(SALE_STATE_WORDS):
            violations.append(
                f"{path}: 판매 관련 화면인데 검수 상태값({SALE_STATE_WORDS})이 전혀 없음 — 확인 필요"
            )
    return violations


MANUAL_CHECK_NOTE = (
    "프레임 크기(390×844, 최소 360px 가로 스크롤 없음)와 Figma 키스크린 자체의 "
    "시각적 규칙 준수는 이 스크립트로 자동 판정할 수 없습니다. 사람이 S3 컨펌 시점에 "
    "직접 확인하세요."
)


# ---------------------------------------------------------------------------
# 메인
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="허들링 디자인 하네스 S5 게이트 체크")
    parser.add_argument("slug", help="request-slug (harness/<slug>/)")
    parser.add_argument("--root", default=None, help="프로젝트 루트 (기본값: 이 스크립트 기준 자동 탐지)")
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[2]
    harness_dir = root / "harness"
    docs_dir = root / "docs"
    slug_dir = harness_dir / args.slug

    design_md_path = docs_dir / "design.md"
    if not design_md_path.exists():
        print(f"ERROR: SSOT 파일을 찾을 수 없습니다: {design_md_path}", file=sys.stderr)
        sys.exit(1)

    if not slug_dir.exists():
        print(f"ERROR: 요청 폴더가 없습니다: {slug_dir}. 먼저 /harness-run {args.slug} 을 실행하세요.", file=sys.stderr)
        sys.exit(1)

    design_md = design_md_path.read_text(encoding="utf-8")
    allowed_radii = parse_allowed_radii(design_md)
    allowed_colors = parse_allowed_colors(design_md)

    files = list(iter_text_files(slug_dir))

    results = {
        "모서리(border-radius)": check_border_radius(files, allowed_radii),
        "그림자(box-shadow)": check_box_shadow(files),
        "색상 토큰": check_colors(files, allowed_colors),
        "폰트/자간": check_font(files),
        "개인정보·기밀 금지 (★ story-service.md)": check_pii(files),
        "판매 자산 검수 상태 (★ story-service.md)": check_sale_flow_states(files),
    }

    total_violations = sum(len(v) for v in results.values())
    overall = "FAIL" if total_violations > 0 else "PASS"
    timestamp = datetime.datetime.now().isoformat(timespec="seconds")

    lines = []
    lines.append(f"# S5 게이트 판정 리포트 — {args.slug}")
    lines.append("")
    lines.append(f"- 판정 시각: {timestamp}")
    lines.append(f"- 스캔한 파일 수: {len(files)}")
    lines.append(f"- 규칙 SSOT: docs/design.md, docs/story-service.md")
    lines.append(f"- **전체 판정: {overall}**")
    lines.append("")
    for rule, violations in results.items():
        status = "PASS" if not violations else f"FAIL ({len(violations)}건)"
        lines.append(f"## {rule} — {status}")
        lines.append("")
        if violations:
            for v in violations:
                lines.append(f"- {v}")
        else:
            lines.append("- 위반 없음")
        lines.append("")

    lines.append("## 수동 확인 필요")
    lines.append("")
    lines.append(f"- {MANUAL_CHECK_NOTE}")
    lines.append("")

    if files:
        lines.append("## 스캔한 파일 목록")
        lines.append("")
        for path, _ in files:
            lines.append(f"- {path.relative_to(root)}")
        lines.append("")
    else:
        lines.append("## 스캔한 파일 목록")
        lines.append("")
        lines.append(
            "- 스캔 대상 텍스트/코드 파일이 없습니다 (S3 Figma 키스크린은 이 스크립트로 읽을 수 없습니다). "
            "S4 산출물이 아직 없다면 게이트를 통과했다고 볼 수 없습니다."
        )
        lines.append("")

    report_path = slug_dir / "S5-review-report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"[{overall}] {args.slug}: {total_violations}건 위반, 리포트 작성 완료 → {report_path}")
    sys.exit(0 if overall == "PASS" else 1)


if __name__ == "__main__":
    main()
