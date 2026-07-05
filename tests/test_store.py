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


def main() -> None:
    fails = catalog_checks()
    print("전부 PASS" if fails == 0 else f"{fails}개 FAIL")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
