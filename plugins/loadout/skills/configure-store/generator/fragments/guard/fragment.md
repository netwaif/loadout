## goal 요금가드

`/goal` 자율 루프가 주간 사용량 한도에 닿으면 자동으로 멈추는 안전장치다. 판정 정책은 `coach`(usage-coach)가 단일 정본으로 갖고, 이 구성은 배선(.claude/settings.json Stop 훅)만 설치한다.

- 전제: codexbar + `coach`(PATH에 있어야). 미설치·조회 실패·플래그 off는 전부 fail-open — 작업을 죽이지 않는다.
- 런타임 스위치: `coach guard on` / `coach guard off` / 상태·미리보기 `coach guard status`.
- 받기 — coach: https://github.com/netwaif/usage-coach · codexbar: https://github.com/steipete/CodexBar
