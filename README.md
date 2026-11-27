# OCI-Lenz

OCI 테넌시에 배포된 리소스를 읽기 전용으로 조회하고, **Codex Draw.io 스킬과 Oracle 공식 OCI 아이콘**으로 편집 가능한 Draw.io 다이어그램과 PNG를 생성합니다. 아키텍처 예시 사진을 함께 전달해 배치·표현의 기준으로 사용할 수 있습니다.

```text
로컬 OCI API 프로필 → Python SDK 조회 → 리소스·관계 스냅샷
                                      ↓
           AI + Draw.io 스킬 지침 + 참고 이미지 → 배치 JSON
                                      ↓
           Python 생성기 + Oracle 공식 아이콘 → architecture.drawio
                                      ↓
           Draw.io Desktop 내보내기 명령 → architecture.png
```

## 다이어그램을 만드는 방식

OCI-Lenz는 Computer Use로 Draw.io 화면을 클릭하거나 도형을 드래그하지 않습니다.
AI가 배치를 설계하고, Python 코드가 편집 가능한 Draw.io XML을 작성합니다.

| 구성 요소 | 역할 |
| --- | --- |
| Draw.io 스킬 | AI에 제공하는 다이어그램 작성 지침입니다. 스킬 자체가 앱을 조작하는 프로그램은 아닙니다. |
| AI | 수집된 관계를 별칭으로 표현한 장면과 참고 이미지를 보고, 컨테이너·리소스 위치와 크기 및 연결선 경로를 JSON으로 제안합니다. 렌더링된 익명 미리보기를 검토하고 수정안을 제안하기도 합니다. |
| Python 생성기 | AI 배치에 실제 이름·IP와 Oracle 공식 아이콘을 적용해 `.drawio` XML을 생성합니다. API 관계와 배치 품질을 검증하고 직각 연결선을 처리합니다. |
| Draw.io Desktop | 생성된 동일 `.drawio` 파일을 명령줄 내보내기로 렌더링해 PNG를 만듭니다. |

현재 구현은 Draw.io 스킬의 지침을 읽어 AI에 전달하되, AI의 작성 결과를 배치 JSON으로 제한합니다.
AI가 최종 XML을 직접 작성하거나 Draw.io 앱 안에서 직접 그리는 구조가 아닙니다.
아이콘·라벨·연결선은 `.drawio`의 개별 편집 가능한 요소로 생성되므로 결과를 Draw.io에서 수정할 수 있습니다.

PNG 변환 중 Draw.io 앱이 실행되거나 창이 잠깐 보일 수 있습니다. 이는 Desktop 실행 파일의
내보내기 기능을 호출하기 때문이며, 화면을 인식해 마우스·키보드로 그리는 자동화는 사용하지 않습니다.

## 설치

Python 3.10+, Git, Draw.io Desktop이 필요합니다. AI는 사용자 본인의 Codex CLI 로그인 또는 OpenAI API 연결을 사용합니다. 실제 OCI 조회에는 로컬에 준비한 읽기 전용 OCI SDK 프로필을 사용합니다. 고객사 OCI 인증정보를 앱에서 등록하거나 OAuth로 관리하지 않습니다.

```sh
git clone https://github.com/haksuperman/OCI-Lenz.git
cd OCI-Lenz
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
```

서버의 Draw.io 실행 경로는 `DRAWIO_BIN`으로 지정합니다. Linux의 화면 없는 환경에서는 Draw.io Desktop과 Xvfb가 필요합니다. 자세한 설치·의존성·진단 방법은 [사용 문서](docs/USAGE.md)를 참고하세요.

처음 사용하는 경우 [설치·AI 연결·Agent 사용 안내](docs/ONBOARDING.md)를 따라 가상 데이터부터 확인하세요. `oci-lenz doctor`는 설치 자산·AI 연결 준비·Draw.io 상태를 확인하며 OCI를 조회하지 않습니다.

## 가상 환경으로 실행

```sh
oci-lenz sample --output /tmp/oci-lenz-sample
oci-lenz draw --snapshot /tmp/oci-lenz-sample/snapshot.json --output /tmp/oci-lenz-diagram
```

