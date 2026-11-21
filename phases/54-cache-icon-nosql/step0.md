# Cache 공식 심벌과 NoSQL 테이블
입력: AGENTS.md, HARNESS.md, PRD.md, ARCHITECTURE.md, ADR.md, collect.py,
draw.py, model.py, managed_data.py, tests/test_collect.py 및 공식 library.xml.
인터페이스: 선택 컴파트먼트 ListTables → 최소 지역 테이블 메타데이터 →
해당 컴파트먼트/VCN 외부 배치 → 공통 편집 가능 Draw.io와 PNG.
범위: Cache에 Oracle 공식 자료가 재사용한 library 46번 NoSQL 심벌을 매핑.
NoSQL은 같은 공식 심벌을 쓰되 별도 kind와 API 소속을 유지한다. 이름·OCID·
컴파트먼트·lifecycle만 저장하고 List 성공 0건과 실패를 구분한다.
AC: index.json의 SDK 실제 메서드·페이지네이션·거부·NoSQL 단독/혼합 컴파트먼트·
부모·정보 보존·XML 재생성 검사, 가상 PNG와 설치 패키지 검증.
금지: GetTable/DDL/스키마/행·쿼리·인덱스 조회, IP/DNS/VCN/NSG/SGW 연결
추론, 테넌시 범위 확장·IAM 쓰기, 고객사 자료 공개, 자동 commit/push.
