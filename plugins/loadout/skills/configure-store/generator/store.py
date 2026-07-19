#!/usr/bin/env python3
"""CLAUDE.md 구성 백화점 — 결정적 조각 설치기.

카탈로그의 구성 조각(fragment)을 골라 대상 폴더 지침 파일에 마커 기반으로
멱등 append 한다. 멀티에이전트 품목만 configure-multiagent init.py에 스캐폴드 위임.
- 결정적: 번들 조각을 그대로 삽입. LLM 자유작문 없음.
- 배타: 같은 corner 품목 동시/중복 설치를 설치 시점에 거부(exit 2).
- flavor: claude(CLAUDE.md, 기본) | codex(AGENTS.md). 조각은 순수 마크다운(벤더 중립),
  flavor별 문구가 필요한 조각만 fragment.codex.md 변형을 둔다.

사용:
    python3 store.py --list
    python3 store.py --target ~/work/my-folder --pick karpathy,fable5-solo --yes
    python3 store.py --target ~/work/my-folder --pick guard --flavor codex --yes
    python3 store.py --target ~/work/my-folder --remove karpathy --yes
    python3 store.py --target ~/work/my-folder --remove fable5-solo --pick multiagent --yes  # 코너 스왑
    python3 store.py --target ~/work/my-folder --doctor
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
FLAVOR_FILES = {"claude": "CLAUDE.md", "codex": "AGENTS.md"}
FLAVOR = "claude"                # main()에서 --flavor로 설정
INSTRUCTION_FILE = "CLAUDE.md"   # FLAVOR_FILES[FLAVOR]와 동기


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


def flavor_label(m: dict) -> str:
    """flavor별 표시명 — codex에서 label_codex가 있으면 그걸 사용(예: 저비용 Fable 5 → 저비용 GPT 5.6)."""
    if FLAVOR == "codex" and m.get("label_codex"):
        return m["label_codex"]
    return m["label"]


def print_catalog(catalog: dict[str, dict]) -> None:
    print("CLAUDE.md 구성 백화점 — 카탈로그")
    for i, (name, m) in enumerate(catalog.items(), 1):
        status = "" if m["available"] else "  [입점 예정]"
        if m.get("flavors"):
            status += f"  [{'·'.join(m['flavors'])} 전용]"
        print(f"  {i}. {flavor_label(m)} ({name}) — 코너: {m['corner']}{status}")
        print(f"     {m['desc']}")
        if m.get("note"):
            print(f"     ※ {m['note']}")
    print("\n규칙: 같은 코너 품목끼리는 함께 설치할 수 없습니다(상호배타). 코너가 다르면 조합 자유.")


def installed_names(target: Path) -> set[str]:
    """설치된 조각 이름 — 폴더는 하나의 작업 공간이므로 두 지침 파일(CLAUDE.md/AGENTS.md) 합집합.
    코너 배타가 flavor를 넘어 적용되게 한다(예: CLAUDE.md Fable5 단독 + AGENTS.md 멀티 = 모순)."""
    names: set[str] = set()
    for fname in FLAVOR_FILES.values():
        instr = target / fname
        if instr.is_file():
            names |= set(re.findall(r"<!-- store:([a-z0-9-]+):start -->", instr.read_text(encoding="utf-8")))
    return names


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


GUARD_HOOK_MARKER = "coach --hook"


def merge_claude_settings_hook(target: Path, hook_file: Path, dry: bool) -> str:
    """대상 .claude/settings.json의 hooks.Stop에 항목을 멱등 병합.
    사용자 훅 보존, 마커(coach --hook) 항목만 dedup 후 정본으로 교체."""
    entry = json.loads(hook_file.read_text(encoding="utf-8"))
    dest = target / ".claude" / "settings.json"
    try:
        data = json.loads(dest.read_text(encoding="utf-8")) if dest.is_file() else {}
    except json.JSONDecodeError:
        data = {}
    if not isinstance(data, dict):
        data = {}
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        hooks = data["hooks"] = {}
    stop = hooks.get("Stop")
    if not isinstance(stop, list):
        stop = hooks["Stop"] = []
    stop[:] = [e for e in stop if GUARD_HOOK_MARKER not in json.dumps(e, ensure_ascii=False)]
    stop.append(entry)
    if not dry:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return "Stop 훅 병합 → .claude/settings.json (coach --hook)"


def fragment_source(frag_dir: Path, instr_name: str) -> Path:
    """flavor별 변형(fragment.codex.md)이 있으면 그것, 없으면 공용 fragment.md."""
    variant = frag_dir / "fragment.codex.md"
    return variant if instr_name == FLAVOR_FILES["codex"] and variant.is_file() else frag_dir / "fragment.md"


def fragment_body(frag_dir: Path, instr_name: str) -> str:
    return fragment_source(frag_dir, instr_name).read_text(encoding="utf-8").strip("\n")


def fragment_files_dirs(frag_dir: Path) -> list[Path]:
    """조각의 딸린 파일 트리 — files/(공용) + files.codex/(codex flavor 전용)."""
    dirs = [frag_dir / "files"]
    if FLAVOR == "codex":
        dirs.append(frag_dir / "files.codex")
    return [d for d in dirs if d.is_dir()]


def install_fragment(target: Path, name: str, dry: bool) -> str:
    """조각을 대상 지침 파일에 멱등 삽입(마커 교체-또는-append) + files/ 트리 복사."""
    frag_dir = FRAGMENTS_DIR / name
    meta = json.loads((frag_dir / "meta.json").read_text(encoding="utf-8"))
    start, end = marker(name)
    block = f"{start}\n{fragment_body(frag_dir, INSTRUCTION_FILE)}\n{end}"
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
    copied = 0
    for files_dir in fragment_files_dirs(frag_dir):
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
    hook_rel = meta.get("claude_settings_hook")
    if hook_rel and FLAVOR == "claude":
        msg = merge_claude_settings_hook(target, frag_dir / hook_rel, dry)
        extra += f" (+{msg})"
    return f"{name} {action} → {INSTRUCTION_FILE}{extra}"


def prune_empty_dirs(d: Path, stop: Path) -> None:
    """삭제로 비게 된 폴더를 stop(미포함) 직전까지 정리 — 빈 폴더만, stop 바깥은 안 건드림."""
    while d != stop and stop in d.parents and d.is_dir() and not any(d.iterdir()):
        d.rmdir()
        d = d.parent


def unmerge_claude_settings_hook(target: Path, dry: bool) -> str | None:
    """merge_claude_settings_hook의 역방향 — hooks.Stop에서 마커(coach --hook) 항목만 제거.
    사용자 훅 보존. 제거로 빈 구조는 정리, settings.json이 통째로 비면 파일 삭제."""
    dest = target / ".claude" / "settings.json"
    if not dest.is_file():
        return None
    try:
        data = json.loads(dest.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    hooks = data.get("hooks") if isinstance(data, dict) else None
    stop = hooks.get("Stop") if isinstance(hooks, dict) else None
    if not isinstance(stop, list):
        return None
    kept = [e for e in stop if GUARD_HOOK_MARKER not in json.dumps(e, ensure_ascii=False)]
    if len(kept) == len(stop):
        return None
    if kept:
        hooks["Stop"] = kept
    else:
        del hooks["Stop"]
        if not hooks:
            del data["hooks"]
    if not dry:
        if data:
            dest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        else:
            dest.unlink()
            prune_empty_dirs(dest.parent, target)
    return "Stop 훅 제거 → .claude/settings.json"


def remove_fragment(target: Path, name: str, dry: bool) -> str:
    """조각 반품 — 마커 블록 제거 + 딸린 파일은 정본 바이트 일치 시만 삭제(수정본 보존).
    미설치·타 flavor·멀티 내장분은 안내 후 no-op(멱등)."""
    instr = target / INSTRUCTION_FILE
    start, end = marker(name)
    text = instr.read_text(encoding="utf-8") if instr.is_file() else ""
    if not (start in text and end in text):
        other_fl, other_fname = next((fl, f) for fl, f in FLAVOR_FILES.items() if f != INSTRUCTION_FILE)
        other_path = target / other_fname
        if other_path.is_file() and start in other_path.read_text(encoding="utf-8"):
            return f"{name}: {other_fname}에 설치돼 있음 — --flavor {other_fl}로 반품하세요 (건너뜀)"
        if name == "karpathy" and multiagent_installed(target):
            return f"{name}: 멀티에이전트 템플릿 내장분(마커 블록 없음) — 반품 대상 아님 (건너뜀)"
        return f"{name}: 설치돼 있지 않음 (건너뜀)"
    new = re.sub(re.escape(start) + r".*?" + re.escape(end), "", text, count=1, flags=re.S)
    new = re.sub(r"\n{3,}", "\n\n", new).lstrip("\n")
    new = new.rstrip("\n") + "\n" if new.strip() else ""
    notes: list[str] = []
    if not new:
        notes.append(f"{INSTRUCTION_FILE} 비어 파일 삭제")
    if not dry:
        if new:
            instr.write_text(new, encoding="utf-8")
        else:
            instr.unlink()
    frag_dir = FRAGMENTS_DIR / name
    removed = 0
    if frag_dir.is_dir():
        for files_dir in fragment_files_dirs(frag_dir):
            for src in sorted(files_dir.rglob("*")):
                if src.is_dir():
                    continue
                dest = target / src.relative_to(files_dir)
                if not dest.is_file():
                    continue
                if dest.read_bytes() == src.read_bytes():
                    if not dry:
                        dest.unlink()
                        prune_empty_dirs(dest.parent, target)
                    removed += 1
                else:
                    notes.append(f"{dest.relative_to(target)} 수정돼 있어 보존")
        meta_path = frag_dir / "meta.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.is_file() else {}
        if meta.get("claude_settings_hook") and FLAVOR == "claude":
            msg = unmerge_claude_settings_hook(target, dry)
            if msg:
                notes.append(msg)
    if removed:
        notes.insert(0, f"딸린 파일 {removed}개 삭제")
    extra = f" ({', '.join(notes)})" if notes else ""
    return f"{name} 반품 → {INSTRUCTION_FILE}{extra}"


def find_multiagent_init() -> Path | None:
    """multi-agent-starter init.py 탐색. env 지정 시 그 경로만 신뢰(없으면 None — 폴백 안 함).
    현재 flavor의 하네스 플러그인 경로를 먼저, 다른 쪽을 폴백으로 훑는다."""
    env = os.environ.get("LOADOUT_MULTIAGENT_INIT")
    if env:
        p = Path(env).expanduser()
        return p if p.is_file() else None
    roots = (".claude", ".codex") if FLAVOR == "claude" else (".codex", ".claude")
    for root in roots:
        hits = sorted(Path.home().glob(f"{root}/plugins/**/skills/configure-multiagent/generator/init.py"))
        if hits:
            return hits[-1]
    return None


def multiagent_installed(target: Path) -> bool:
    return "multiagent" in installed_names(target) or (target / "_shared" / "orchestrator-rules.md").is_file()


def install_multiagent(target: Path, dry: bool) -> str:
    """멀티에이전트 스캐폴드를 설치된 multi-agent-starter의 init.py에 위임.
    init.py가 CLAUDE.md를 통째로 쓰므로 기존 조각 블록을 회수했다가 재-append(보존).
    karpathy 조각은 템플릿에 4원칙이 내장돼 있어 재부착하지 않는다."""
    init_py = find_multiagent_init()
    if init_py is None:
        sys.exit("[error] multi-agent-starter 플러그인을 찾지 못했습니다. "
                 "먼저 설치하거나 LOADOUT_MULTIAGENT_INIT로 init.py 경로를 지정하세요.")
    instr = target / INSTRUCTION_FILE
    saved: list[str] = []
    text = instr.read_text(encoding="utf-8") if instr.is_file() else ""
    if text:
        # 회수·재부착은 현재 flavor의 지침 파일에 있는 블록만 (다른 파일은 init.py가 안 건드림)
        names = set(re.findall(r"<!-- store:([a-z0-9-]+):start -->", text))
        if "karpathy" in names:
            print("  [안내] 멀티에이전트 템플릿에는 카파시 4원칙이 이미 내장 — 기존 karpathy 조각은 재부착하지 않습니다.")
        for name in sorted(names - {"multiagent", "karpathy"}):
            start, end = marker(name)
            m = re.search(re.escape(start) + r".*?" + re.escape(end), text, flags=re.S)
            if m:
                saved.append(m.group(0))
    if dry:
        return f"multiagent 스캐폴드 위임 예정 ({init_py}, 보존 조각 {len(saved)}개)"
    bak = target / f"{INSTRUCTION_FILE}.loadout-bak"
    if instr.is_file():
        import shutil
        shutil.copy2(instr, bak)
        residue = re.sub(r"<!-- store:([a-z0-9-]+):start -->.*?<!-- store:\1:end -->", "", text, flags=re.S)
        if residue.strip():
            print(f"  [주의] 기존 {INSTRUCTION_FILE}의 비-store 본문은 init.py가 덮어씁니다 — 백업: {bak}")
    rc = subprocess.run([sys.executable, str(init_py), "--flavor", FLAVOR,
                         "--target", str(target), "--yes", "--no-validate"]).returncode
    if rc != 0:
        note = f" — 이전 {INSTRUCTION_FILE} 백업: {bak}" if bak.is_file() else ""
        sys.exit(f"[error] init.py 실패 (exit {rc}){note}")
    if saved:
        text = instr.read_text(encoding="utf-8").rstrip("\n")
        instr.write_text(text + "\n\n" + "\n\n".join(saved) + "\n", encoding="utf-8")
    return f"multiagent 스캐폴드 설치 (init.py 위임, 보존 조각 {len(saved)}개 재부착)"


def doctor(target: Path, catalog: dict) -> int:
    """읽기 전용 진단. 아무것도 고치지 않는다. 반환 = exit 코드(FAIL 있으면 1)."""
    counts = {"FAIL": 0, "WARN": 0}

    def report(level: str, msg: str) -> None:
        if level in counts:
            counts[level] += 1
        print(f"  [{level}]{' ' * (5 - len(level))}{msg}")

    print(f"loadout doctor — {target}")
    present = [(fl, target / fname) for fl, fname in FLAVOR_FILES.items() if (target / fname).is_file()]
    if not present and not multiagent_installed(target):
        print("  지침 파일(CLAUDE.md/AGENTS.md)이 없습니다 — 설치된 조각 없음.")
        return 0

    installed_by_file: dict[str, set[str]] = {}
    for fl, path in present:
        text = path.read_text(encoding="utf-8")
        tokens = re.findall(r"<!-- store:([a-z0-9-]+):(start|end) -->", text)
        starts = [n for n, k in tokens if k == "start"]
        ends = [n for n, k in tokens if k == "end"]
        # 순서·중첩 검사(스택) — 개수가 맞아도 end-before-start·교차 중첩이면 블록이 깨진 것
        order_bad: set[str] = set()
        stack: list[str] = []
        for n, kind in tokens:
            if kind == "start":
                stack.append(n)
            elif stack and stack[-1] == n:
                stack.pop()
            else:
                order_bad.add(n)
        order_bad.update(stack)
        clean: set[str] = set()
        for n in sorted(set(starts) | set(ends)):
            s, e = starts.count(n), ends.count(n)
            if s != e:
                report("FAIL", f"{path.name}: '{n}' 마커 짝 깨짐 (start {s} / end {e})")
            elif s > 1:
                report("FAIL", f"{path.name}: '{n}' 블록 중복 {s}개")
            elif n in order_bad:
                report("FAIL", f"{path.name}: '{n}' 마커 순서·교차 오류 (end가 먼저 오거나 다른 블록과 얽힘)")
            else:
                clean.add(n)
        for n in sorted(clean):
            if n not in catalog:
                report("WARN", f"{path.name}: 카탈로그에 없는 조각 마커 '{n}'")
        known = {n for n in clean if n in catalog}
        for n in sorted(known):
            allowed = catalog[n].get("flavors")
            if allowed and fl not in allowed:
                report("WARN", f"{path.name}: '{n}'는 {'·'.join(allowed)} 전용 품목 — 이 파일에 설치돼 있음(제거 권장)")
        for n in sorted(known):
            start, end = marker(n)
            m = re.search(re.escape(start) + r"\n(.*?)\n" + re.escape(end), text, flags=re.S)
            src = fragment_source(FRAGMENTS_DIR / n, path.name)
            if m and src.is_file() and m.group(1) != src.read_text(encoding="utf-8").strip("\n"):
                report("WARN", f"{path.name}: '{n}' 블록이 카탈로그 최신본과 다름 — 재설치 권장")
        report("OK", f"{path.name}: 마커 구조 점검 완료 (조각 {len(clean)}개)")
        installed_by_file[path.name] = known

    installed_all = set().union(*installed_by_file.values()) if installed_by_file else set()

    # 코너 배타 — 폴더는 하나의 작업 공간이므로 두 지침 파일 합집합으로 판정
    by_corner: dict[str, list[str]] = {}
    for n in sorted(installed_all):
        by_corner.setdefault(catalog[n]["corner"], []).append(n)
    for corner, names in by_corner.items():
        if len(names) > 1:
            report("FAIL", f"같은 코너({corner}) 조각 공존 — {', '.join(names)}")

    # 멀티에이전트 스캐폴드(마커 없는 위임 설치) — 배타·전제 점검
    if multiagent_installed(target):
        ma_corner = catalog.get("multiagent", {}).get("corner")
        for n in sorted(installed_all - {"multiagent"}):
            if catalog[n]["corner"] == ma_corner:
                report("FAIL", f"멀티에이전트 스캐폴드와 같은 코너({ma_corner}) 조각 공존 — {n}")
        if find_multiagent_init() is None:
            report("WARN", "multiagent: multi-agent-starter init.py를 찾을 수 없음 — 재설치·업데이트 불가 상태")
        else:
            report("OK", "multiagent: starter init.py 탐색 가능")

    # 딸린 파일 — files/(공용) + AGENTS.md에 설치된 조각은 files.codex/(codex 전용)도
    for n in sorted(installed_all):
        dirs = [FRAGMENTS_DIR / n / "files"]
        if n in installed_by_file.get(FLAVOR_FILES["codex"], set()):
            dirs.append(FRAGMENTS_DIR / n / "files.codex")
        dirs = [d for d in dirs if d.is_dir()]
        if not dirs:
            continue
        missing = [str(p.relative_to(d)) for d in dirs for p in sorted(d.rglob("*"))
                   if p.is_file() and not (target / p.relative_to(d)).is_file()]
        if missing:
            report("WARN", f"{n}: 딸린 파일 유실 — {', '.join(missing)} — 재설치 권장")
        else:
            report("OK", f"{n}: 딸린 파일 존재")

    # guard 전제조건 (배선은 설치된 지침 파일별로)
    if "guard" in installed_all:
        import shutil
        if shutil.which("coach"):
            report("OK", "guard: coach가 PATH에 있음")
        else:
            report("WARN", "guard: coach가 PATH에 없음 — 가드는 fail-open(무력) 상태")
        if "guard" in installed_by_file.get(FLAVOR_FILES["claude"], set()):
            wired: list = []
            settings = target / ".claude" / "settings.json"
            if settings.is_file():
                try:
                    stop = json.loads(settings.read_text(encoding="utf-8")).get("hooks", {}).get("Stop", [])
                    wired = [e for e in stop if GUARD_HOOK_MARKER in json.dumps(e, ensure_ascii=False)]
                except (json.JSONDecodeError, AttributeError):
                    pass
            canonical = json.loads((FRAGMENTS_DIR / "guard" / "hook.json").read_text(encoding="utf-8"))
            if not wired:
                report("WARN", "guard(claude): .claude/settings.json에 coach --hook Stop 훅 없음 — 재설치 권장")
            elif len(wired) != 1:
                report("WARN", f"guard(claude): Stop 훅 중복({len(wired)}개) — 재설치 권장")
            elif wired[0] != canonical:
                report("WARN", "guard(claude): Stop 훅이 hook.json 정본과 불일치 — 재설치 권장")
            else:
                report("OK", "guard(claude): Stop 훅 정본 일치 (.claude/settings.json)")
        if "guard" in installed_by_file.get(FLAVOR_FILES["codex"], set()):
            canon = FRAGMENTS_DIR / "guard" / "files.codex" / "_shared" / "guard" / "codex_goal_watch.mjs"
            watch = target / "_shared" / "guard" / "codex_goal_watch.mjs"
            if watch.is_file():  # 부재는 위 딸린 파일 검사가 WARN 처리
                if watch.read_bytes() != canon.read_bytes():
                    report("WARN", "guard(codex): 워처가 codex_goal_watch.mjs 정본과 불일치 — 재설치 권장")
                else:
                    report("OK", "guard(codex): 워처 정본 일치 (_shared/guard/)")

    verdict = ("FAIL " + str(counts['FAIL']) + "건" if counts["FAIL"] else "구조 이상 없음") \
        + (f", WARN {counts['WARN']}건" if counts["WARN"] else "")
    print(f"\n  진단 결과: {verdict}")
    return 1 if counts["FAIL"] else 0


def main() -> None:
    ap = argparse.ArgumentParser(description="CLAUDE.md 구성 백화점 (결정적 조각 설치기)")
    ap.add_argument("--list", action="store_true", help="카탈로그 출력")
    ap.add_argument("--target", help="설치 대상 폴더")
    ap.add_argument("--pick", help="설치할 품목(쉼표 구분, 예: karpathy,agent-loop)")
    ap.add_argument("--remove", help="반품할 품목(쉼표 구분) — --pick과 병용 시 제거를 먼저 실행(코너 스왑)")
    ap.add_argument("--flavor", choices=sorted(FLAVOR_FILES), default="claude",
                    help="대상 하네스: claude=CLAUDE.md(기본) | codex=AGENTS.md")
    ap.add_argument("--doctor", action="store_true", help="설치 상태 진단(읽기 전용, 수정 없음)")
    ap.add_argument("--yes", action="store_true", help="확인 프롬프트 생략")
    ap.add_argument("--dry-run", action="store_true", help="실제 쓰지 않고 미리보기")
    args = ap.parse_args()

    global FLAVOR, INSTRUCTION_FILE
    FLAVOR = args.flavor
    INSTRUCTION_FILE = FLAVOR_FILES[FLAVOR]

    catalog = load_catalog()
    if not catalog:
        sys.exit(f"[error] fragments가 없습니다: {FRAGMENTS_DIR}")

    if args.doctor:
        if not args.target:
            sys.exit("[error] --doctor에는 --target이 필요합니다")
        sys.exit(doctor(Path(args.target).expanduser().resolve(), catalog))

    if args.list or not (args.target and (args.pick or args.remove)):
        print_catalog(catalog)
        return

    target = Path(args.target).expanduser().resolve()
    if target == SCRIPT_DIR or SCRIPT_DIR in target.parents or target in SCRIPT_DIR.parents:
        sys.exit(f"[error] installer 트리 안에는 설치할 수 없습니다: {target}")

    installed = installed_names(target)

    removes = [p.strip() for p in (args.remove or "").split(",") if p.strip()]
    removes = list(dict.fromkeys(removes))
    scaffold_rm = [r for r in removes if r in catalog and catalog[r].get("scaffold")]
    if scaffold_rm:
        for r in scaffold_rm:
            print(f"[안내] {catalog[r]['label']}: 스캐폴드형 품목은 반품을 지원하지 않습니다 — "
                  f"tasks/ 등에 사용자 작업물이 쌓이는 구조라 자동 제거가 위험합니다. "
                  f"보존할 작업물을 옮긴 뒤 {INSTRUCTION_FILE}·_shared/ 등을 수동으로 정리하세요.")
        sys.exit(2)
    # 반품 대상 검증은 카탈로그 ∪ 실제 설치 마커 — 카탈로그에서 빠진 옛 조각도 반품 가능해야 함
    unknown_rm = [r for r in removes if r not in catalog and r not in installed]
    if unknown_rm:
        print(f"[error] 없는 품목(카탈로그·설치 모두 없음): {', '.join(unknown_rm)}")
        sys.exit(2)

    picks = [p.strip() for p in (args.pick or "").split(",") if p.strip()]
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
    wrong_flavor = [p for p in picks if FLAVOR not in catalog[p].get("flavors", list(FLAVOR_FILES))]
    if wrong_flavor:
        for p in wrong_flavor:
            print(f"[안내] {catalog[p]['label']}: {'·'.join(catalog[p]['flavors'])} 전용 품목 — "
                  f"{FLAVOR} flavor에는 설치할 수 없습니다. ({catalog[p]['note']})")
        sys.exit(2)

    # 배타 검사는 반품 반영 후 상태 기준 — 현재 flavor 파일에서 실제로 빠질 마커만 차감
    instr = target / INSTRUCTION_FILE
    current_names = set(re.findall(r"<!-- store:([a-z0-9-]+):start -->",
                                   instr.read_text(encoding="utf-8"))) if instr.is_file() else set()
    installed_after = installed - (set(removes) & current_names)
    if multiagent_installed(target):
        installed_after |= {"multiagent"}
    problems = check_exclusions(picks, installed_after, catalog)
    if problems:
        print("[배타 위반] 설치를 거부합니다 — 대상 파일은 변경되지 않았습니다:")
        for msg in problems:
            print(f"  · {msg}")
        sys.exit(2)

    if "karpathy" in picks and ("multiagent" in picks or "multiagent" in installed_after):
        print("  [안내] 멀티에이전트 템플릿에는 카파시 4원칙이 이미 내장 — karpathy 설치를 생략합니다.")
        picks = [p for p in picks if p != "karpathy"]

    print(f"  target : {target}")
    if removes:
        print(f"  반품 품목: {', '.join(flavor_label(catalog[r]) if r in catalog else r for r in removes)}")
    if picks:
        print(f"  담은 품목: {', '.join(flavor_label(catalog[p]) for p in picks)}")
    if not args.yes and not args.dry_run:
        if input("\n진행할까요? [y/N]: ").strip().lower() not in ("y", "yes"):
            sys.exit("취소됨")

    prefix = "(dry) " if args.dry_run else ""
    for r in removes:
        print(f"  {prefix}{remove_fragment(target, r, dry=args.dry_run)}")
    ordered = sorted(picks, key=lambda p: 0 if catalog[p].get("scaffold") else 1)
    for p in ordered:
        if catalog[p].get("scaffold"):
            print(f"  {prefix}{install_multiagent(target, dry=args.dry_run)}")
            continue
        skip_marker = catalog[p].get("skip_if_contains")
        if skip_marker:
            instr = target / INSTRUCTION_FILE
            if instr.is_file() and skip_marker in instr.read_text(encoding="utf-8"):
                print(f"  [안내] {catalog[p].get('skip_note', catalog[p]['label'] + ' 생략')}")
                continue
        print(f"  {prefix}{install_fragment(target, p, dry=args.dry_run)}")
    print("\n  완료.")


if __name__ == "__main__":
    main()
