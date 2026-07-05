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
import os
import re
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
FRAGMENTS_DIR = SCRIPT_DIR / "fragments"
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


def check_exclusions(picks: list[str], installed: set[str], catalog: dict) -> list[str]:
    """같은 corner = 상호배타. picks 내부 쌍 + picks↔기설치(동일 품목 제외)."""
    problems: list[str] = []
    for i, a in enumerate(picks):
        for b in picks[i + 1:]:
            if catalog[a]["corner"] == catalog[b]["corner"]:
                problems.append(f"{catalog[a]['label']} ↔ {catalog[b]['label']}: 같은 코너({catalog[a]['corner']}) — 동시 설치 불가")
    for p in picks:
        for ins in installed:
            if ins != p and ins in catalog and catalog[ins]["corner"] == catalog[p]["corner"]:
                problems.append(f"{catalog[p]['label']}: 이미 설치된 {catalog[ins]['label']}와 같은 코너({catalog[p]['corner']}) — 설치 불가")
    return problems


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


def find_multiagent_init() -> Path | None:
    """multi-agent-starter init.py 탐색. env 지정 시 그 경로만 신뢰(없으면 None — 폴백 안 함)."""
    env = os.environ.get("LOADOUT_MULTIAGENT_INIT")
    if env:
        p = Path(env).expanduser()
        return p if p.is_file() else None
    hits = sorted(Path.home().glob(".claude/plugins/**/skills/configure-multiagent/generator/init.py"))
    return hits[-1] if hits else None


def multiagent_installed(target: Path) -> bool:
    return "multiagent" in installed_names(target) or (target / "_shared" / "orchestrator-rules.md").is_file()


def install_multiagent(target: Path, dry: bool) -> str:
    """멀티에이전트 스캐폴드를 설치된 multi-agent-starter의 init.py에 위임.
    init.py가 CLAUDE.md를 통째로 쓰므로 기존 조각 블록을 회수했다가 재-append(보존)."""
    init_py = find_multiagent_init()
    if init_py is None:
        sys.exit("[error] multi-agent-starter 플러그인을 찾지 못했습니다. "
                 "먼저 설치하거나 LOADOUT_MULTIAGENT_INIT로 init.py 경로를 지정하세요.")
    instr = target / INSTRUCTION_FILE
    saved: list[str] = []
    if instr.is_file():
        text = instr.read_text(encoding="utf-8")
        for name in sorted(installed_names(target) - {"multiagent"}):
            start, end = marker(name)
            m = re.search(re.escape(start) + r".*?" + re.escape(end), text, flags=re.S)
            if m:
                saved.append(m.group(0))
    if dry:
        return f"multiagent 스캐폴드 위임 예정 ({init_py}, 보존 조각 {len(saved)}개)"
    rc = subprocess.run([sys.executable, str(init_py), "--flavor", "claude",
                         "--target", str(target), "--yes", "--no-validate"]).returncode
    if rc != 0:
        sys.exit(f"[error] init.py 실패 (exit {rc})")
    if saved:
        text = instr.read_text(encoding="utf-8").rstrip("\n")
        instr.write_text(text + "\n\n" + "\n\n".join(saved) + "\n", encoding="utf-8")
    return f"multiagent 스캐폴드 설치 (init.py 위임, 보존 조각 {len(saved)}개 재부착)"


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
    picks = list(dict.fromkeys(picks))  # 중복 pick 제거(순서 보존) — 같은 품목 2회가 배타 거부되지 않게
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

    installed = installed_names(target)
    if multiagent_installed(target):
        installed |= {"multiagent"}
    problems = check_exclusions(picks, installed, catalog)
    if problems:
        print("[배타 위반] 설치를 거부합니다 — 대상 파일은 변경되지 않았습니다:")
        for msg in problems:
            print(f"  · {msg}")
        sys.exit(2)

    if "karpathy" in picks and ("multiagent" in picks or "multiagent" in installed):
        print("  [안내] 멀티에이전트 템플릿에는 카파시 4원칙이 이미 내장 — karpathy 설치를 생략합니다.")
        picks = [p for p in picks if p != "karpathy"]

    print(f"  target : {target}")
    print(f"  담은 품목: {', '.join(catalog[p]['label'] for p in picks)}")
    if not args.yes and not args.dry_run:
        if input("\n진행할까요? [y/N]: ").strip().lower() not in ("y", "yes"):
            sys.exit("취소됨")

    prefix = "(dry) " if args.dry_run else ""
    ordered = sorted(picks, key=lambda p: 0 if catalog[p].get("scaffold") else 1)
    for p in ordered:
        if catalog[p].get("scaffold"):
            print(f"  {prefix}{install_multiagent(target, dry=args.dry_run)}")
        else:
            print(f"  {prefix}{install_fragment(target, p, dry=args.dry_run)}")
    print("\n  완료.")


if __name__ == "__main__":
    main()
