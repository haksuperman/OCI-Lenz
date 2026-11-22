# 가상 검증 근거
- 새 서비스 회귀 테스트 13개: 실제 SDK List/Get GET transport, 2페이지 조회,
  권한 거부/성공 0건/AD 의존성 실패, 상세 실패 보존, IPv6, 다중 Subnet,
  교차 컴파트먼트 참조, HTTP IP 중복/VCN 범위, 미지원 백엔드, 비밀 필드 제외.
- 전체 테스트 370개: OCI SDK 2.192.0과 최소 지원 2.191.0에서 통과.
- file-storage / api-gateway / functions / application-services 가상 진단 생성 통과.
  진단 경로는 AI 미실행이며 배치 품질은 needs_review로 구분된다.
- application-services 신규 Codex AI 생성: 시각 검토 accepted, 품질 clear.
  리소스/제목 침범 0, 비직각 선분 0, 선 겹침 0; 교차 1개는 arc jump로 구분.
- 같은 snapshot과 저장된 layout으로 XML 정확한 재생성, 전체 PNG payload/CRC와
  불필요한 metadata 부재 검증. PNG의 공식 아이콘·라벨·잘림을 직접 확인.
- 일반 패키지 설치 후 저장소 밖 isolated Python으로 CLI와 Draw.io/PNG 검증.
- 실제 OCI 고객사 재조회는 이 변경에서 수행하지 않았다. 실환경 서비스별
  리소스 수/관계 및 IAM 접근 확인은 다음 명시적 collect 작업에 남는다.
- 가상 산출물은 저장소 밖 application-services-20261122 검증 디렉터리에 보관.
  고객사 파일/참고 이미지, 키/프로필/원본 OCI 응답은 변경에 포함하지 않았다.
