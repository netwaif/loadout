# Changelog

## [0.2.0] - 2026-07-05
### Added
- knot 조각 입점: 자동층 블록($KNOT_VAULT 게이트). 기존 `--with-knot` 관리블록 감지 시 생략(meta `skip_if_contains`).
- 요금가드(guard) 조각 입점: fragment + `.claude/settings.json` `hooks.Stop` 훅 멱등 병합(meta `claude_settings_hook` — 마커 "coach --hook" dedup, 사용자 훅 보존, dry-run 미기록). 전 품목 구매 가능(6품목).

## [0.1.0] - 2026-07-05
### Added
- configure-store 스킬: CLAUDE.md 구성 백화점 — 조합형 구성 카탈로그(카파시 4원칙 / Fable5 단독 / 멀티에이전트(위임) / 에이전트 루프 + 입점 예정: knot·요금가드).
- 결정적 설치기 store.py: 마커 멱등 append, 코너 기반 배타(설치 시점 거부), 딸린 파일 복사, multi-agent-starter init.py 위임.
- 입점 양식(fragments/_TEMPLATE) — 새 구성 추가 = 조각 폴더 하나.
