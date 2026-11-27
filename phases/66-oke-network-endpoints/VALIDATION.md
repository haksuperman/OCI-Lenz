# 검증 근거

- OKE 전용 회귀 16개를 추가했다. SDK의 GET transport와 2페이지 List,
  성공 0건/권한 실패/상세 실패, Summary 중첩 필드 fallback과 명시적 빈 값,
  응답 ID/컴파트먼트 충돌, URL/IPv6의 IP-only 처리와 비밀 필드 제외를 검증한다.
- 실제 Subnet/VCN/컴파트먼트 fallback, 공식 74번 native 아이콘, 역할/IP 라벨,
  익명화/모델 별칭, 부적절한 부모 변경 거부, 기존 VM 중복 없음/추측선 없음,
  여러 선택 컴파트먼트의 정확한 Pod Subnet 참조와 Flannel 제외를 검증했다.
- 최종 전체 444개 테스트가 SDK 2.192.0과 최소 지원 2.191.0에서 통과했다.
  하네스 구조 check 및 git diff --check도 통과했다. phase 상태는 실행기가 관리한다.
- 공개 CLI의 oke 가상 시나리오로 실제 native Draw.io/PNG를 생성했다.
  AI 미사용 진단 배치는 needs_review이며 AI 수용 결과와 구분한다.
- 공개형 API Endpoint/Private 워커와 두 종류의 위치 미확인 fallback을 포함한
  최종 신규 Codex AI 배치는 코드 품질 clear, AI 시각 검토 accepted였다.
  자원/제목 침범, 겹침, 대각선, 화살촉 혼잡, 짧은 단말, 통로 부족 모두 0이다.
  이는 해당 가상 예제의 결과이며 실환경 모든 배치 품질을 보증하지 않는다.
- 세 OKE 아이콘의 실제 부모와 공식 아이콘 출처를 확인했고, OKE에 연결된
  근거 없는 통신 화살표가 없음을 검사했다. API Endpoint만 IP를 보여주고
  위치 미확인 두 아이콘은 이름/역할만 표시한다. Node Pool 프레임도 없다.
- 같은 snapshot/layout의 XML 정확한 재생성, 전체 PNG payload/CRC/metadata
  검증 통과. architecture.png(1056×811)와 부록(1154×1330)을 확인했다.
  공식 아이콘·라벨·Endpoint/Pod Subnet 역할·생성 검증 안내의 잘림이 없다.
- 일반 패키지 설치 후 저장소 밖 isolated Python으로 CLI 재생성 및 설치 모듈의
  소스 일치를 확인했다. 설치된 생성기의 XML도 체크아웃 결과와 정확히 같다.
- 실제 OCI 재조회, kubeconfig/Kubernetes API, 인증정보/고객사 자료 공개와
  commit/push는 수행하지 않았다. 가상 산출물은 저장소 밖 검증 경로에 유지한다.
