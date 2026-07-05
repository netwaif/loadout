---
name: configure-store
description: Use when the user wants to pick-and-install CLAUDE.md 구성 조각(카파시 4원칙, Fable5 단독, 멀티에이전트, 에이전트 루프 등) for a folder. Triggers on "CLAUDE.md 구성 백화점", "loadout 설치", "구성 골라 담아줘", "카파시 4원칙만 설치", "이 폴더에 에이전트 루프 구성 넣어줘", "Fable5 단독 구성 설치". Composable fragments with corner-based exclusion, installed by a deterministic marker-append installer.
---

# CLAUDE.md 구성 백화점 (loadout / configure-store)

작업 폴더 성격에 맞는 CLAUDE.md 구성 조각을 카탈로그에서 **골라 담아** 설치한다.
**직접 파일을 손으로 쓰지 말 것** — 반드시 이 스킬 폴더의 결정적 설치기 `generator/store.py`를 실행한다.

## 절차

1. **카탈로그 제시** — `python3 "<이 스킬 폴더>/generator/store.py" --list` 출력을 보여준다.
2. **대상 폴더 확인** — 어디에 설치할지 묻는다(정확한 경로 확인).
3. **품목 선택** — 사용자가 고른다. 규칙 안내: 같은 코너 품목은 함께 담을 수 없다(예: Fable5 단독 ↔ 멀티에이전트).
4. **실행**:
   ```bash
   python3 "<이 스킬 폴더>/generator/store.py" --target "<대상폴더>" --pick <품목1,품목2> --yes
   ```
5. **결과 보고** — 배타 위반(exit 2)이면 위반 내용을 그대로 전달한다. "완료"는 exit 0일 때만.
6. **멀티에이전트 포함 시** — multi-agent-starter 플러그인이 설치돼 있어야 한다(store가 그 init.py에 위임). 못 찾으면 설치 안내 후 중단. knot·요금가드 옵션은 configure-multiagent 스킬에서 추가 가능(백화점에는 입점 예정).

## 동작 보장

- **결정적**: 번들 조각을 그대로 마커 append. 모델이 구성 내용을 창작하지 않는다.
- **멱등**: 같은 품목 재설치 = 마커 블록 교체(중복 없음).
- **배타는 설치 시점 거부**: 모순된 CLAUDE.md가 만들어지지 않는다.
- **조건부 문단**: 조각 안 `[X도 설치된 경우] …`는 X가 같이 설치됐을 때만 의미를 갖는다(코드 아님 — 에이전트가 파일 안에서 판단).

## 새 구성 추가 (입점)

`generator/fragments/_TEMPLATE/README.md` 참조 — 폴더 복사 + meta.json(코너 지정) + fragment.md 작성이 전부다.

## Do NOT

- 조각 내용을 손으로 CLAUDE.md에 붙여넣지 말 것(마커 없는 야생 설치 금지).
- 같은 코너 배타를 우회해 설치하지 말 것.
- 플러그인 자신의 폴더 안에 설치하지 말 것.
- multi-agent-starter의 파일을 수정하지 말 것(위임 호출만).
