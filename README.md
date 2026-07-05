# loadout — CLAUDE.md 구성 백화점

작업 폴더 성격에 맞는 CLAUDE.md 구성을 카탈로그에서 **골라 담는** 조합형 설치기.

| 품목 | 코너 | 비고 |
|------|------|------|
| 카파시 4원칙 | 행동 규율 | 조건부: 멀티=층별 적용 / Fable5=번역 |
| Fable5 단독 | 실행 구조 | 멀티와 상호배타 |
| 멀티에이전트 | 실행 구조 | multi-agent-starter 플러그인에 위임 |
| 에이전트 루프 | 자율성 | goal-prompt·채점표 템플릿 딸림 |
| knot / 요금가드 | 지식 관리 / 비용 통제 | 입점 예정 |

**규칙**: 같은 코너 = 상호배타, 코너가 다르면 조합 자유. 조합 품목은 없다 — 조각 안 `[X도 설치된 경우]` 조건부 문단이 조합을 처리한다.

## 설치

Claude Code 마켓플레이스로 이 repo를 추가하면 `configure-store` 스킬이 로드된다.
"CLAUDE.md 구성 골라 담아줘"로 시작.

수동 실행:
```bash
python3 plugins/loadout/skills/configure-store/generator/store.py --list
python3 plugins/loadout/skills/configure-store/generator/store.py \
  --target <폴더> --pick karpathy,agent-loop --yes
```

## 새 구성 입점

`plugins/loadout/skills/configure-store/generator/fragments/_TEMPLATE/README.md` 참조.

## License

MIT — `NOTICE` 참조(카파시 4원칙 출처 포함).