기본 `draw`는 AI가 전체 컨테이너·리소스 좌표와 연결선 경로를 설계합니다. 고객사 정보가 없는 기본 참고 이미지를 함께 보내며, 별도 사진은 `--references /path/to/sanitized-images`로 지정합니다. 앱은 공식 아이콘과 실제 이름·IP를 적용하고 겹침·경계·관계를 검증합니다. 잘못된 배치는 AI에 최대 두 번 수정 요청하며 실패를 고정 배치로 숨기지 않습니다. PNG는 동일 Draw.io 파일에서 내보내며 원본을 보존합니다.

사용자별 AI 연결을 선택할 수 있습니다. API 키는 로컬 비밀 관리 도구를 통해 `OPENAI_API_KEY` 환경변수로 주입하고 저장소에 기록하지 않습니다.

```sh
codex login
oci-lenz draw --snapshot /local/private-snapshot/snapshot.json \
  --output /local/private-diagram --ai-provider codex --model YOUR_CODEX_MODEL
# API 방식: 실행 환경에 OPENAI_API_KEY가 준비되어 있어야 합니다.
oci-lenz draw --snapshot /local/private-snapshot/snapshot.json \
  --output /local/private-diagram --ai-provider openai --model YOUR_API_MODEL
```

`--model`을 생략한 Codex 방식은 해당 사용자의 로컬 모델 설정을 사용합니다. 상세 주소가 많은 리소스는 구성도 카드와 전체 정보 부록으로 나누며, 실제 이름과 수집 정보는 부록에도 그대로 보존합니다.

서비스 단위로 여러 VCN을 묶으려면 저장소 밖의 그룹 JSON을 `--groups`로 지정합니다. 그룹을 지정하지 않으면 API Compartment와 확인된 연결 관계를 사용합니다. 리소스 이름만 보고 업무 소유 관계를 추측하지 않습니다.

