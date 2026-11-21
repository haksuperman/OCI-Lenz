# OCI-Lenz requirements

OCI 테넌시의 읽기 전용 인벤토리에서 편집 가능한 Draw.io와 공유용 PNG를 생성한다.

첫 버전: 전체 환경을 담은 아키텍처 한 페이지와 선택적인 VCN별 상세 페이지,
VCN·Subnet·Compute·LB·Network Load Balancer(NLB)·Internet/NAT/Service Gateway,
Route Table 목적지/다음 홉, NSG와 LB Backend Set 관계를 포함한다.
Regional WAF는 Subnet 밖에서 API가 지정한 보호 대상 LB를 향해 연결한다.
Edge WAF(WAAS)는 선택된 기본 Origin/Origin Group을 수집하며, 유일한 관측 공개 IP
대상으로 연결하거나 미확인 논리 Origin으로 표시한다. DNS나 비공개 IP로 추정하지 않는다.
Oracle 공식 아이콘을 사용하고 같은 Draw.io에서 PNG를 내보낸다.
DRG·Attachment, LPG·RPC의 구성 관계까지 수집한다. 범위 밖 피어를 자동 조회하거나
VCN 간 전이 연결을 추론하지 않는다. Oracle Base DB의 DB System·Node·VNIC도 수집하며,
기본 구성도에는 System Display Name과 Node IP만 표시한다. MySQL, Autonomous DB,
ExaCC, ExaCI, Exascale의 인프라·클러스터·네트워크 관계도 수집한다.
DB Home·일반 Database/PDB 카탈로그·Data Guard, OKE, DRG 라우팅 정책은 후속 범위다.
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
동일 입력에서 점수가 개선되고 모호한 교차·겹침·침범 등이 증가하지 않을 때만 채택한다.
AI 검토가 통과하더라도 측정된 문제가 남으면 검토 필요로 표시한다. 반복 신규
생성의 실패와 품질 편차를 기록하며 모든 고객사에서 동일한 품질을 보장하지 않는다.
리소스 증감에 따라 기존 배치를 부분 갱신하는 기능은 후속 범위다.

연결선 공통 규칙: 모든 보이는 관계가 직각 경로와 교차·겹침 회피에 참여한다.
같은 LB/Backend Set/DRG에서 갈라지는 근거 있는 분기만 공통선을 허용하며 다른
소유자의 연결은 별도 통로를 사용한다. 미확인 대상은 단일 출발점이 확인될 때
그 근처에 배치하도록 AI에 요청하고 거리·병렬 분기 정렬을 품질 평가한다.
실제 부모 경계가 우선이며 근접 배치를 위해 Subnet/VCN 소속을 바꾸지 않는다.

LB/NLB의 미확인 백엔드는 독립적인 외부 리소스로 배치하지 않는다. 백엔드셋
네이티브 라벨 하단에 `백엔드 대상 미확인 (개수)`로 모아 고정 표시한다.
등록 목록 조회 성공 0건이면 백엔드셋만 표시하며, 실패는 `백엔드 조회 불가`,
성공 여부가 없는 기존 빈 스냅샷은 `백엔드 조회 상태 미확인`으로 구분한다.
기존 대상 노드·연결·근거는 숨겨진 편집 가능 XML과 내부 모델에 유지한다.

연결선은 짧은 직선과 단순한 직각 분기를 우선하고, 명확한 수직 교차는
Draw.io 네이티브 점프 아치로 표시한다. 교차를 없애기 위한 긴 우회·계단을
피하되, 글자·리소스 관통과 모호한 끝점 접촉·공선 겹침은 허용하지 않는다.
원래 교차 수와 아치로 구분 가능한 교차 수는 별도 지표로 유지한다.

OCI Cache(RedisCluster), OCI Database with PostgreSQL(DB System), Search with
OpenSearch(클러스터)도 선택 리전·컴파트먼트 범위에서 수집한다. Subnet·NSG는
반환된 ID로만 연결하고 대표 IP와 이름을 표시한다. PostgreSQL 연결 상세의
Primary/Reader/Instance 엔드포인트 IP를 허용 목록으로 보존한다. SQL·캐시 키·
검색 인덱스/문서·사용자/인증/백업/복제 설정과 인증서는 수집 범위에 넣지 않는다.

NoSQL은 선택 컴파트먼트의 ListTables 메타데이터(테이블 이름·OCID·소속·상태)만
수집한다. 실제 소속 컴파트먼트 안의 지역 서비스로 표시하고 VCN/Subnet/IP/
SGW·애플리케이션 연결을 추정하지 않는다. 데이터 행·스키마·DDL은 범위 밖이다.
Cache는 Oracle 공식 자료의 사례에 따라 기존 NoSQL 심벌을 재사용하며, 두
서비스의 리소스 종류와 API 관계는 합치지 않는다.

## Object Storage · Container Registry · DevOps
선택 리전·컴파트먼트의 Object Storage 버킷, Container Registry 저장소, DevOps
프로젝트·코드 저장소·빌드 파이프라인·배포 파이프라인·배포 환경 메타데이터를 지원한다.
리소스는 실제 컴파트먼트 안, VCN/Subnet 밖에 배치하고 API project_id만 프로젝트
소속 관계로 연결한다. 실행 순서·아티팩트 전달·SGW 사용·배포 대상을 추정하지 않는다.
객체·이미지·소스코드·빌드/배포 변수·연결 인증정보·로그·실행 이력은 수집하지 않는다.
