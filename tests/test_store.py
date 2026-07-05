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
KARPATHY_START, KARPATHY_END = "<!-- store:karpathy:start -->", "<!-- store:karpathy:end -->"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True)


FAKE_INIT = '''#!/usr/bin/env python3
import argparse, pathlib
ap = argparse.ArgumentParser()
ap.add_argument("--flavor"); ap.add_argument("--target")
ap.add_argument("--yes", action="store_true"); ap.add_argument("--no-validate", action="store_true")
a = ap.parse_args()
t = pathlib.Path(a.target); (t / "_shared").mkdir(parents=True, exist_ok=True)
(t / "_shared" / "orchestrator-rules.md").write_text("stub", encoding="utf-8")
(t / "CLAUDE.md").write_text("# MultiAgent stub CLAUDE.md\\n", encoding="utf-8")
'''


def run_env(args: list[str], env_extra: dict) -> subprocess.CompletedProcess:
    import os
    env = dict(os.environ); env.update(env_extra)
    return subprocess.run(args, capture_output=True, text=True, env=env)


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


def install_checks() -> int:
    fails = 0
    with tempfile.TemporaryDirectory() as d:
        tgt = Path(d) / "t1"
        r = run([sys.executable, str(STORE), "--target", str(tgt), "--pick", "karpathy", "--yes"])
        text = (tgt / "CLAUDE.md").read_text(encoding="utf-8") if (tgt / "CLAUDE.md").is_file() else ""
        ok = r.returncode == 0 and KARPATHY_START in text and KARPATHY_END in text
        print(f"  {'PASS' if ok else 'FAIL'} 단일 조각 설치(마커)"); fails += 0 if ok else 1
        run([sys.executable, str(STORE), "--target", str(tgt), "--pick", "karpathy", "--yes"])
        text2 = (tgt / "CLAUDE.md").read_text(encoding="utf-8")
        ok = text2.count(KARPATHY_START) == 1
        print(f"  {'PASS' if ok else 'FAIL'} 멱등(재설치=교체 1회)"); fails += 0 if ok else 1
        run([sys.executable, str(STORE), "--target", str(tgt), "--pick", "agent-loop", "--yes"])
        ok = (tgt / "prep" / "goal-prompt.template.md").is_file() and (tgt / "prep" / "채점표.template.md").is_file()
        print(f"  {'PASS' if ok else 'FAIL'} 딸린 파일 prep/ 복사"); fails += 0 if ok else 1
        r = run([sys.executable, str(STORE), "--target", str(tgt), "--pick", "knot", "--yes"])
        ok = r.returncode == 2
        print(f"  {'PASS' if ok else 'FAIL'} 입점 예정 pick 거부(exit 2)"); fails += 0 if ok else 1
    return fails


def exclusion_checks() -> int:
    fails = 0
    with tempfile.TemporaryDirectory() as d:
        tgt = Path(d) / "t2"
        r = run([sys.executable, str(STORE), "--target", str(tgt),
                 "--pick", "fable5-solo,multiagent", "--yes"])
        ok = r.returncode == 2 and not (tgt / "CLAUDE.md").is_file()
        print(f"  {'PASS' if ok else 'FAIL'} 픽 내 배타(동시) 거부+무변경"); fails += 0 if ok else 1
        run([sys.executable, str(STORE), "--target", str(tgt), "--pick", "fable5-solo", "--yes"])
        before = (tgt / "CLAUDE.md").read_text(encoding="utf-8")
        r = run([sys.executable, str(STORE), "--target", str(tgt), "--pick", "multiagent", "--yes"])
        after = (tgt / "CLAUDE.md").read_text(encoding="utf-8")
        ok = r.returncode == 2 and before == after
        print(f"  {'PASS' if ok else 'FAIL'} 기설치 배타(추가) 거부+무변경"); fails += 0 if ok else 1
        r = run([sys.executable, str(STORE), "--target", str(tgt), "--pick", "fable5-solo", "--yes"])
        ok = r.returncode == 0
        print(f"  {'PASS' if ok else 'FAIL'} 동일 품목 재설치는 허용(멱등)"); fails += 0 if ok else 1
    return fails


