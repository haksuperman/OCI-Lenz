# 검증 근거
- LB/NLB 공통 IP 관계 테스트 6개: 부가 ID 조회 상태/필드 미확인과 독립,
  서로 다른 PrivateIp ID 보유 여부와 무관한 등록 주소 근거, 중복·다른 VCN
  차단, 등록 Backend 정상 표시/익명화, 동일 VM 두 포트의 두 등록 관계 보존,
  IP가 있는 항목에서 추가 신원 API 미호출.
- 기존 IP 없는 NLB OCID 보완 조회 테스트 16개와 실제 SDK/기타 회귀를 포함한
  전체 392개 테스트가 SDK 2.192.0 및 최소 지원 2.191.0에서 통과했다.
- 실제 로컬 스냅샷에서 NLB를 LB 유형으로 대조한 IP 관계가 모두 동일함을 검증.
  고객사 이름·IP·OCID·그림은 저장소 밖 private 디렉터리에만 유지한다.
- 가상 nlb-backends CLI Draw.io/PNG 생성, 네이티브 라벨/부모/관계 검증,
  같은 snapshot/layout의 XML 정확한 재생성과 전체 PNG payload/CRC 검증 통과.
- 가상 PNG에서 등록 IP와 Set→Backend/VM 화살표, 실패 문구 제거, 잘림 없는
  라벨을 확인했다. 코드 품질 지표는 clear이나 AI 시각 검토는 unclear_flow로
  needs_review다. 제안된 수정안은 점수가 악화되어 원래 배치를 유지했다.
  시각 검토 통과로 보고하지 않으며 공통 연결선/배치의 추가 개선 대상으로 남긴다.
- 일반 패키지 설치 후 저장소 밖 isolated Python에서 공통 매칭 모듈의 실제
  site-packages 소스 일치 및 네이티브 라벨 smoke 검증 통과.
- 자동 commit/push를 수행하지 않았다. phase 상태는 실행기가 관리한다.
