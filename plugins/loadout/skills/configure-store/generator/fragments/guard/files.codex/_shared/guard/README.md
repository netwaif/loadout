# 요금가드 워처 (Codex flavor)

opt-in goal 요금가드의 **Codex 절반**. loadout 카탈로그의 guard 품목이 설치한다
(`store.py --pick guard --flavor codex` → 이 폴더가 대상의 `_shared/guard/`로 복사됨.
정본 = loadout `fragments/guard/files.codex/`, claude flavor Stop 훅도 같은 guard 품목이 병합).
가드 *정책*은 전부 `coach`(usage-coach)가 단일 정본으로 판정하고, 워처는 그 결정을 *집행*만 한다.

## 왜 워처인가 (Claude와 셋업이 다른 이유)
Claude는 Stop 훅(`continue:false`)으로 `/goal` 루프를 **인-훅** 정지한다 — 별도 프로세스 없이
`.claude/settings.json` 한 줄이면 끝. 반면 Codex의 `/goal` 런타임은 Stop 훅 `continue:false`를
무시한다(실측). 네이티브 정지 = app-server JSON-RPC `thread/goal/clear`. 그래서 Codex는 **외부 워처**가
폴링하다 한도 초과 시 활성 goal thread를 clear하는 3단계 셋업이 필요하다.

## Transport (중요)
codex app-server는 **loopback WebSocket**으로 붙는다. unix 소켓(control·`--listen unix://`)은 UDS 위
WebSocket이고 `codex app-server proxy`는 stdio↔UDS 얇은 바이트 파이프라 raw JSON-RPC가 안 통한다.
그래서 워처는 `codex app-server --listen ws://127.0.0.1:PORT`로 띄운 서버에 **node 네이티브
WebSocket**으로 붙는다(외부 의존성 0). 가드 대상 `/goal` 세션은 **같은 서버에 attach**돼 있어야 워처가
그 thread를 본다(TUI가 자체 embedded app-server로 뜨면 외부 워처가 못 본다 — 그래서 `--remote` 필수).

> ⚠️ **보안**: loopback ws 서버는 무인증(127.0.0.1 바인드만). 즉 **같은 머신의 로컬 프로세스는 누구나**
> 그 세션을 제어(goal clear 등)할 수 있다. 신뢰된 단일 사용자 머신 가정. 원격 노출 금지(필요 시 SSH 포워딩).

## 사전 준비
- **codexbar + `coach`**(가드 데이터·판정). `coach`가 PATH에 있어야 한다. 없으면 워처는 fail-open
  (아무것도 정지시키지 않음)으로 조용히 통과.
  - coach 설치: <https://github.com/netwaif/usage-coach> · codexbar: <https://github.com/steipete/CodexBar>
- **가드 켜기**: `coach guard on`(런타임 스위치, 벤더 무관 단일 플래그). 끄기=`coach guard off`,
  상태·미리보기=`coach guard status`.

## 실행 — Codex 3단계
포트는 셋이 **같아야** 한다(기본 47931, 바꾸려면 셋 다 같은 값).

1. **가드용 ws app-server 기동** (loopback 전용):
   ```bash
   codex app-server --listen ws://127.0.0.1:47931
   ```
2. **`/goal` 세션을 그 서버에 attach**해서 시작:
   ```bash
   codex --remote ws://127.0.0.1:47931
   ```
   (이렇게 띄운 세션에서 `/goal`로 자율 루프를 돌린다. `--remote` 없이 그냥 `codex`로 띄우면 워처가
   thread를 못 본다.)
3. **워처 실행**:
   ```bash
   node _shared/guard/codex_goal_watch.mjs
   ```
   환경변수(선택): `GUARD_INTERVAL`(폴링 주기 초, 기본 60) · `GUARD_WS_PORT`(기본 47931) ·
   `GUARD_WS_URL`(기본 `ws://127.0.0.1:$GUARD_WS_PORT`) · `GUARD_PROVIDERS`(coach provider, 기본 `codex`).

## 동작
`GUARD_INTERVAL`초마다 `coach --guard-check`로 판정 → 정지 판정이면 `thread/loaded/list`로 그 서버에
로드된 thread를 열거하고, goal이 있는 thread를 `thread/goal/clear`한다. 판정 통과·coach 부재·조회
실패는 전부 fail-open(정지 안 함).

## 끄기
- 임시: `coach guard off` (워처는 coach 결정을 따르므로 즉시 무력화 — 워처를 죽일 필요 없음).
- 완전: 워처 프로세스 Ctrl-C.
