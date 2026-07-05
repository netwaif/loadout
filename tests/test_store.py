#!/usr/bin/env python3
"""configure-store 결정적 테스트 — 외부 호출 없음."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
STORE_GEN = REPO / "plugins" / "loadout" / "skills" / "configure-store" / "generator"
STORE = STORE_GEN / "store.py"
FRAGMENTS = STORE_GEN / "fragments"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True)


def catalog_checks() -> int:
    fails = 0
    metas = {p.parent.name: json.loads(p.read_text(encoding="utf-8"))
             for p in FRAGMENTS.glob("*/meta.json") if not p.parent.name.startswith("_")}
    ok = set(metas) == {"karpathy", "fable5-solo", "multiagent", "agent-loop", "knot", "guard"}
    print(f"  {'PASS' if ok else 'FAIL'} 카탈로그 6품목"); fails += 0 if ok else 1
    avail = {n for n, m in metas.items() if m.get("available")}
    ok = avail == {"karpathy", "fable5-solo", "multiagent", "agent-loop"}
    print(f"  {'PASS' if ok else 'FAIL'} available 4품목(knot·guard=입점 예정)"); fails += 0 if ok else 1
    corners = {m["corner"] for m in metas.values()}
    ok = {"행동 규율", "실행 구조", "자율성"} <= corners
    print(f"  {'PASS' if ok else 'FAIL'} 코너 3종 존재"); fails += 0 if ok else 1
    r = run([sys.executable, str(STORE), "--list"])
    ok = r.returncode == 0 and "카파시" in r.stdout and "입점 예정" in r.stdout
    print(f"  {'PASS' if ok else 'FAIL'} --list 출력"); fails += 0 if ok else 1
    return fails


def karpathy_fragment_checks() -> int:
    fails = 0
    p = FRAGMENTS / "karpathy" / "fragment.md"
    if not p.is_file():
        print("  FAIL karpathy fragment 존재"); return 1
    frag = p.read_text(encoding="utf-8")
    ok = all(h in frag for h in ("### 1. Think Before Coding", "### 2. Simplicity First",
                                 "### 3. Surgical Changes", "### 4. Goal-Driven Execution"))
    print(f"  {'PASS' if ok else 'FAIL'} 4원칙 헤더 4종"); fails += 0 if ok else 1
    ok = "[멀티에이전트도 설치된 경우]" in frag and "[Fable5 단독도 설치된 경우]" in frag
    print(f"  {'PASS' if ok else 'FAIL'} 조건부 문단 2종"); fails += 0 if ok else 1
    ok = "andrej-karpathy-skills" in frag
    print(f"  {'PASS' if ok else 'FAIL'} 출처 표기"); fails += 0 if ok else 1
    return fails


def fragment_content_checks() -> int:
    fails = 0
    f5 = (FRAGMENTS / "fable5-solo" / "fragment.md").read_text(encoding="utf-8")
    ok = "다른 모델" in f5 and "호출하지 않는다" in f5
    print(f"  {'PASS' if ok else 'FAIL'} fable5-solo 단독 실행 명시"); fails += 0 if ok else 1
    loop = (FRAGMENTS / "agent-loop" / "fragment.md").read_text(encoding="utf-8")
    ok = all(k in loop for k in ("완료조건", "이터레이션 캡", "[멀티에이전트도 설치된 경우]", "[요금가드도 설치된 경우]"))
    print(f"  {'PASS' if ok else 'FAIL'} agent-loop 핵심 규율+조건부 2종"); fails += 0 if ok else 1
    ok = all((FRAGMENTS / "agent-loop" / "files" / "prep" / n).is_file()
             for n in ("goal-prompt.template.md", "채점표.template.md"))
    print(f"  {'PASS' if ok else 'FAIL'} agent-loop 딸린 파일 2장"); fails += 0 if ok else 1
    ok = all((FRAGMENTS / "_TEMPLATE" / n).is_file() for n in ("meta.json", "fragment.md", "README.md"))
    print(f"  {'PASS' if ok else 'FAIL'} 입점 양식 _TEMPLATE"); fails += 0 if ok else 1
    return fails


def main() -> None:
    fails = catalog_checks()
    fails += karpathy_fragment_checks()
    fails += fragment_content_checks()
    print("전부 PASS" if fails == 0 else f"{fails}개 FAIL")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
