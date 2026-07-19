# loadout 반품(--remove) 설계 — v0.5.0

2026-07-19 승인. 대상: `plugins/loadout/skills/configure-store/generator/store.py`

## 배경·목적

loadout에는 설치(`--pick`)·진단(`--doctor`)만 있고 제거가 없다. 같은 코너 품목은 설치
시점에 배타 거부되므로 코너 스왑(예: Fable5 단독 → 멀티에이전트)을 하려면 CLAUDE.md를
손으로 지워야 한다 — "야생 설치 금지"가 철학인데 야생 제거가 유일한 경로인 자기모순.
마커 블록 구조 덕에 결정적 제거는 설계상 싸게 얹힌다.

## CLI

```bash
python3 store.py --target <폴더> --remove <품목1,품목2> [--pick <품목>] \
                 [--flavor codex] [--yes] [--dry-run]
```

- `--remove` 단독 사용 가능.
- `--pick` 병용 시 **제거 먼저 실행 → 설치**. 배타 검사(`check_exclusions`)는 제거가
  반영된 설치 상태 기준으로 수행 — 코너 스왑이 한 호출로 끝난다.
- 대상 파일 = 현재 flavor의 지침 파일(`CLAUDE.md`/`AGENTS.md`), 설치와 대칭.
  블록이 반대쪽 flavor 파일에만 있으면 제거하지 않고 안내한다
  ("AGENTS.md에 설치돼 있음 — --flavor codex로 제거").
- 확인 프롬프트(`--yes` 생략 시)·`--dry-run` 미리보기·installer 트리 내 대상 거부는
  설치와 동일하게 적용.

## 마커 블록 제거

- `<!-- store:이름:start -->` ~ `<!-- store:이름:end -->` 블록을 삭제하고 주변 빈 줄을
  정리한다(블록 사이 `\n\n` 유지, 파일 끝 개행 정리).
- 미설치 품목 `--remove` = 안내 후 no-op(멱등). 이것만으로 실패하지 않는다(exit 0).
- **제거 대상 검증은 "카탈로그 ∪ 대상에 실제 설치된 마커" 기준** — 카탈로그에서 빠진
  옛 조각(doctor가 "카탈로그에 없는 조각 마커"로 WARN하는 것)도 반품할 수 있어야 한다.
  둘 다에 없는 이름만 `[error] 없는 품목`(exit 2).
- 제거 후 지침 파일 내용이 공백뿐이면 파일 자체를 삭제한다(설치 전 원상복구).

## 딸린 파일 — 정본 일치 시만 삭제

- 조각의 `files/`(+ codex flavor면 `files.codex/`) 트리에 있는 각 파일에 대해,
  대상 폴더의 대응 파일을 **정본과 바이트 대조**한다.
  - 동일 → 삭제.
  - 다름(사용자 수정) → 보존 + "수정돼 있어 보존함" 안내.
  - 이미 없음 → 무시.
- 삭제로 비게 된 하위 폴더는 target까지 거슬러 올라가며 정리한다(빈 폴더만).
- 사용자 데이터(예: SESSION.md)는 딸린 파일이 아니므로 어떤 경로로도 건드리지 않는다.

## 품목별 예외

- **multiagent(스캐폴드형, `meta.scaffold=true`)**: 제거 거부(exit 2) + 수동 절차 안내.
  근거: starter가 CLAUDE.md를 통째로 쓰고(마커 없음) tasks/·_shared/에 사용자 작업물이
  쌓이는 구조라 결정적 제거가 성립하지 않는다. 안내문에는 "tasks/ 등 작업물을 보존하려면
  수동으로 정리해야 함"을 명시.
- **guard(claude flavor)**: 블록 제거에 더해 `.claude/settings.json`의 `hooks.Stop`에서
  `coach --hook` 마커를 포함한 항목만 제거(설치의 `merge_claude_settings_hook` dedup
  로직 역방향). 사용자 훅은 보존. 제거 후 빈 `Stop` 리스트·빈 `hooks` dict는 키 정리.
  codex flavor의 워처(`_shared/guard/`)는 위 딸린 파일 규칙으로 처리된다.
- **karpathy가 멀티 템플릿 내장분일 때**: 마커 블록이 없으므로 안내 후 no-op
  (멀티에이전트 템플릿 내장 4원칙은 loadout 소관이 아님).

## 구현 노트

- 재활용: 마커 정규식(`installed_names`·doctor), 정본 바이트 대조(doctor stale 검사),
  `GUARD_HOOK_MARKER` dedup(`merge_claude_settings_hook`).
- 새 함수 예상: `remove_fragment(target, name, dry) -> str`(설치의 `install_fragment`와
  대칭), `unmerge_claude_settings_hook(target, dry)`.
- main() 흐름: `--remove` 파싱·검증 → (확인) → 제거 실행 → `--pick` 있으면 기존 설치
  경로로 진입(installed 재계산).

## 테스트 (tests/test_store.py 추가)

1. 기본 제거 — 설치 후 제거하면 블록·딸린 파일이 사라지고 파일이 원상복구된다.
2. 미설치 no-op — exit 0, 파일 무변경.
3. 수정된 딸린 파일 보존 — 변조 후 제거해도 파일이 남는다.
4. guard 훅 제거 — settings.json에서 coach --hook 항목만 사라지고 사용자 훅 보존.
5. multiagent 거부 — exit 2.
6. 스왑(배타 해소) — fable5-solo 설치 상태에서:
   - 대조군: `--pick multiagent --dry-run` → exit 2(배타 위반).
   - 실험군: `--remove fable5-solo --pick multiagent --dry-run` → exit 0(제거 반영 후
     배타 통과). 두 경우 모두 `LOADOUT_MULTIAGENT_INIT`를 더미 파일로 지정해 starter
     실설치 없이 검증(dry-run은 위임 전에 반환).
   - 겸사 검증: dry-run이므로 실제 파일 무변경이어야 함.
7. 반대 flavor 안내 — CLAUDE.md에만 있는 조각을 `--flavor codex --remove` 시 no-op+안내.

## 문서·버전

- SKILL.md: 절차에 "반품" 단계 추가(카탈로그 제시 규칙과 동일한 톤).
- README.md: 반품 사용법 한 블록.
- CHANGELOG.md `[0.5.0]` / `plugin.json`·`marketplace.json` 버전 0.5.0
  (새 CLI 표면 = minor 승격).

## 명시적 비범위

- 스캐폴드(multiagent) 자동 제거.
- HOME 레벨 설정·플러그인 자체 제거.
- 제거 이력·롤백 기능.
