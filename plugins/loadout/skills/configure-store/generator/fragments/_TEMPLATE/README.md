# 입점 양식 — 새 구성 추가하기

1. 이 폴더를 `fragments/<새이름>/` 으로 복사한다 (`_` 없이).
2. `meta.json`을 채운다. **corner가 배타 관계를 결정한다** — 같은 코너 품목과는 동시 설치 불가.
3. `fragment.md`에 규칙을 쓴다. 다른 구성과의 상호작용은 `[X도 설치된 경우]` 조건부 문단으로(별도 combo 품목 금지).
4. 딸린 파일이 있으면 `files/` 아래에 대상 폴더 기준 상대 경로로 둔다(설치 시 그대로 복사됨).
5. flavor별 차이가 필요할 때만: 조각 문구는 `fragment.codex.md`(codex에서 그걸 사용, 없으면 공용), 딸린 파일은 `files.codex/`(codex flavor에서만 추가 복사).
6. `python3 store.py --list` 로 카탈로그에 뜨는지 확인.
