# OKE 네트워크 표현
입력: AGENTS.md, HARNESS/PRD/ARCHITECTURE/ADR, Draw.io/OCI 스킬,
수집기·관계 모델·부모 배치·표시·공식 아이콘·테스트 구조, OCI OKE 공식 API/IAM.
인터페이스: 선택 컴파트먼트 List/Get Cluster/NodePool → 허용된 네트워크 메타데이터
→ OKE 공식 74번 아이콘/관측 API Endpoint IP → 같은 native Draw.io/PNG.
범위: 확인된 API Endpoint Subnet에 클러스터명/역할/IP, 미확인 시 확인된 VCN
또는 실제 컴파트먼트에 아이콘만. 기존 Compute 재사용, 확인된 VCN-native Pod
Subnet 역할 표시. Pool은 네트워크 근거만 보존하고 별도 도형/통신선은 추가하지 않는다.
AC: GET·페이지네이션/실패·0건·필드 허용 목록/부모 fallback/아이콘·익명화/
워크 노드 중복 없음/추측선 없음/전체 테스트·실제 가상 XML/PNG·정확한 재생성.
금지: kubeconfig·Kubernetes 내부 API·키·토큰·SSH/환경/태그 원문 저장,
실제 OCI 무단 재조회, 범위 밖 열거, Control Plane VM/Pod/가상 노드 추측,
NodePool frame/OKE→워커 통신선·자동 게이트웨이 연결, 자동 commit/push/merge.
