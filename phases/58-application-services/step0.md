# File Storage · API Gateway · Functions
입력: AGENTS.md, docs/HARNESS.md, PRD.md, ARCHITECTURE.md, ADR.md, IAM.md,
collect.py, model.py, draw.py, application_services.py, 공식 library.xml, 기존 테스트.
인터페이스: 지정 리전·컴파트먼트 List/Get → 최소 snapshot → 공통 graph/AI layout
→ 편집 가능한 architecture.drawio → 동일 문서의 PNG.
범위: AD별 FileSystem/MountTarget, ExportSet ID 조인, 실제 MT Subnet/NSG/IP;
Functions Application/Function 소속과 관측 Subnet/NSG; API Gateway/Deployment와
Function OCID 또는 유일한 관측 HTTP IP 백엔드. 실패와 성공 0건을 구분한다.
AC: index.json의 SDK GET·페이지네이션·실패/0건·허용목록·교차 컴파트먼트·
다중 Subnet·모호한 IP 테스트, 전체 회귀 테스트, 가상 4개 시나리오 PNG/Draw.io
정확한 재생성과 공식 아이콘/잘림 시각 검사. AI 수용과 진단 통과는 구분해 보고.
금지: 실제 OCI 자동 재수집, NFS 클라이언트 마운트 추정, DNS/업무 소속 추정,
파일 내용·함수 코드/환경/이미지·호출·URL 인증/경로/쿼리·원본응답 저장,
OSN 재도입, IAM 쓰기, 자동 commit/push. MT는 공식 File Storage 심벌 재사용,
Export/Deployment는 논리 태그임을 명시. phase 상태는 실행기만 변경한다.
