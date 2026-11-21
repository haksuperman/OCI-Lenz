# Object Storage · Container Registry · DevOps
입력: AGENTS.md, docs/HARNESS.md, PRD.md, ARCHITECTURE.md, ADR.md,
collect.py, nosql.py, draw.py, model.py, tests/test_collect.py, 공식 library.xml.
인터페이스: 명시한 컴파트먼트의 List/Get 메타데이터 → 공통 regional kinds →
편집 가능한 공식 아이콘 Draw.io와 같은 XML을 렌더링한 PNG.
범위: 버킷/OCIR 저장소/DevOps 프로젝트·저장소·빌드·배포 파이프라인·배포 환경.
버킷은 GetBucket OCID를 사용하고 거부 시 안정적인 비OCID 목록 ID로 구분한다.
DevOps project_id만 연결 근거이며 실제 컴파트먼트 밖으로 소속을 추정하지 않는다.
AC: index.json의 테스트, 실제 SDK GET 페이지네이션, 거부/0건/선행실패 상태,
메타데이터 허용목록, 네트워크 추정 방지, 재생성 일치와 가상 PNG 시각 검증.
금지: 객체·이미지·소스코드·변수·인증정보·로그/실행 이력 저장, SGW/데이터 흐름/
배포 대상 추정, 테넌시 조회 범위 확대, IAM 쓰기, 고객사 공개, 자동 commit/push.