새 PNG 생성은 익명화된 배치 미리보기를 AI가 검토하고, 기본 최대 한 번의 수정과 채택한 수정본의 최종 확인을 거칩니다. 코드가 교차·겹침·간격·컨테이너 내부 여백·카드 크기·정렬을 평가하며, 점수가 개선되고 교차·침범 등이 늘지 않은 수정본만 채택합니다. 측정된 문제가 남으면 AI 판단과 별개로 검토 필요로 기록합니다. 실제 이름·IP가 표시된 고객사 PNG는 자동 업로드하지 않습니다. `visual-review.json`에서 검토 결과와 수정본 채택 이유를, `validation.json`에서 최종 품질 수치를 확인할 수 있습니다. `--review-rounds 0`으로 AI 검토를 끌 수 있으며 저장된 배치 재사용도 추가 모델 호출 없이 동작합니다. 반복 신규 생성 검증은 [사용 문서](docs/USAGE.md#배치-품질과-반복-신규-생성-검증)를 참고하세요.

모델 호출 없이 저장된 배치를 재사용할 수 있습니다.

```sh
oci-lenz draw --snapshot /tmp/oci-lenz-sample/snapshot.json \
  --reuse-layout /tmp/oci-lenz-diagram/skill-layout.json --output /tmp/oci-lenz-repeat
```

## 실제 OCI 환경 조회

```sh
oci-lenz collect --profile READONLY --region REGION \
  --compartment-id COMPARTMENT_OCID --output /local/private-snapshot
oci-lenz draw --snapshot /local/private-snapshot/snapshot.json \
  --references /local/reference-images --output /local/private-diagram
```

조회 범위는 리전과 컴파트먼트로 지정하며, 지정한 컴파트먼트의 지원 대상 리소스를 VCN 필터 없이 수집합니다. 여러 컴파트먼트는 `--compartment-id`를 반복해 지정합니다. `--config-file`로 로컬 프로필 파일 경로를 선택할 수 있습니다. 키·암호는 SDK가 로컬 프로필에서 참조하고 AI 입력으로 전달하지 않습니다. 고객사마다 프로필·조회 범위·출력 디렉터리를 분리합니다. IAM 정책 변경은 수행하지 않습니다. API별 권한은 [IAM 문서](docs/IAM.md)에 정리했습니다.

## 표시 범위와 결과

선택한 리전·컴파트먼트의 지원 대상 리소스를 하나의 아키텍처 페이지에 표시합니다. VCN·Subnet 경계는 유지하며, VCN별 상세 페이지는 `--detail-pages`로 추가할 수 있습니다.

### OCI 서비스별 지원 범위

OCI 콘솔 대분류별로 구현된 서비스를 정리했습니다.

| OCI 콘솔 대분류 | 지원 서비스 |
| --- | --- |
| Networking | VCN · Subnet · IGW · NAT Gateway · SGW · Route Table · NSG · LB · NLB · DRG · LPG · RPC · Site-to-Site VPN · CPE · FastConnect |
| Compute | Compute Instance · VNIC |
| Storage | File Storage · Object Storage |
| Oracle AI Database | Base DB(DBCS) · ExaCC · ExaCI(ExaCS) · Exascale · Autonomous AI Database(ADB) · GoldenGate |
| Databases | MySQL HeatWave · PostgreSQL · OCI Cache · NoSQL Database · OpenSearch |
| Developer Services | Kubernetes Engine(OKE) · API Gateway · OCI Functions · Container Registry · DevOps |
| Identity & Security | Regional WAF · Edge WAF(WAAS) |

### 생성 파일

| 파일 | 내용 |
| --- | --- |
| `architecture.drawio` | 리소스·라벨·연결선을 편집할 수 있는 원본 |
| `architecture.png` | 전체 아키텍처 이미지 |
| `information-index.png` | 수집 정보 부록 |
| `coverage.json` | 서비스/API별 조회 상태와 건수 |
| `skill-layout.json` | AI 배치 좌표와 경로; `--reuse-layout`으로 재사용 |
| `validation.json` · `visual-review.json` | 관계·배치 품질 검증과 AI 시각 검토 결과 |
| `vcn-N.png` | `--detail-pages`를 지정한 경우의 VCN별 상세 이미지 |

서비스별 상세 범위와 권한은 [사용 문서](docs/USAGE.md)와 [IAM 문서](docs/IAM.md)를 참고하세요. 버킷·컨테이너 이미지·파일의 콘텐츠, 실행 변수, VPN 공유 비밀·장비 설정은 수집하지 않습니다.

예시 사진은 시각적 기준입니다. 리소스나 연결의 존재는 OCI 응답을 기준으로 판단하며 실제 트래픽 도달성을 보장하지 않습니다. DB Home·일반 Database/PDB 카탈로그·Data Guard, Kubernetes 내부 워크로드, DRG 내부 라우팅 정책은 후속 범위입니다. DB 서비스별 범위와 가상 예제는 [사용 문서](docs/USAGE.md#확장-db-서비스)를 참고하세요. 피어가 지정 범위 밖이면 자동 조회하지 않고 `대상 미확인`으로 표시합니다.

기본 구성도는 운영용으로 실제 리소스 이름과 수집된 IP·CIDR·백엔드 주소를 표시합니다. 고객사 PNG·Draw.io 파일·스냅샷은 모두 저장소 밖에 보관하세요. GitHub 예시는 가상 데이터로 생성합니다. 별도 공유용 PNG가 필요하면 `draw --redact`로 이름과 IP를 숨길 수 있지만, XML에는 내부 식별자가 남으므로 익명화된 공개 파일로 취급하면 안 됩니다. PNG에는 원본 XML을 포함하지 않습니다. 표시 모드와 관계없이 AI에는 별칭과 리소스 유형·관계만 전달하며, 참고 사진은 사용자가 명시적으로 지정한 경우 전달합니다.

규모와 연결 형태가 다른 가상 환경에서 AI로 생성한 [Draw.io·PNG 예시와 재현 방법](artifacts/ai-quality/README.md)을 제공합니다. 실제 고객사 환경, Linux 서버 실행 및 사용자 제공 사진에 대한 스타일 검수는 해당 환경·입력으로 추가 검증해야 합니다. 복잡하거나 큰 환경의 배치는 추가 개선이 필요합니다.

## 개발 문서

- [개발 및 테스트](CONTRIBUTING.md)
- [설치·실행·제약사항](docs/USAGE.md)
- [스킬 선정·출처](docs/SKILLS.md)
- [공식 아이콘 출처·매핑](assets/oci/SOURCE.md)
- [요구사항](docs/PRD.md) · [아키텍처](docs/ARCHITECTURE.md) · [설계 결정](docs/ADR.md)