def resub_escape_checks() -> int:
    """재설치(교체 경로)에서 조각 본문의 backslash escape(\\g, \\\\)가 byte-exact로 보존되는지."""
    fails = 0
    import importlib.util
    spec = importlib.util.spec_from_file_location("store", STORE)
    store = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(store)
    with tempfile.TemporaryDirectory() as d:
        frag_root = Path(d) / "fragments"
        (frag_root / "esc").mkdir(parents=True)
        body = "## esc\n\n정규식 예시: `\\g<0>` 와 백슬래시 \\\\ 두 개.\n"
        (frag_root / "esc" / "fragment.md").write_text(body, encoding="utf-8")
        store.FRAGMENTS_DIR = frag_root
        tgt = Path(d) / "t"
        store.install_fragment(tgt, "esc", dry=False)   # append 경로
        store.install_fragment(tgt, "esc", dry=False)   # 교체 경로(위험 지점)
        text = (tgt / "CLAUDE.md").read_text(encoding="utf-8")
        ok = body.strip("\n") in text and text.count("<!-- store:esc:start -->") == 1
        print(f"  {'PASS' if ok else 'FAIL'} 교체 경로 backslash byte-exact"); fails += 0 if ok else 1
    return fails


def multiagent_checks() -> int:
    fails = 0
    with tempfile.TemporaryDirectory() as d:
        fake = Path(d) / "fake_init.py"; fake.write_text(FAKE_INIT, encoding="utf-8")
        env = {"LOADOUT_MULTIAGENT_INIT": str(fake)}
        tgt = Path(d) / "t3"
        r = run_env([sys.executable, str(STORE), "--target", str(tgt),
                     "--pick", "multiagent,agent-loop", "--yes"], env)
        text = (tgt / "CLAUDE.md").read_text(encoding="utf-8")
        ok = (r.returncode == 0 and "MultiAgent stub" in text
              and "<!-- store:agent-loop:start -->" in text
              and (tgt / "_shared" / "orchestrator-rules.md").is_file())
        print(f"  {'PASS' if ok else 'FAIL'} 멀티 위임 + 조각 공존"); fails += 0 if ok else 1
        # 나중 멀티 추가 시 기존 조각 보존
        tgt2 = Path(d) / "t4"
        run_env([sys.executable, str(STORE), "--target", str(tgt2), "--pick", "agent-loop", "--yes"], env)
        run_env([sys.executable, str(STORE), "--target", str(tgt2), "--pick", "multiagent", "--yes"], env)
        text = (tgt2 / "CLAUDE.md").read_text(encoding="utf-8")
        ok = "MultiAgent stub" in text and text.count("<!-- store:agent-loop:start -->") == 1
        print(f"  {'PASS' if ok else 'FAIL'} 나중 멀티 추가 시 기존 조각 보존"); fails += 0 if ok else 1
        # karpathy×멀티 = 생략 안내
        r = run_env([sys.executable, str(STORE), "--target", str(tgt2), "--pick", "karpathy", "--yes"], env)
        text = (tgt2 / "CLAUDE.md").read_text(encoding="utf-8")
        ok = r.returncode == 0 and "<!-- store:karpathy:start -->" not in text and "내장" in r.stdout
        print(f"  {'PASS' if ok else 'FAIL'} karpathy×멀티=생략 안내"); fails += 0 if ok else 1
        # 멀티 스캐폴드 위에 fable5-solo 추가 → 배타 거부(휴리스틱 감지)
        r = run_env([sys.executable, str(STORE), "--target", str(tgt2), "--pick", "fable5-solo", "--yes"], env)
        ok = r.returncode == 2
        print(f"  {'PASS' if ok else 'FAIL'} 멀티(휴리스틱)↔fable5 배타 거부"); fails += 0 if ok else 1
        # init.py 미발견 → 명확한 에러
        r = run_env([sys.executable, str(STORE), "--target", str(Path(d) / "t5"),
                     "--pick", "multiagent", "--yes"], {"LOADOUT_MULTIAGENT_INIT": str(Path(d) / "none.py")})
        ok = r.returncode != 0 and "multi-agent-starter" in (r.stdout + r.stderr)
        print(f"  {'PASS' if ok else 'FAIL'} init.py 미발견 시 안내 에러"); fails += 0 if ok else 1
    return fails


def main() -> None:
    fails = catalog_checks()
    fails += karpathy_fragment_checks()
    fails += fragment_content_checks()
    fails += install_checks()
    fails += exclusion_checks()
    fails += resub_escape_checks()
    fails += multiagent_checks()
    print("전부 PASS" if fails == 0 else f"{fails}개 FAIL")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
