# OSN 추가 이전 배치로 복원
입력: AGENTS.md, docs/HARNESS.md, PRD.md, ARCHITECTURE.md, ADR.md, main 기준
수집/관계/배치 코드, 미커밋 GoldenGate 구현과 테스트, 기존 가상 배치.
인터페이스: 기존 스냅샷·수집기 → 원래 컴파트먼트/VCN/Subnet 배치 → 공통
편집 가능한 Draw.io·PNG. OSN 추가 이전의 기존 배치 파일도 검증한다.
범위: 사용자 요청에 따라 미커밋 OSN 영역·서비스 이동·endpoint 분류·스킬/
문서/가상 시나리오를 제거한다. GoldenGate와 이전 확장 서비스는 보존한다.
AC: index.json의 기존 서비스 소속·OSN 부재·GG 수집과 전체 회귀 검사, 기존
가상 스냅샷/배치 재사용과 실제 PNG 시각 검사, 설치 패키지 검증.
금지: GoldenGate 등 이전 구현 손실, 실제 OCI 조회·IAM 변경·인증정보 노출,
고객사 자료 공개, 새 AI 호출, 자동 commit/push.
