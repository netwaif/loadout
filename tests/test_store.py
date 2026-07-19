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
fname = "AGENTS.md" if a.flavor == "codex" else "CLAUDE.md"
(t / fname).write_text(f"# MultiAgent stub {a.flavor}\\n", encoding="utf-8")
'''


FAKE_INIT_FAIL = '''#!/usr/bin/env python3
import argparse, pathlib, sys
ap = argparse.ArgumentParser()
ap.add_argument("--flavor"); ap.add_argument("--target")
ap.add_argument("--yes", action="store_true"); ap.add_argument("--no-validate", action="store_true")
a = ap.parse_args()
t = pathlib.Path(a.target); t.mkdir(parents=True, exist_ok=True)
(t / "CLAUDE.md").write_text("# half-written\\n", encoding="utf-8")
sys.exit(3)
'''


def run_env(args: list[str], env_extra: dict) -> subprocess.CompletedProcess:
    import os
    env = dict(os.environ); env.update(env_extra)
    return subprocess.run(args, capture_output=True, text=True, env=env)


def catalog_checks() -> int:
    fails = 0
    metas = {p.parent.name: json.loads(p.read_text(encoding="utf-8"))
             for p in FRAGMENTS.glob("*/meta.json") if not p.parent.name.startswith("_")}
    all_items = {"karpathy", "fable5-solo", "fable5-lowcost", "multiagent",
                 "agent-loop", "knot", "guard", "session-handoff", "no-yesman"}
    ok = set(metas) == all_items
    print(f"  {'PASS' if ok else 'FAIL'} 카탈로그 9품목"); fails += 0 if ok else 1
    avail = {n for n, m in metas.items() if m.get("available")}
    ok = avail == all_items
    print(f"  {'PASS' if ok else 'FAIL'} available 9품목(전 품목 구매 가능)"); fails += 0 if ok else 1
    corners = {m["corner"] for m in metas.values()}
    ok = {"행동 규율", "실행 구조", "자율성"} <= corners
    print(f"  {'PASS' if ok else 'FAIL'} 코너 3종 존재"); fails += 0 if ok else 1
    r = run([sys.executable, str(STORE), "--list"])
    ok = r.returncode == 0 and "카파시" in r.stdout and "코너" in r.stdout
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
        before = (tgt / "CLAUDE.md").read_text(encoding="utf-8")
        r = run([sys.executable, str(STORE), "--target", str(tgt), "--pick", "no-such-item", "--yes"])
        ok = r.returncode == 2 and (tgt / "CLAUDE.md").read_text(encoding="utf-8") == before
        print(f"  {'PASS' if ok else 'FAIL'} 없는 품목 거부(exit 2)+무변경"); fails += 0 if ok else 1
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
        (frag_root / "esc" / "meta.json").write_text('{"label": "esc", "corner": "t", "available": true}', encoding="utf-8")
        store.FRAGMENTS_DIR = frag_root
        tgt = Path(d) / "t"
        store.install_fragment(tgt, "esc", dry=False)   # append 경로
        store.install_fragment(tgt, "esc", dry=False)   # 교체 경로(위험 지점)
        text = (tgt / "CLAUDE.md").read_text(encoding="utf-8")
        ok = body.strip("\n") in text and text.count("<!-- store:esc:start -->") == 1
        print(f"  {'PASS' if ok else 'FAIL'} 교체 경로 backslash byte-exact"); fails += 0 if ok else 1
    return fails


def knot_checks() -> int:
    fails = 0
    with tempfile.TemporaryDirectory() as d:
        tgt = Path(d) / "k1"
        r = run([sys.executable, str(STORE), "--target", str(tgt), "--pick", "knot", "--yes"])
        text = (tgt / "CLAUDE.md").read_text(encoding="utf-8")
        ok = r.returncode == 0 and "<!-- store:knot:start -->" in text and "KNOT_VAULT" in text
        print(f"  {'PASS' if ok else 'FAIL'} knot 조각 설치"); fails += 0 if ok else 1
        tgt2 = Path(d) / "k2"; tgt2.mkdir(parents=True)
        (tgt2 / "CLAUDE.md").write_text("# x\n<!-- knot:start -->\nold\n<!-- knot:end -->\n", encoding="utf-8")
        r = run([sys.executable, str(STORE), "--target", str(tgt2), "--pick", "knot", "--yes"])
        text = (tgt2 / "CLAUDE.md").read_text(encoding="utf-8")
        ok = r.returncode == 0 and "<!-- store:knot:start -->" not in text and "생략" in r.stdout
        print(f"  {'PASS' if ok else 'FAIL'} 기존 --with-knot 블록 감지 시 생략"); fails += 0 if ok else 1
    return fails


def guard_checks() -> int:
    fails = 0
    with tempfile.TemporaryDirectory() as d:
        tgt = Path(d) / "g1"
        run([sys.executable, str(STORE), "--target", str(tgt), "--pick", "guard", "--yes"])
        s = tgt / ".claude" / "settings.json"
        data = json.loads(s.read_text(encoding="utf-8"))
        stops = data.get("hooks", {}).get("Stop", [])
        ok = sum("coach --hook" in json.dumps(e) for e in stops) == 1
        print(f"  {'PASS' if ok else 'FAIL'} guard Stop 훅 주입"); fails += 0 if ok else 1
        text = (tgt / "CLAUDE.md").read_text(encoding="utf-8")
        ok = "<!-- store:guard:start -->" in text
        print(f"  {'PASS' if ok else 'FAIL'} guard CLAUDE.md 조각"); fails += 0 if ok else 1
        run([sys.executable, str(STORE), "--target", str(tgt), "--pick", "guard", "--yes"])
        data = json.loads(s.read_text(encoding="utf-8"))
        ok = sum("coach --hook" in json.dumps(e) for e in data["hooks"]["Stop"]) == 1
        print(f"  {'PASS' if ok else 'FAIL'} 훅 멱등(재설치=1개)"); fails += 0 if ok else 1
        tgt2 = Path(d) / "g2"; (tgt2 / ".claude").mkdir(parents=True)
        (tgt2 / ".claude" / "settings.json").write_text(
            '{"hooks": {"Stop": [{"type": "command", "command": "echo user-own"}]}}', encoding="utf-8")
        run([sys.executable, str(STORE), "--target", str(tgt2), "--pick", "guard", "--yes"])
        data = json.loads((tgt2 / ".claude" / "settings.json").read_text(encoding="utf-8"))
        cmds = json.dumps(data["hooks"]["Stop"])
        ok = "user-own" in cmds and "coach --hook" in cmds
        print(f"  {'PASS' if ok else 'FAIL'} 사용자 기존 훅 보존"); fails += 0 if ok else 1
        tgt3 = Path(d) / "g3"
        run([sys.executable, str(STORE), "--target", str(tgt3), "--pick", "guard", "--yes", "--dry-run"])
        ok = not (tgt3 / ".claude" / "settings.json").is_file() and not (tgt3 / "CLAUDE.md").is_file()
        print(f"  {'PASS' if ok else 'FAIL'} dry-run 무변경"); fails += 0 if ok else 1
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


def multiagent_safety_checks() -> int:
    fails = 0
    with tempfile.TemporaryDirectory() as d:
        fake = Path(d) / "fake_init.py"; fake.write_text(FAKE_INIT, encoding="utf-8")
        fake_fail = Path(d) / "fake_init_fail.py"; fake_fail.write_text(FAKE_INIT_FAIL, encoding="utf-8")
        env = {"LOADOUT_MULTIAGENT_INIT": str(fake)}
        env_fail = {"LOADOUT_MULTIAGENT_INIT": str(fake_fail)}
        # 1. karpathy 선설치 → 나중 멀티 추가 시 karpathy 재부착 차단 + 안내
        t1 = Path(d) / "s1"
        run([sys.executable, str(STORE), "--target", str(t1), "--pick", "karpathy", "--yes"])
        r = run_env([sys.executable, str(STORE), "--target", str(t1), "--pick", "multiagent", "--yes"], env)
        text = (t1 / "CLAUDE.md").read_text(encoding="utf-8")
        ok = (r.returncode == 0 and text.count(KARPATHY_START) == 0
              and "재부착하지 않습니다" in r.stdout and "MultiAgent stub" in text)
        print(f"  {'PASS' if ok else 'FAIL'} karpathy 선설치→멀티 추가 시 재부착 차단+안내"); fails += 0 if ok else 1
        # 2. 손글씨 CLAUDE.md → [주의] 경고 + 백업에 원문 보존
        t2 = Path(d) / "s2"; t2.mkdir(parents=True)
        (t2 / "CLAUDE.md").write_text("# my rules\n", encoding="utf-8")
        r = run_env([sys.executable, str(STORE), "--target", str(t2), "--pick", "multiagent", "--yes"], env)
        bak = t2 / "CLAUDE.md.loadout-bak"
        ok = (r.returncode == 0 and "[주의]" in r.stdout
              and bak.is_file() and bak.read_text(encoding="utf-8") == "# my rules\n")
        print(f"  {'PASS' if ok else 'FAIL'} 비-store 본문 경고+백업 원문 보존"); fails += 0 if ok else 1
        # 3. init.py 실패(rc≠0) → 백업 경로 안내 + 회수 조각이 백업에 살아있음
        t3 = Path(d) / "s3"
        run([sys.executable, str(STORE), "--target", str(t3), "--pick", "agent-loop", "--yes"])
        r = run_env([sys.executable, str(STORE), "--target", str(t3), "--pick", "multiagent", "--yes"], env_fail)
        bak = t3 / "CLAUDE.md.loadout-bak"
        ok = (r.returncode != 0 and "loadout-bak" in (r.stdout + r.stderr)
              and bak.is_file() and "<!-- store:agent-loop:start -->" in bak.read_text(encoding="utf-8"))
        print(f"  {'PASS' if ok else 'FAIL'} init.py 실패 시 백업 안내+조각 보존"); fails += 0 if ok else 1
        # 4. dry-run은 백업 파일을 만들지 않음
        t4 = Path(d) / "s4"
        run([sys.executable, str(STORE), "--target", str(t4), "--pick", "agent-loop", "--yes"])
        r = run_env([sys.executable, str(STORE), "--target", str(t4),
                     "--pick", "multiagent", "--yes", "--dry-run"], env)
        ok = r.returncode == 0 and not (t4 / "CLAUDE.md.loadout-bak").is_file()
        print(f"  {'PASS' if ok else 'FAIL'} dry-run은 백업 미생성"); fails += 0 if ok else 1
    return fails


def flavor_checks() -> int:
    fails = 0
    with tempfile.TemporaryDirectory() as d:
        # codex flavor → AGENTS.md에 설치, CLAUDE.md는 안 만듦
        tgt = Path(d) / "f1"
        r = run([sys.executable, str(STORE), "--target", str(tgt), "--pick", "karpathy",
                 "--flavor", "codex", "--yes"])
        text = (tgt / "AGENTS.md").read_text(encoding="utf-8") if (tgt / "AGENTS.md").is_file() else ""
        ok = r.returncode == 0 and KARPATHY_START in text and not (tgt / "CLAUDE.md").is_file()
        print(f"  {'PASS' if ok else 'FAIL'} codex flavor=AGENTS.md 설치"); fails += 0 if ok else 1
        # multiagent 위임에 flavor 전달
        fake = Path(d) / "fake_init.py"; fake.write_text(FAKE_INIT, encoding="utf-8")
        env = {"LOADOUT_MULTIAGENT_INIT": str(fake)}
        tgt2 = Path(d) / "f2"
        r = run_env([sys.executable, str(STORE), "--target", str(tgt2), "--pick", "multiagent,agent-loop",
                     "--flavor", "codex", "--yes"], env)
        text = (tgt2 / "AGENTS.md").read_text(encoding="utf-8") if (tgt2 / "AGENTS.md").is_file() else ""
        ok = (r.returncode == 0 and "MultiAgent stub codex" in text
              and "<!-- store:agent-loop:start -->" in text)
        print(f"  {'PASS' if ok else 'FAIL'} 멀티 위임에 flavor 전달+조각 공존(AGENTS.md)"); fails += 0 if ok else 1
        # cross-flavor 배타: CLAUDE.md에 fable5-solo → AGENTS.md에 multiagent 거부
        tgt3 = Path(d) / "f3"
        run([sys.executable, str(STORE), "--target", str(tgt3), "--pick", "fable5-solo", "--yes"])
        r = run_env([sys.executable, str(STORE), "--target", str(tgt3), "--pick", "multiagent",
                     "--flavor", "codex", "--yes"], env)
        ok = r.returncode == 2 and not (tgt3 / "AGENTS.md").is_file()
        print(f"  {'PASS' if ok else 'FAIL'} cross-flavor 코너 배타 거부"); fails += 0 if ok else 1
        # cross-flavor 동일 품목은 허용(양쪽 하네스에 같은 규율)
        tgt4 = Path(d) / "f4"
        run([sys.executable, str(STORE), "--target", str(tgt4), "--pick", "karpathy", "--yes"])
        r = run([sys.executable, str(STORE), "--target", str(tgt4), "--pick", "karpathy",
                 "--flavor", "codex", "--yes"])
        ok = (r.returncode == 0 and (tgt4 / "AGENTS.md").is_file()
              and KARPATHY_START in (tgt4 / "AGENTS.md").read_text(encoding="utf-8"))
        print(f"  {'PASS' if ok else 'FAIL'} cross-flavor 동일 품목 허용"); fails += 0 if ok else 1
        # claude 전용 품목(fable5-solo)은 codex flavor 거부 + 무변경
        tgt5 = Path(d) / "f5"
        r = run([sys.executable, str(STORE), "--target", str(tgt5), "--pick", "fable5-solo",
                 "--flavor", "codex", "--yes"])
        ok = r.returncode == 2 and "전용 품목" in r.stdout and not (tgt5 / "AGENTS.md").is_file()
        print(f"  {'PASS' if ok else 'FAIL'} claude 전용 품목 codex 거부+무변경"); fails += 0 if ok else 1
        r = run([sys.executable, str(STORE), "--target", str(tgt5), "--pick", "fable5-solo", "--yes"])
        ok = r.returncode == 0 and (tgt5 / "CLAUDE.md").is_file()
        print(f"  {'PASS' if ok else 'FAIL'} 같은 품목 claude 설치는 정상"); fails += 0 if ok else 1
        # 저비용 Fable5는 codex에서 GPT 5.6 번안(fragment.codex.md)으로 설치
        tgt6 = Path(d) / "f6"
        r = run([sys.executable, str(STORE), "--target", str(tgt6), "--pick", "fable5-lowcost",
                 "--flavor", "codex", "--yes"])
        text = (tgt6 / "AGENTS.md").read_text(encoding="utf-8") if (tgt6 / "AGENTS.md").is_file() else ""
        ok = r.returncode == 0 and "저비용 GPT 5.6" in text and "Fable 5는 가장 비싼" not in text
        print(f"  {'PASS' if ok else 'FAIL'} lowcost codex=GPT 5.6 번안 설치"); fails += 0 if ok else 1
        run([sys.executable, str(STORE), "--target", str(tgt6), "--pick", "fable5-lowcost", "--yes"])
        text = (tgt6 / "CLAUDE.md").read_text(encoding="utf-8")
        ok = "저비용 Fable 5" in text and "GPT 5.6" not in text
        print(f"  {'PASS' if ok else 'FAIL'} lowcost claude=Fable5 원본 유지"); fails += 0 if ok else 1
        # codex flavor 카탈로그 라벨 = label_codex (저비용 GPT 5.6), 기본은 원본 라벨
        r = run([sys.executable, str(STORE), "--list", "--flavor", "codex"])
        ok = "저비용 GPT 5.6" in r.stdout and "저비용 Fable 5" not in r.stdout
        print(f"  {'PASS' if ok else 'FAIL'} codex --list 라벨=저비용 GPT 5.6"); fails += 0 if ok else 1
        r = run([sys.executable, str(STORE), "--list"])
        ok = "저비용 Fable 5" in r.stdout
        print(f"  {'PASS' if ok else 'FAIL'} 기본 --list 라벨=저비용 Fable 5"); fails += 0 if ok else 1
        # doctor: claude 전용 마커가 AGENTS.md에 있으면 WARN
        (tgt6 / "AGENTS.md").write_text(
            (tgt6 / "AGENTS.md").read_text(encoding="utf-8")
            + "\n<!-- store:fable5-solo:start -->\n수동 삽입\n<!-- store:fable5-solo:end -->\n",
            encoding="utf-8")
        r = run([sys.executable, str(STORE), "--target", str(tgt6), "--doctor"])
        ok = "전용 품목" in r.stdout
        print(f"  {'PASS' if ok else 'FAIL'} doctor: 전용 품목 오설치=WARN"); fails += 0 if ok else 1
    return fails


def codex_guard_checks() -> int:
    """guard × codex flavor — 워처는 loadout 동봉(files.codex/)이 정본, starter 불필요."""
    fails = 0
    canon = FRAGMENTS / "guard" / "files.codex" / "_shared" / "guard"
    with tempfile.TemporaryDirectory() as d:
        tgt = Path(d) / "cg1"
        r = run([sys.executable, str(STORE), "--target", str(tgt), "--pick", "guard",
                 "--flavor", "codex", "--yes"])
        text = (tgt / "AGENTS.md").read_text(encoding="utf-8") if (tgt / "AGENTS.md").is_file() else ""
        ok = (r.returncode == 0 and "<!-- store:guard:start -->" in text
              and "codex_goal_watch.mjs" in text)
        print(f"  {'PASS' if ok else 'FAIL'} codex guard=fragment.codex.md 설치(starter 불필요)"); fails += 0 if ok else 1
        w, rd = tgt / "_shared" / "guard" / "codex_goal_watch.mjs", tgt / "_shared" / "guard" / "README.md"
        ok = (w.is_file() and rd.is_file()
              and w.read_bytes() == (canon / "codex_goal_watch.mjs").read_bytes())
        print(f"  {'PASS' if ok else 'FAIL'} 동봉 워처+README 복사(정본 바이트 일치)"); fails += 0 if ok else 1
        ok = not (tgt / ".claude" / "settings.json").is_file()
        print(f"  {'PASS' if ok else 'FAIL'} codex에선 claude 훅 미주입"); fails += 0 if ok else 1
        # claude flavor guard는 워처를 복사하지 않음(files.codex는 codex 전용)
        tgt2 = Path(d) / "cg2"
        run([sys.executable, str(STORE), "--target", str(tgt2), "--pick", "guard", "--yes"])
        ok = (tgt2 / ".claude" / "settings.json").is_file() and not (tgt2 / "_shared").exists()
        print(f"  {'PASS' if ok else 'FAIL'} claude에선 워처 미복사"); fails += 0 if ok else 1
        # dry-run은 워처 미복사
        tgt3 = Path(d) / "cg3"
        r = run([sys.executable, str(STORE), "--target", str(tgt3), "--pick", "guard",
                 "--flavor", "codex", "--yes", "--dry-run"])
        ok = r.returncode == 0 and not (tgt3 / "_shared").exists() and not (tgt3 / "AGENTS.md").is_file()
        print(f"  {'PASS' if ok else 'FAIL'} dry-run 무변경(워처 포함)"); fails += 0 if ok else 1
    return fails


def doctor_checks() -> int:
    fails = 0
    with tempfile.TemporaryDirectory() as d:
        # 정상 설치 → exit 0, FAIL 없음, 파일 무변경(읽기 전용)
        tgt = Path(d) / "d1"
        run([sys.executable, str(STORE), "--target", str(tgt), "--pick", "karpathy,agent-loop", "--yes"])
        before = (tgt / "CLAUDE.md").read_text(encoding="utf-8")
        r = run([sys.executable, str(STORE), "--target", str(tgt), "--doctor"])
        after = (tgt / "CLAUDE.md").read_text(encoding="utf-8")
        ok = r.returncode == 0 and "[FAIL]" not in r.stdout and before == after
        print(f"  {'PASS' if ok else 'FAIL'} doctor 정상=exit 0+무변경"); fails += 0 if ok else 1
        # 마커 짝 깨짐 → exit 1
        tgt2 = Path(d) / "d2"; tgt2.mkdir(parents=True)
        (tgt2 / "CLAUDE.md").write_text("# x\n<!-- store:karpathy:start -->\n본문\n", encoding="utf-8")
        r = run([sys.executable, str(STORE), "--target", str(tgt2), "--doctor"])
        ok = r.returncode == 1 and "짝 깨짐" in r.stdout
        print(f"  {'PASS' if ok else 'FAIL'} 마커 짝 깨짐=FAIL exit 1"); fails += 0 if ok else 1
        # 손편집 stale → WARN(exit 0)
        tgt3 = Path(d) / "d3"
        run([sys.executable, str(STORE), "--target", str(tgt3), "--pick", "karpathy", "--yes"])
        p = tgt3 / "CLAUDE.md"
        p.write_text(p.read_text(encoding="utf-8").replace("### 1. Think Before Coding", "### 1. 변조됨"),
                     encoding="utf-8")
        r = run([sys.executable, str(STORE), "--target", str(tgt3), "--doctor"])
        ok = r.returncode == 0 and "최신본과 다름" in r.stdout
        print(f"  {'PASS' if ok else 'FAIL'} stale 조각=WARN"); fails += 0 if ok else 1
        # 수동 편집으로 생긴 코너 배타 위반 → FAIL
        tgt4 = Path(d) / "d4"
        run([sys.executable, str(STORE), "--target", str(tgt4), "--pick", "fable5-solo", "--yes"])
        p = tgt4 / "CLAUDE.md"
        p.write_text(p.read_text(encoding="utf-8")
                     + "\n<!-- store:multiagent:start -->\n수동 삽입\n<!-- store:multiagent:end -->\n",
                     encoding="utf-8")
        r = run([sys.executable, str(STORE), "--target", str(tgt4), "--doctor"])
        ok = r.returncode == 1 and "같은 코너" in r.stdout
        print(f"  {'PASS' if ok else 'FAIL'} 코너 배타 위반=FAIL"); fails += 0 if ok else 1
        # 딸린 파일 유실 → WARN
        tgt5 = Path(d) / "d5"
        run([sys.executable, str(STORE), "--target", str(tgt5), "--pick", "agent-loop", "--yes"])
        (tgt5 / "prep" / "goal-prompt.template.md").unlink()
        r = run([sys.executable, str(STORE), "--target", str(tgt5), "--doctor"])
        ok = r.returncode == 0 and "딸린 파일 유실" in r.stdout
        print(f"  {'PASS' if ok else 'FAIL'} 딸린 파일 유실=WARN"); fails += 0 if ok else 1
        # guard(claude) 훅 배선 끊김 → WARN
        tgt6 = Path(d) / "d6"
        run([sys.executable, str(STORE), "--target", str(tgt6), "--pick", "guard", "--yes"])
        (tgt6 / ".claude" / "settings.json").unlink()
        r = run([sys.executable, str(STORE), "--target", str(tgt6), "--doctor"])
        ok = r.returncode == 0 and "Stop 훅 없음" in r.stdout
        print(f"  {'PASS' if ok else 'FAIL'} guard 훅 끊김=WARN"); fails += 0 if ok else 1
        # 빈 폴더 → exit 0
        r = run([sys.executable, str(STORE), "--target", str(Path(d) / "empty"), "--doctor"])
        ok = r.returncode == 0
        print(f"  {'PASS' if ok else 'FAIL'} 빈 폴더=exit 0"); fails += 0 if ok else 1
        # end가 start보다 먼저(개수는 짝) → FAIL exit 1
        tgt7 = Path(d) / "d7"; tgt7.mkdir(parents=True)
        (tgt7 / "CLAUDE.md").write_text(
            "<!-- store:karpathy:end -->\n본문\n<!-- store:karpathy:start -->\n", encoding="utf-8")
        r = run([sys.executable, str(STORE), "--target", str(tgt7), "--doctor"])
        ok = r.returncode == 1 and "순서·교차" in r.stdout
        print(f"  {'PASS' if ok else 'FAIL'} end-before-start=FAIL"); fails += 0 if ok else 1
        # 교차 중첩(a:start b:start a:end b:end) → FAIL exit 1
        tgt8 = Path(d) / "d8"; tgt8.mkdir(parents=True)
        (tgt8 / "CLAUDE.md").write_text(
            "<!-- store:karpathy:start -->\nA\n<!-- store:knot:start -->\nB\n"
            "<!-- store:karpathy:end -->\nC\n<!-- store:knot:end -->\n", encoding="utf-8")
        r = run([sys.executable, str(STORE), "--target", str(tgt8), "--doctor"])
        ok = r.returncode == 1 and "순서·교차" in r.stdout
        print(f"  {'PASS' if ok else 'FAIL'} 교차 중첩=FAIL"); fails += 0 if ok else 1
        # codex guard: README 유실 → WARN(딸린 파일) / 워처 변조 → WARN(정본 불일치) / 조각 변조 → WARN(stale)
        tgt9 = Path(d) / "d9"
        run([sys.executable, str(STORE), "--target", str(tgt9), "--pick", "guard",
             "--flavor", "codex", "--yes"])
        (tgt9 / "_shared" / "guard" / "README.md").unlink()
        r = run([sys.executable, str(STORE), "--target", str(tgt9), "--doctor"])
        ok = r.returncode == 0 and "README.md" in r.stdout and "재설치 권장" in r.stdout
        print(f"  {'PASS' if ok else 'FAIL'} codex guard README 유실=WARN"); fails += 0 if ok else 1
        w = tgt9 / "_shared" / "guard" / "codex_goal_watch.mjs"
        w.write_text(w.read_text(encoding="utf-8") + "\n// 변조\n", encoding="utf-8")
        r = run([sys.executable, str(STORE), "--target", str(tgt9), "--doctor"])
        ok = r.returncode == 0 and "정본과 불일치" in r.stdout
        print(f"  {'PASS' if ok else 'FAIL'} 워처 변조=WARN(정본 바이트 대조)"); fails += 0 if ok else 1
        p = tgt9 / "AGENTS.md"
        p.write_text(p.read_text(encoding="utf-8").replace("goal 요금가드 (Codex)", "변조됨"), encoding="utf-8")
        r = run([sys.executable, str(STORE), "--target", str(tgt9), "--doctor"])
        ok = r.returncode == 0 and "최신본과 다름" in r.stdout
        print(f"  {'PASS' if ok else 'FAIL'} codex 변형 stale=WARN(fragment.codex.md 대조)"); fails += 0 if ok else 1
        # claude guard: 훅 변조 → WARN(hook.json 정본 대조)
        tgt10 = Path(d) / "d10"
        run([sys.executable, str(STORE), "--target", str(tgt10), "--pick", "guard", "--yes"])
        s = tgt10 / ".claude" / "settings.json"
        s.write_text(s.read_text(encoding="utf-8").replace("coach --hook", "coach --hook --tampered"),
                     encoding="utf-8")
        r = run([sys.executable, str(STORE), "--target", str(tgt10), "--doctor"])
        ok = r.returncode == 0 and "정본과 불일치" in r.stdout
        print(f"  {'PASS' if ok else 'FAIL'} claude 훅 변조=WARN(hook.json 정본 대조)"); fails += 0 if ok else 1
    return fails


def main() -> None:
    fails = catalog_checks()
    fails += karpathy_fragment_checks()
    fails += fragment_content_checks()
    fails += install_checks()
    fails += exclusion_checks()
    fails += resub_escape_checks()
    fails += knot_checks()
    fails += guard_checks()
    fails += multiagent_checks()
    fails += multiagent_safety_checks()
    fails += flavor_checks()
    fails += codex_guard_checks()
    fails += doctor_checks()
    print("전부 PASS" if fails == 0 else f"{fails}개 FAIL")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
