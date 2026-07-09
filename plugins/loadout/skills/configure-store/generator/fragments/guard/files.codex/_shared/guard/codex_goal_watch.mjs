#!/usr/bin/env node
// codex_goal_watch.mjs — opt-in 요금가드 워처 (Codex flavor, 벤더중립 가드의 Codex 절반)
//
// 왜 워처인가: Claude는 Stop 훅(command, continue:false)으로 /goal 루프를 인-훅 정지할 수 있지만,
// Codex의 /goal 런타임은 Stop 훅 continue:false를 무시한다(실측). 네이티브 정지 = app-server
// JSON-RPC `thread/goal/clear`. 그래서 외부 워처가 폴링하다 한도 초과 시 활성 goal thread를 clear한다.
//
// 가드 *정책*은 워처가 갖지 않는다 — `coach --guard-check`(usage-coach)가 단일 정본으로 판정한다
// (guard-enabled 플래그·7일 하이브리드 OR·pace/floor 모두 거기서). 워처는 그 결정을 *집행*만 한다.
//   coach --guard-check 계약: 통과 = exit 0 + 무출력 / 정지 = exit≠0 또는 stdout에 사유 1줄.
//   coach 미설치/조회실패 = fail-open(정지하지 않음 — 작업 안 죽임).
//
// Transport(중요): codex의 app-server는 **loopback WebSocket**으로 붙는다. unix 소켓(control·
// --listen unix://)은 UDS 위 WebSocket이고 `app-server proxy`는 stdio↔UDS 얇은 바이트파이프라
// raw JSON-RPC가 안 통한다(실측). 그래서 워처는 `codex app-server --listen ws://127.0.0.1:PORT`로
// 띄운 서버에 **node 네이티브 WebSocket**으로 붙는다(의존성 0, 인증 0=loopback). 가드 대상 /goal
// 세션은 같은 서버에 `codex --remote ws://127.0.0.1:PORT`로 attach돼 있어야 워처가 그 thread를 본다.
// 절차 상세 = _shared/guard/README.md. ⚠️ loopback 무인증 → 같은 머신 로컬 프로세스가 제어 가능.
//
// 실행:  node _shared/guard/codex_goal_watch.mjs
// 환경:  GUARD_INTERVAL=초(기본 60) · GUARD_WS_PORT=포트(기본 47931) ·
//        GUARD_WS_URL=ws URL(기본 ws://127.0.0.1:$GUARD_WS_PORT) · GUARD_PROVIDERS=coach provider(기본 codex)
// 정지:  Ctrl-C. 가드 자체를 끄려면 `coach guard off`(워처는 coach 결정을 따르므로 즉시 무력화).

import { spawn } from "node:child_process";

const INTERVAL_MS = Math.max(5, parseInt(process.env.GUARD_INTERVAL || "60", 10)) * 1000;
const PORT = parseInt(process.env.GUARD_WS_PORT || "47931", 10);
const WS_URL = process.env.GUARD_WS_URL || `ws://127.0.0.1:${PORT}`;
const PROVIDERS = process.env.GUARD_PROVIDERS || "codex";

const log = (...a) => console.log(new Date().toISOString(), ...a);

// ── coach --guard-check: 단일 정본 판정. true=정지해야 함, false=통과/판정불가(fail-open) ──
function shouldStop() {
  return new Promise((resolve) => {
    // command -v 로 coach 부재 시 fail-open(정지 안 함). 셸 경유라 PATH 함정도 흡수.
    const sh = `command -v coach >/dev/null 2>&1 && coach --guard-check --providers ${PROVIDERS}`;
    const child = spawn("/bin/sh", ["-c", sh], { stdio: ["ignore", "pipe", "pipe"] });
    let out = "";
    child.stdout.on("data", (d) => (out += d));
    const timer = setTimeout(() => child.kill("SIGTERM"), 30000);
    child.on("close", (code) => {
      clearTimeout(timer);
      // coach 부재 → sh exit 0 + 무출력 → 통과. 정지 = exit≠0 또는 사유 출력.
      const stop = code !== 0 || out.trim().length > 0;
      resolve({ stop, reason: out.trim() || (code !== 0 ? `coach --guard-check exit ${code}` : "") });
    });
    child.on("error", () => { clearTimeout(timer); resolve({ stop: false, reason: "" }); });
  });
}

