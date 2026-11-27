# 검증 근거

- 사용자가 이전에 지정한 읽기 전용 프로필과 같은 리전/컴파트먼트 범위로
  공개 collect 경로를 재실행했다. 인증정보·원문 응답·고객사 식별자는 기록하지 않는다.
- OKE ListClusters/GetCluster/ListNodePools/GetNodePool 호출이 모두 성공했다.
  독립 SDK 재조회에서 인벤토리, Endpoint VCN/Subnet/NSG/관측 IP, NodePool
  워커 ID와 Pod Subnet 참조가 수집 결과와 일치했다. 알려진 Subnet의 Get도 대조했다.
- 실제 스냅샷으로 공개 AI draw 경로를 실행했다. Endpoint의 실제 부모,
  공식 OKE 아이콘, 실제 이름/Private IP, 공개 IP 미추가, 기존 워커 재사용,
  Pod Subnet 역할, Pool 프레임·추측 통신선 부재를 최종 XML에서 확인했다.
- 원본 식별자/IP를 모델 요청에 포함하지 않는지 검사했다. 실제 이름/IP가
  표시된 그림은 저장소 밖에 유지하고 로컬 시각 검토는 마스킹된 PNG로 수행했다.
- native XML/관계 검증, 같은 snapshot/layout의 정확한 재생성,
  전체 PNG payload/CRC 검증 통과. OKE 아이콘·역할·라벨 잘림은 확인되지 않았다.
- 전체 구성도에는 구분이 부족한 연결선 교차가 남아 코드 품질/AI 시각 검토는
  needs_review다. 자원/제목 침범·선 겹침·비직각·화살촉 혼잡·짧은 진입부·통로
  부족은 없지만 전체 배치의 시각 수용으로 과장하지 않는다.
- OKE와 별도인 DB API의 404가 coverage에 남아 있다. 정상 0건이나 모든 API
  조회 성공으로 보고하지 않는다. 자세한 건수·API 대조·배치 지표는 비공개
  live-validation.json과 api-comparison.json에 보관한다.
- 실제 조회 후 구현 코드 변경/commit/push/OCI 쓰기를 수행하지 않았다.
  하네스 구조와 git diff --check를 확인했으며 phase 상태는 실행기가 관리한다.
