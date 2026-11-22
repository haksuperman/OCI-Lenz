# 산출물의 생성·검증 안내
입력: AGENTS.md, HARNESS/PRD/ARCHITECTURE/ADR, Draw.io/OCI 스킬,
architecture.py, draw.py, scope-heading/출력/네이티브 검증 테스트.
인터페이스: AI provider provenance 또는 진단 생성 → 모든 native 페이지 하단
편집 가능한 검증 안내 → 같은 Draw.io 파일의 PNG.
범위: AI 활용 및 실제 OCI 리소스·설정 대조 후 사용 안내. AI 미사용 진단은
자동 생성으로 구분한다. 프레임/리소스/연결선 geometry를 변경하지 않는다.
AC: 모든 페이지·AI/진단 구분·좁은 페이지 줄바꿈·검증·레거시 호환 회귀,
전체 테스트 및 같은 파일의 실제 PNG에서 안내/잘림 확인.
금지: 고객 정보/인증정보 공개, 실제 OCI 호출, 기존 연결선/배치 변경,
AI 미사용 결과를 AI 생성으로 허위 표시, 자동 머지, phase 상태 조작.
현재 PR 추가 커밋·푸시는 사용자의 수정 요청에 따른다.
