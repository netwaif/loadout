#!/usr/bin/env python3
"""CLAUDE.md 구성 백화점 — 결정적 조각 설치기.

카탈로그의 구성 조각(fragment)을 골라 대상 폴더 CLAUDE.md에 마커 기반으로
멱등 append 한다. 멀티에이전트 품목만 configure-multiagent init.py에 스캐폴드 위임.
- 결정적: 번들 조각을 그대로 삽입. LLM 자유작문 없음.
- 배타: 같은 corner 품목 동시/중복 설치를 설치 시점에 거부(exit 2).
- 1차 지원 하네스 = claude (CLAUDE.md). 조각은 순수 마크다운(벤더 중립).

사용:
    python3 store.py --list
    python3 store.py --target ~/work/my-folder --pick karpathy,fable5-solo --yes
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
FRAGMENTS_DIR = SCRIPT_DIR / "fragments"
INIT_PY = SCRIPT_DIR.parents[1] / "configure-multiagent" / "generator" / "init.py"
INSTRUCTION_FILE = "CLAUDE.md"   # 1차 = claude flavor만. 2차서 flavor 매핑 확장.


def marker(name: str) -> tuple[str, str]:
    return f"<!-- store:{name}:start -->", f"<!-- store:{name}:end -->"


def load_catalog() -> dict[str, dict]:
    catalog: dict[str, dict] = {}
    for meta_path in sorted(FRAGMENTS_DIR.glob("*/meta.json")):
        name = meta_path.parent.name
        if name.startswith("_"):
            continue
        catalog[name] = json.loads(meta_path.read_text(encoding="utf-8"))
    return catalog


def print_catalog(catalog: dict[str, dict]) -> None:
    print("CLAUDE.md 구성 백화점 — 카탈로그")
    for i, (name, m) in enumerate(catalog.items(), 1):
        status = "" if m["available"] else "  [입점 예정]"
        print(f"  {i}. {m['label']} ({name}) — 코너: {m['corner']}{status}")
        print(f"     {m['desc']}")
        if m.get("note"):
            print(f"     ※ {m['note']}")
    print("\n규칙: 같은 코너 품목끼리는 함께 설치할 수 없습니다(상호배타). 코너가 다르면 조합 자유.")


def installed_names(target: Path) -> set[str]:
    instr = target / INSTRUCTION_FILE
    if not instr.is_file():
        return set()
    return set(re.findall(r"<!-- store:([a-z0-9-]+):start -->", instr.read_text(encoding="utf-8")))


def install_fragment(target: Path, name: str, dry: bool) -> str:
    """조각을 대상 CLAUDE.md에 멱등 삽입(마커 교체-또는-append) + files/ 트리 복사."""
    frag_dir = FRAGMENTS_DIR / name
    start, end = marker(name)
    block = f"{start}\n{(frag_dir / 'fragment.md').read_text(encoding='utf-8').strip(chr(10))}\n{end}"
    instr = target / INSTRUCTION_FILE
    text = instr.read_text(encoding="utf-8") if instr.is_file() else ""
    if start in text and end in text:
        new = re.sub(re.escape(start) + r".*?" + re.escape(end), lambda m: block, text, count=1, flags=re.S)  # 치환문자열 backslash escape 해석 방지 — 조각 본문에 \g·\\ 있어도 byte-exact
        action = "교체"
    else:
        new = (text.rstrip("\n") + "\n\n" if text else "") + block + "\n"
        action = "설치"
    if not dry:
        target.mkdir(parents=True, exist_ok=True)
        instr.write_text(new, encoding="utf-8")
    files_dir = frag_dir / "files"
    copied = 0
    if files_dir.is_dir():
        import shutil
        for src in sorted(files_dir.rglob("*")):
            if src.is_dir():
                continue
            dest = target / src.relative_to(files_dir)
            if not dry:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
            copied += 1
    extra = f" (+딸린 파일 {copied}개)" if copied else ""
    return f"{name} {action} → {INSTRUCTION_FILE}{extra}"


def main() -> None:
    ap = argparse.ArgumentParser(description="CLAUDE.md 구성 백화점 (결정적 조각 설치기)")
    ap.add_argument("--list", action="store_true", help="카탈로그 출력")
    ap.add_argument("--target", help="설치 대상 폴더")
    ap.add_argument("--pick", help="설치할 품목(쉼표 구분, 예: karpathy,agent-loop)")
    ap.add_argument("--yes", action="store_true", help="확인 프롬프트 생략")
    ap.add_argument("--dry-run", action="store_true", help="실제 쓰지 않고 미리보기")
    args = ap.parse_args()

    catalog = load_catalog()
    if not catalog:
        sys.exit(f"[error] fragments가 없습니다: {FRAGMENTS_DIR}")

    if args.list or not (args.target and args.pick):
        print_catalog(catalog)
        return

    picks = [p.strip() for p in args.pick.split(",") if p.strip()]
    unknown = [p for p in picks if p not in catalog]
    if unknown:
        print(f"[error] 없는 품목: {', '.join(unknown)}")
        sys.exit(2)
    unavailable = [p for p in picks if not catalog[p]["available"]]
    if unavailable:
        for p in unavailable:
            print(f"[안내] {catalog[p]['label']}: {catalog[p]['note']}")
        sys.exit(2)

    target = Path(args.target).expanduser().resolve()
    if target == SCRIPT_DIR or SCRIPT_DIR in target.parents or target in SCRIPT_DIR.parents:
        sys.exit(f"[error] installer 트리 안에는 설치할 수 없습니다: {target}")

    print(f"  target : {target}")
    print(f"  담은 품목: {', '.join(catalog[p]['label'] for p in picks)}")
    if not args.yes and not args.dry_run:
        if input("\n진행할까요? [y/N]: ").strip().lower() not in ("y", "yes"):
            sys.exit("취소됨")

    prefix = "(dry) " if args.dry_run else ""
    for p in picks:
        print(f"  {prefix}{install_fragment(target, p, dry=args.dry_run)}")
    print("\n  완료.")


if __name__ == "__main__":
    main()
