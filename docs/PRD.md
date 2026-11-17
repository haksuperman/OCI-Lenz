# OCI-Lenz requirements

OCI 테넌시의 읽기 전용 인벤토리에서 편집 가능한 Draw.io와 공유용 PNG를 생성한다.

첫 버전: 전체 환경을 담은 아키텍처 한 페이지와 선택적인 VCN별 상세 페이지,
VCN·Subnet·Compute·LB·Internet/NAT/Service Gateway,
Route Table 목적지/다음 홉, NSG와 LB Backend Set 관계를 포함한다.
Oracle 공식 아이콘을 사용하고 같은 Draw.io에서 PNG를 내보낸다.
DB, OKE, DRG, 피어링은 후속 범위다.

가상 데이터 산출물은 실제 OCI 접근 없이 검증한다. 실제 조회는 리전·컴파트먼트·프로필이
지정되었을 때만 수행한다. 공유용 익명 PNG는 `--redact`로 별도 생성한다.

운영용 로컬 구성도에는 실제 리소스 이름과 관측된 IP·CIDR·백엔드 주소를 표시한다.
공유용 익명화는 `--redact`로 명시하며 운영용 생성 경로에 자동 적용하지 않는다.
GitHub 공개 예시는 가상 데이터로 생성하고, 고객사 산출물은 저장소 밖에 보관한다.

로컬 OCI 프로필을 사용하며, Codex Draw.io 스킬과 공식 아이콘으로 작성한다. 고객사 등록 웹 서비스는 범위에 포함하지 않는다.

조회 범위는 리전과 명시한 하나 이상의 컴파트먼트로 지정한다. VCN 단위
수집 필터는 제공하지 않고 지정 범위의 모든 지원 대상 리소스를 보존한다.
