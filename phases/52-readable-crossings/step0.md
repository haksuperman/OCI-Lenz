# 짧은 직각 경로와 명시적 교차
입력: AGENTS.md, HARNESS.md, PRD.md, ARCHITECTURE.md, ADR.md, routing.py,
quality.py, connector_rules.py 및 기존 연결선 회귀 테스트.
인터페이스: 동일 근거 그래프/AI 좌표 → 길이·꺾임 중심 라우팅 → 네이티브
jumpStyle=arc → 표시 가능한 교차와 모호한 접촉을 구분한 품질 평가 → PNG.
범위: 짧은 직선, 공유 분기, 일정한 열린 화살표, 안전한 교차의 점프 아치.
AC: index.json 테스트, 교차 강제 가상 PNG와 기존 실제 배치의 재생성 비교.
금지: 글자/아이콘 관통 허용, 임의 관계 생성·삭제, 고객사 좌표 예외, 고객사
원본 공개, XML 구문 오류가 있는 참고 원본의 임의 수정, 자동 commit/push.
공통 API 의미는 유지하며, raw 교차 수는 계속 보고하고 아치만으로 안전을
선언하지 않는다. 끝점·꺾임 근접·공선 겹침은 안전한 교차로 분류하지 않는다.
