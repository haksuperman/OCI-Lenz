# 공통 연결선 가독성 규칙
입력: AGENTS.md, docs/HARNESS.md, PRD.md, ARCHITECTURE.md, ADR.md,
routing.py, connector_rules.py, architecture.py, ai.py, quality.py와 관련 테스트.
인터페이스: API 관계 → 별칭 기반 근접·분기 힌트 → AI 배치 → 공통 직각 라우터
→ 동일 기준 품질 측정 및 PNG 검증.
범위: 모든 보이는 연결의 교차 회피, 같은 출발점의 분기만 공유, 미확인 대상
근접 배치 피드백, 병렬 분기 정렬. 기존 원본 좌표 재생성도 검증한다.
AC: index.json의 테스트, 가상 PNG 및 기존 실제 스냅샷 재렌더링 비교.
금지: OCI 재조회/쓰기, 관계·부모 변경, 서비스 소속 추론, 고객사별 좌표 예외,
원본 이미지·스냅샷 공개, AI 배치의 임의 이동, 자동 commit/push.
