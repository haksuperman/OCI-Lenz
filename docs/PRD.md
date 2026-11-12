# OCI-Lenz requirements

OCI 테넌시의 읽기 전용 인벤토리에서 편집 가능한 Draw.io와 공유용 PNG를 생성한다.

첫 버전: 리전 요약과 VCN별 상세 페이지, VCN·Subnet·Compute·LB·Internet/NAT/Service Gateway,
Route Table 목적지/다음 홉, NSG와 LB Backend Set 관계를 포함한다.
Oracle 공식 아이콘을 사용하고 같은 Draw.io에서 PNG를 내보낸다.
DB, OKE, DRG, 피어링은 후속 범위다.

가상 데이터 산출물은 실제 OCI 접근 없이 검증한다. 실제 조회는 리전·컴파트먼트·프로필이
지정되었을 때만 수행한다. OCID와 IP는 공유 PNG에서 기본 숨김이다.

현재 phase는 개발 하네스만 제공한다. 수집기와 생성기는 아직 구현하지 않았다.
