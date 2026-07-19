![loadout](assets/banner.png)

# loadout — CLAUDE.md 구성 백화점

작업 폴더 성격에 맞는 CLAUDE.md 구성을 카탈로그에서 **골라 담는** 조합형 설치기.
Claude Code(CLAUDE.md)와 Codex CLI(AGENTS.md, `--flavor codex`) 둘 다 지원.

| 품목 | 코너 | 비고 |
|------|------|------|
| 카파시 4원칙 | 행동 규율 | 조건부: 멀티=층별 적용 / Fable5=번역 |
| Fable5 단독 | 실행 구조 | 멀티와 상호배타 · claude 전용(codex 미지원) |
| 멀티에이전트 | 실행 구조 | multi-agent-starter 플러그인에 위임 |
| 에이전트 루프 | 자율성 | goal-prompt·채점표 템플릿 딸림 |
| knot 지식 vault | 지식 관리 | 자동층 조각(능동 스킬=multi-agent-starter) |
| goal 요금가드 | 비용 통제 | claude=Stop 훅 / codex=워처 복사(coach 필요) |
| 세션 이어가기 | 세션 연속성 | SESSION.md 체크포인트·재정박 |
| 예스맨 금지 | 소통 태도 | 반사적 동의 금지 — 검증 후에만 근거 붙여 동의 |
| 저비용 Fable 5 · GPT 5.6 | 모델 운용 | Effort 상한·역할 분리·기획 선행 / codex 카탈로그명="저비용 GPT 5.6" |

**규칙**: 같은 코너 = 상호배타, 코너가 다르면 조합 자유. 조합 품목은 없다 — 조각 안 `[X도 설치된 경우]` 조건부 문단이 조합을 처리한다.

## 설치

Claude Code 또는 Codex CLI 마켓플레이스로 이 repo를 추가하면 `configure-store` 스킬이 로드된다.
"CLAUDE.md 구성 골라 담아줘"로 시작.

수동 실행:
```bash
python3 plugins/loadout/skills/configure-store/generator/store.py --list
python3 plugins/loadout/skills/configure-store/generator/store.py \
  --target <폴더> --pick karpathy,agent-loop --yes          # Codex 폴더면 --flavor codex 추가
```

## 반품 (remove)

설치의 역방향 — 마커 블록 제거 + 딸린 파일은 정본 바이트 일치 시만 삭제(수정본 보존).
`--pick` 병용 시 제거를 먼저 실행해 같은 코너 갈아타기가 한 호출로 끝난다.

```bash
python3 plugins/loadout/skills/configure-store/generator/store.py \
  --target <폴더> --remove fable5-solo --pick multiagent --yes   # 코너 스왑
```

multiagent는 반품 미지원(사용자 작업물이 얽힌 스캐폴드 — 수동 정리 안내).

## 진단 (doctor)

설치 상태를 읽기 전용으로 점검한다 — 아무것도 고치지 않는다.

```bash
python3 plugins/loadout/skills/configure-store/generator/store.py --target <폴더> --doctor
```

`[FAIL]` 마커 짝 깨짐·블록 중복·코너 배타 위반(exit 1) / `[WARN]` 조각이 카탈로그 최신본과 다름·딸린 파일 유실·guard/multiagent 전제조건 미비(exit 0). stale·유실은 해당 품목 재설치(멱등)로 복구.

## 새 구성 입점

`plugins/loadout/skills/configure-store/generator/fragments/_TEMPLATE/README.md` 참조.

## License

MIT — `NOTICE` 참조(카파시 4원칙 출처 포함).
