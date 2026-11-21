# 백엔드셋 소유 상태 표시
입력: AGENTS.md, docs/HARNESS.md, PRD.md, ARCHITECTURE.md, ADR.md,
collect.py, load_balancers.py, diagram_model.py, architecture.py, typography.py.
인터페이스: ListBackends의 성공/실패 → 최소 상태 필드 → 근거 그래프 유지 →
백엔드셋 하단에 고정된 네이티브 라벨 → 동일 Draw.io와 PNG.
범위: 빈 성공, 조회 실패, 기존 상태 미상, 미확인 타깃 개수 구분.
미확인 백엔드와 연결의 원본 셀은 숨겨서 편집·검증 근거를 보존한다.
AC: index.json 테스트, 가상 및 기존 수집 스냅샷 PNG 검증.
금지: OCI 재조회/쓰기, 대상/소속 추론, API 관계 삭제, 고객사별 좌표 예외,
고객사 산출물 공개, 자동 commit/push. 저장 배치의 크기가 달라지면 재생성한다.
