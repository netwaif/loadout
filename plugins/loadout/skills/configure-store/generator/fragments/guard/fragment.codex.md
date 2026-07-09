## goal 요금가드 (Codex)

`/goal` 자율 루프가 주간 사용량 한도에 닿으면 자동으로 멈추는 안전장치다. 판정 정책은 `coach`(usage-coach)가 단일 정본으로 갖고, Codex에서는 외부 워처 `_shared/guard/codex_goal_watch.mjs`가 그 결정을 집행한다(Codex `/goal` 런타임은 Stop 훅 정지를 무시 — 실측. 네이티브 정지 = `thread/goal/clear`).

- 전제: codexbar + `coach`(PATH에 있어야). 미설치·조회 실패·플래그 off는 전부 fail-open — 작업을 죽이지 않는다.
- 실행 3단계 (포트 셋이 같아야 함, 기본 47931):
  1. 가드용 ws app-server 기동: `codex app-server --listen ws://127.0.0.1:47931`
  2. `/goal` 세션을 그 서버에 attach해서 시작: `codex --remote ws://127.0.0.1:47931` (`--remote` 없이 띄우면 워처가 thread를 못 본다)
  3. 워처 실행: `node _shared/guard/codex_goal_watch.mjs`
- 런타임 스위치: `coach guard on` / `coach guard off` / 상태·미리보기 `coach guard status`.
- ⚠️ loopback ws 서버는 무인증(127.0.0.1 바인드만) — 신뢰된 단일 사용자 머신 가정, 원격 노출 금지.
- 상세(환경변수·동작·끄기): `_shared/guard/README.md`
- 받기 — coach: https://github.com/netwaif/usage-coach · codexbar: https://github.com/steipete/CodexBar
