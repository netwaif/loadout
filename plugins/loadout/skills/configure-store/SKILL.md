---
name: configure-store
description: Use when the user wants to pick-and-install CLAUDE.md/AGENTS.md 구성 조각(카파시 4원칙, Fable5 단독, 멀티에이전트, 에이전트 루프 등) for a folder, or to diagnose an installed folder. Triggers on "CLAUDE.md 구성 백화점", "loadout 설치", "구성 골라 담아줘", "카파시 4원칙만 설치", "이 폴더에 에이전트 루프 구성 넣어줘", "Fable5 단독 구성 설치", "codex에 설치", "AGENTS.md에 설치", "loadout doctor", "구성 점검해줘". Composable fragments with corner-based exclusion, installed by a deterministic marker-append installer; read-only doctor included.
---

# CLAUDE.md 구성 백화점 (loadout / configure-store)

작업 폴더 성격에 맞는 구성 조각을 카탈로그에서 **골라 담아** 설치한다.
**직접 파일을 손으로 쓰지 말 것** — 반드시 이 스킬 폴더의 결정적 설치기 `generator/store.py`를 실행한다.

## 절차

1. **카탈로그 제시** — `python3 "<이 스킬 폴더>/generator/store.py" --list` 출력 **전문을 그대로** 보여준다(요약·발췌 금지). 대상이 Codex(AGENTS.md)면 `--list --flavor codex`로 — 품목 표시명이 codex 기준(예: 저비용 GPT 5.6)으로 나온다.
2. **대상 폴더·하네스 확인** — 어디에 설치할지 묻는다(정확한 경로 확인). 대상이 Codex(AGENTS.md) 폴더면 `--flavor codex`를 쓴다(기본은 claude=CLAUDE.md). 사용자가 명시하지 않고 대상 폴더에 AGENTS.md만 있으면 codex인지 확인한다.
3. **품목 선택** — 사용자가 텍스트로 고른다. **품목 목록을 옵션 선택 위젯(질문 UI)으로 띄우지 말 것** — 위젯은 옵션 개수 제한(예: 4개)이 있어 카탈로그가 조용히 잘린다. 규칙 안내: 같은 코너 품목은 함께 담을 수 없다(예: Fable5 단독 ↔ 멀티에이전트).
4. **실행**:
   ```bash
   python3 "<이 스킬 폴더>/generator/store.py" --target "<대상폴더>" --pick <품목1,품목2> [--flavor codex] --yes
   ```
5. **결과 보고** — 배타 위반(exit 2)이면 위반 내용을 그대로 전달한다. "완료"는 exit 0일 때만.
6. **멀티에이전트 포함 시** — multi-agent-starter 플러그인이 설치돼 있어야 한다(store가 그 init.py에 flavor 그대로 위임). 못 찾으면 설치 안내 후 중단. knot·요금가드도 카탈로그에서 담을 수 있다. knot 능동 스킬은 netwaif/knot 플러그인이 제공.
7. **요금가드 × codex flavor** — 조각 설치와 함께 동봉 워처(`files.codex/` → 대상 `_shared/guard/`)가 자동 복사된다. loadout 단독으로 완결(starter 불필요). 이후 3단계 실행법은 조각 본문·`_shared/guard/README.md` 참조.

## 진단 (doctor)

"구성 점검해줘", "loadout doctor" 요청 시:

```bash
python3 "<이 스킬 폴더>/generator/store.py" --target "<대상폴더>" --doctor
```

읽기 전용 — 아무것도 고치지 않는다. `[FAIL]`=마커 짝 깨짐·블록 중복·코너 배타 위반(exit 1), `[WARN]`=조각이 카탈로그 최신본과 다름(stale)·딸린 파일 유실·guard/multiagent 전제조건 미비(exit 0). 결과를 그대로 보여주고, stale·유실은 해당 품목 재설치(멱등)로 고칠 수 있음을 안내한다.

## 동작 보장

- **결정적**: 번들 조각을 그대로 마커 append. 모델이 구성 내용을 창작하지 않는다.
- **멱등**: 같은 품목 재설치 = 마커 블록 교체(중복 없음).
- **배타는 설치 시점 거부**: 모순된 CLAUDE.md가 만들어지지 않는다.
- **조건부 문단**: 조각 안 `[X도 설치된 경우] …`는 X가 같이 설치됐을 때만 의미를 갖는다(코드 아님 — 에이전트가 파일 안에서 판단).

## 새 구성 추가 (입점)

`generator/fragments/_TEMPLATE/README.md` 참조 — 폴더 복사 + meta.json(코너 지정) + fragment.md 작성이 전부다.

## Do NOT

- 품목 선택을 옵션 위젯으로 나열하지 말 것 — 개수 제한으로 품목이 잘린 채 제시된다(전체 카탈로그는 `--list` 텍스트로).
- 조각 내용을 손으로 CLAUDE.md에 붙여넣지 말 것(마커 없는 야생 설치 금지).
- 같은 코너 배타를 우회해 설치하지 말 것.
- 플러그인 자신의 폴더 안에 설치하지 말 것.
- multi-agent-starter의 파일을 수정하지 말 것(위임 호출만).
