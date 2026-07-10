# Changelog

## [0.4.6] - 2026-07-10
### Fixed
- 문서의 codex 반영 누락 정리(docs only, 동작 변경 없음): README 품목 표에 Fable5 단독=claude 전용·저비용 Fable 5=codex "저비용 GPT 5.6" 번안 비고 추가, 입점 양식(_TEMPLATE/README.md)에 `label_codex` 규약 문서화, marketplace.json 상위 description 품목 열거를 현행 8종으로 갱신.

## [0.4.5] - 2026-07-10
### Changed
- codex flavor 카탈로그 표시명: meta `label_codex` 규약 — `--list --flavor codex`에서 "저비용 Fable 5"가 **"저비용 GPT 5.6"**으로 표시(설치 확인 문구도 동일). 실사용에서 "GPT 저비용이 왜 안 보이지" 혼동 발생 → 라벨을 flavor 기준으로. SKILL 절차 1에 codex 대상이면 `--list --flavor codex` 명시.

## [0.4.4] - 2026-07-10
### Changed
- 저비용 조각(claude·codex 둘 다) ① 역할 분리에 **위임 손익분기** 반영 — 3-run 실측(Fable 단독 $0.76 vs Haiku 위임 $0.78 vs Opus 위임 $1.80) 결과: 서브에이전트는 캐시 미공유 고정비 + 명세 작성 토큰 때문에, 산출물이 그걸 크게 넘는 대량 작업에서만 위임이 이긴다. **파일 몇 개짜리 단발 구현은 직접** 명시.
- 위임처 사다리 명시(claude): Haiku=기계적·반복 / Sonnet=일반 구현·테스트 / **Opus=비용 절감용 위임처 아님**(실측 Haiku의 ~5배 — 난도·병렬화·컨텍스트 분리 목적만). codex: 위임처는 진짜 싼 티어(Luna·mini)만 — 중상급 티어 위임은 손해.

## [0.4.3] - 2026-07-10
### Changed
- 저비용 GPT 5.6 조각(codex 번안)을 OpenAI 공식 지침으로 정밀화: 티어 라우팅(Sol=프런티어/Terra=균형/Luna=고효율) 반영하되 **"비싼 모델"="세션 가용 최상위 티어"** 기준(구독에 Sol 미제공 가능) — Sol 특화 지침 아님. 추론 강도 문구도 공식 표현(medium=균형 시작점, max=최난도 전용)에 맞춤.

## [0.4.2] - 2026-07-10
### Added
- 저비용 Fable 5 품목의 codex 번안: `fragment.codex.md` — codex flavor로 담으면 **"저비용 GPT 5.6"**(역할 분리·reasoning effort 상한·기획 선행을 `/model`·`config.toml` 프로필 개념으로)이 AGENTS.md에 설치된다. claude flavor는 기존 Fable 5 원본 그대로.
- meta `flavors` 필드: flavor 제한 품목 규약. **Fable5 단독은 `["claude"]`** — Anthropic 공식 Fable 5 팁 기반이라 GPT 대응 공식 지침이 확인되기 전까지 codex flavor에서 설치 거부(exit 2 + 안내). 카탈로그에 `[claude 전용]` 표기, doctor는 전용 품목이 다른 flavor 파일에 있으면 WARN.

## [0.4.1] - 2026-07-10
### Fixed
- SKILL 절차 교정: 품목 선택을 옵션 위젯(질문 UI)으로 나열하지 않도록 명시 — 위젯 옵션 개수 제한(4개)으로 8품목 카탈로그가 조용히 잘리는 문제(실측: 저비용 Fable5·에이전트 루프·knot·요금가드 누락). 카탈로그는 `--list` 출력 전문, 선택은 텍스트로.

## [0.4.0] - 2026-07-10
### Added
- `--doctor`: 읽기 전용 설치 진단 — 마커 짝 깨짐·블록 중복·코너 배타 위반(FAIL, exit 1) / stale 조각(카탈로그 최신본과 다름)·미지 마커·딸린 파일 유실·guard(coach PATH, claude 훅 배선, codex 워처)·multiagent(starter 탐색) 전제조건(WARN, exit 0). CLAUDE.md·AGENTS.md 둘 다 진단.
- Codex 지원: `--flavor claude|codex`(기본 claude) → CLAUDE.md/AGENTS.md 매핑. 멀티에이전트 위임에 flavor 전달, init.py 탐색에 `~/.codex/plugins/**` 추가(flavor 쪽 우선). 루트 `.agents/plugins/marketplace.json` 카탈로그 추가 — Codex CLI에서 loadout 플러그인 설치 가능.
- 요금가드 codex flavor 정식 지원: `fragment.codex.md`(워처 3단계 문구) + 동봉 워처(`files.codex/` — `codex_goal_watch.mjs`·README)를 대상 `_shared/guard/`로 자동 복사. **워처 정본이 multi-agent-starter에서 loadout으로 이관** — loadout 단독으로 완결(starter 불필요). claude 훅 병합은 claude flavor에서만. doctor가 가드 배선 정본 대조까지 수행(claude=Stop 훅 hook.json 일치·중복, codex=워처 바이트 일치 — starter validate C12의 소관 이관).
- 조각 규약 확장: `files.codex/` — codex flavor에서만 복사되는 딸린 파일 트리(공용 `files/`와 병행).
### Fixed
- 테스트 카탈로그 검사 6품목→8품목 교정(0.3.0에서 미갱신돼 baseline 2 FAIL이던 것).

## [0.3.0] - 2026-07-09
### Added
- 세션 이어가기(session-handoff) 조각 입점 — "세션 연속성" 코너 신설. SESSION.md 고정 섹션 5개(목표/현재 상태/다음 단계/결정 기록/파일 흔적)로 세션 마감 체크포인트·다음 세션 재정박. 사용자는 "이어서 해줘"/"세션 마감" 한마디면 충분. SESSION.template.md 딸림 — 살아있는 SESSION.md는 배포하지 않아 재설치에도 기록 보존.
- 저비용 Fable 5(fable5-lowcost) 조각 입점 — "모델 운용" 코너 신설. 역할 분리(싼 메인+advisor / Fable 메인+서브에이전트 위임 두 갈래)·Effort 상한(기본 low~medium, max 자제)·기획 선행. 에이전트 직접 실행 + 사용자 설정은 한 줄 제안의 두 층 구조. 전 품목 8종.

## [0.2.0] - 2026-07-05
### Added
- knot 조각 입점: 자동층 블록($KNOT_VAULT 게이트). 기존 `--with-knot` 관리블록 감지 시 생략(meta `skip_if_contains`).
- 요금가드(guard) 조각 입점: fragment + `.claude/settings.json` `hooks.Stop` 훅 멱등 병합(meta `claude_settings_hook` — 마커 "coach --hook" dedup, 사용자 훅 보존, dry-run 미기록). 전 품목 구매 가능(6품목).

## [0.1.0] - 2026-07-05
### Added
- configure-store 스킬: CLAUDE.md 구성 백화점 — 조합형 구성 카탈로그(카파시 4원칙 / Fable5 단독 / 멀티에이전트(위임) / 에이전트 루프 + 입점 예정: knot·요금가드).
- 결정적 설치기 store.py: 마커 멱등 append, 코너 기반 배타(설치 시점 거부), 딸린 파일 복사, multi-agent-starter init.py 위임.
- 입점 양식(fragments/_TEMPLATE) — 새 구성 추가 = 조각 폴더 하나.