// ── app-server JSON-RPC over 네이티브 WebSocket(loopback) ──
let ws = null;
let nextId = 1;
const pending = new Map();

function request(method, params = {}, timeoutMs = 30000) {
  const id = nextId++;
  ws.send(JSON.stringify({ jsonrpc: "2.0", id, method, params }));
  return new Promise((resolve, reject) => {
    const t = setTimeout(() => { pending.delete(id); reject(new Error(`timeout ${method}`)); }, timeoutMs);
    pending.set(id, { resolve: (m) => { clearTimeout(t); resolve(m); }, reject: (e) => { clearTimeout(t); reject(e); } });
  });
}

function notify(method, params = {}) {
  ws.send(JSON.stringify({ jsonrpc: "2.0", method, params }));
}

// thread/loaded/list의 data 항목은 **thread ID 문자열**이다(실측). 객체로 올 경우도 방어.
const threadIdOf = (it) => (typeof it === "string" ? it : (it?.id || it?.threadId || it?.thread?.id || null));

// 현재 로드된 thread 중 active goal을 가진 것을 clear. 반환 = clear한 threadId 배열.
async function clearActiveGoals(reason) {
  const cleared = [];
  let cursor = null;
  do {
    const r = await request("thread/loaded/list", cursor ? { cursor } : {});
    const data = r?.result?.data || [];
    for (const it of data) {
      const tid = threadIdOf(it);
      if (!tid) continue;
      let goal = null;
      try { goal = (await request("thread/goal/get", { threadId: tid }))?.result?.goal; } catch { continue; }
      if (!goal) continue; // goal 없음 → 건너뜀
      try {
        const c = await request("thread/goal/clear", { threadId: tid });
        if (c?.result?.cleared) { cleared.push(tid); log("[CLEARED]", tid, "—", reason); }
      } catch (e) { log("[clear.error]", tid, String(e)); }
    }
    cursor = r?.result?.nextCursor || null;
  } while (cursor);
  return cleared;
}

async function tick() {
  let decision;
  try { decision = await shouldStop(); } catch { return; } // 판정 실패 → fail-open
  if (!decision.stop) return;
  log("[GUARD]", "한도 초과 판정 —", decision.reason, "→ 활성 goal thread clear 시도");
  try { await clearActiveGoals(decision.reason); } catch (e) { log("[guard.error]", String(e)); }
}

function main() {
  ws = new WebSocket(WS_URL);
  ws.onmessage = (ev) => {
    const raw = typeof ev.data === "string" ? ev.data : ev.data.toString();
    let msg; try { msg = JSON.parse(raw); } catch { return; }
    if (Object.prototype.hasOwnProperty.call(msg, "id") && pending.has(msg.id)) {
      const e = pending.get(msg.id);
      pending.delete(msg.id);
      e.resolve(msg);
    }
  };
  ws.onopen = async () => {
    try {
      await request("initialize", {
        clientInfo: { name: "codex-goal-guard-watch", version: "1" },
        capabilities: { experimentalApi: true, requestAttestation: false },
      });
      notify("initialized", {});
    } catch (e) { log("[initialize.error]", String(e)); process.exit(1); }
    log("요금가드 워처 시작 —", WS_URL, "interval", INTERVAL_MS / 1000 + "s, providers", PROVIDERS,
        "(가드 on/off는 `coach guard on/off`)");
    await tick();
    setInterval(tick, INTERVAL_MS);
  };
  ws.onerror = (e) => log("[ws.error]", e?.message || String(e),
    `— ws 서버(${WS_URL})가 떠 있는지 확인: codex app-server --listen ws://127.0.0.1:${PORT}`);
  ws.onclose = () => { log("[ws.close] 종료"); process.exit(1); };
}

process.on("SIGINT", () => { log("종료합니다."); try { ws?.close(); } catch {} process.exit(0); });
main();
