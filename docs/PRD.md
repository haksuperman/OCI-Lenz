# OCI-Lenz requirements

OCI 테넌시의 읽기 전용 인벤토리에서 편집 가능한 Draw.io와 공유용 PNG를 생성한다.

첫 버전: 전체 환경을 담은 아키텍처 한 페이지와 선택적인 VCN별 상세 페이지,
VCN·Subnet·Compute·LB·Internet/NAT/Service Gateway,
Route Table 목적지/다음 홉, NSG와 LB Backend Set 관계를 포함한다.
Oracle 공식 아이콘을 사용하고 같은 Draw.io에서 PNG를 내보낸다.
DRG·Attachment, LPG·RPC의 구성 관계까지 수집한다. 범위 밖 피어를 자동 조회하거나
VCN 간 전이 연결을 추론하지 않는다. Oracle Base DB의 DB System·Node·VNIC도 수집하며,
기본 구성도에는 System Display Name과 Node IP만 표시한다. Exadata·Exascale·다른 DB
서비스와 OKE, DRG 라우팅 정책은 후속 범위다.
FastConnect Virtual Circuit·Cross-Connect Group·Cross-Connect를 읽기 전용으로 수집하고 공식 FastConnect 심볼로 표시한다.
Attachment는 내부 API 관계 근거로 유지하고 도형·이름·경계는 모든 페이지에서 제외한다.
VCN–DRG–IPSec/Remote Peering 관계를 검증된 직접 연결선으로 표시한다.
IPSec VPN의 CPE·연결·터널과 DRG Attachment 관계도 수집한다.
IPSec 연결은 컨테이너로 표시하고, API로 확인된 소속 터널을 그 안에 배치한다. DRG와 CPE는 밖에 둔다. 공유 비밀과 장비 설정은 조회하지 않는다.

가상 데이터 산출물은 실제 OCI 접근 없이 검증한다. 실제 조회는 리전·컴파트먼트·프로필이
지정되었을 때만 수행한다. 공유용 익명 PNG는 `--redact`로 별도 생성한다.

운영용 구성도 리소스 라벨에는 실제 리소스 이름과 관측된 대표 IP를 표시한다.
IP가 없으면 이름만 표시하며 VCN·Subnet 경계에는 CIDR을 유지한다. 포트·백엔드
주소 등 상세 설정은 정보 페이지에 보존하고 구성도에 추가 정보 안내 문구를 붙이지 않는다.
공유용 익명화는 `--redact`로 명시하며 운영용 생성 경로에 자동 적용하지 않는다.
GitHub 공개 예시는 가상 데이터로 생성하고, 고객사 산출물은 저장소 밖에 보관한다.

로컬 OCI 프로필을 사용하며, Codex Draw.io 스킬과 공식 아이콘으로 작성한다. 고객사 등록 웹 서비스는 범위에 포함하지 않는다.

조회 범위는 리전과 명시한 하나 이상의 컴파트먼트로 지정한다. VCN 단위
수집 필터는 제공하지 않고 지정 범위의 모든 지원 대상 리소스를 보존한다.

배치 균등성은 기본 전체 구성도의 코드 기반 품질 평가로 보완한다. AI 수정본은
동일 입력에서 점수가 개선되고 교차·침범 등이 증가하지 않을 때만 채택한다.
AI 검토가 통과하더라도 측정된 문제가 남으면 검토 필요로 표시한다. 반복 신규
생성의 실패와 품질 편차를 기록하며 모든 고객사에서 동일한 품질을 보장하지 않는다.
리소스 증감에 따라 기존 배치를 부분 갱신하는 기능은 후속 범위다.
