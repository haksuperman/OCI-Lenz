# 검증 근거
- 새 NLB 보완 조회/표시 테스트 16개: 누락 Private IP/VNIC/Attachment/Instance,
  명시 Instance OCID, 단계별 실패와 범위 밖/ID·주소 충돌/모호한 Attachment,
  기존 인벤토리 재사용·중복 참조 캐시, 엄격한 IP-only fallback, 이전 단계에서
  확인한 identity를 뒤 단계 실패로 덮어쓰지 않음, 네이티브 부모, 익명화/AI 별칭.
- 전체 테스트 386개: OCI SDK 2.192.0 및 최소 지원 2.191.0에서 모두 통과.
- 가상 nlb-backends 진단 생성 통과. 진단 배치는 AI 수용 결과가 아님.
- 신규 Codex AI 생성/시각 검토 accepted, 품질 clear. 리소스·제목 침범,
  비직각 선분과 구분되지 않은 교차 0건. 공식 NLB 심벌, 등록 IP 논리 태그,
  실제 VM과의 연결, 라벨 잘림을 가상 PNG에서 확인했다.
- 같은 snapshot/layout의 XML 정확한 재생성 및 PNG 전체 payload/CRC/metadata 검증.
- 일반 패키지 설치 후 저장소 밖 isolated Python CLI XML/PNG 생성·재생성,
  최종 설치된 nlb_backends 모듈의 체크아웃 소스 일치 및 논리 태그 검증 통과.
- 실제 고객사 참조 조회/산출물은 저장소 밖 private 디렉터리에만 보관하며,
  실제 환경의 존재·권한·통신 가능 여부를 가상 테스트 결과로 보장하지 않는다.
- 자동 commit/push를 수행하지 않았다. phase 상태는 실행기가 관리한다.
