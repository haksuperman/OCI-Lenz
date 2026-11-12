# OCI-Lenz

OCI 테넌시에 배포된 리소스를 읽기 전용으로 조회하고, **Codex Draw.io 스킬과 Oracle 공식 OCI 아이콘**으로 편집 가능한 Draw.io 다이어그램과 PNG를 생성합니다. 아키텍처 예시 사진을 함께 전달해 배치·표현의 기준으로 사용할 수 있습니다.

```text
로컬 OCI API 프로필 → Python SDK 조회 → 리소스·관계 스냅샷
                                      ↓
                  Codex Draw.io 스킬 + 공식 아이콘 + 예시 사진
                                      ↓
                          architecture.drawio + PNG
```

## 설치

Python 3.10+, Git, Draw.io Desktop, 인증된 Codex CLI가 필요합니다. 실제 OCI 조회에는 사용자가 로컬에 준비한 읽기 전용 OCI SDK 프로필을 사용합니다. 고객사 인증정보를 앱에서 등록하거나 OAuth로 관리하지 않습니다.

```sh
git clone https://github.com/haksuperman/OCI-Lenz.git
cd OCI-Lenz
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
```

서버의 Draw.io 실행 경로는 `DRAWIO_BIN`으로 지정합니다. Linux의 화면 없는 환경에서는 Draw.io Desktop과 Xvfb가 필요합니다. 자세한 설치·의존성·진단 방법은 [사용 문서](docs/USAGE.md)를 참고하세요.

## 가상 환경으로 실행

```sh
oci-lenz sample --output artifacts/sample
oci-lenz draw --snapshot artifacts/sample/snapshot.json --output artifacts/diagram
```

`draw`는 Codex를 실제 호출합니다. 예시 사진이 있으면 `--references /path/to/images`를 추가합니다. 스킬이 배치를 정하고 로컬 도우미가 공식 편집 가능 스텐실·컨테이너·연결선을 작성한 뒤 입력 관계와 검증합니다. PNG는 동일 Draw.io 파일에서 내보내며 원본을 보존합니다.

모델 호출 없이 저장된 배치를 재사용할 수 있습니다.

```sh
oci-lenz draw --snapshot artifacts/sample/snapshot.json \
  --reuse-layout artifacts/diagram/skill-layout.json --output artifacts/repeat
```

## 실제 OCI 환경 조회

```sh
oci-lenz collect --profile READONLY --region REGION \
  --compartment-id COMPARTMENT_OCID --output /local/private-snapshot
oci-lenz draw --snapshot /local/private-snapshot/snapshot.json \
  --references /local/reference-images --output /local/private-diagram
```

조회 시 선택적 `--vcn-id`, `--config-file`을 사용할 수 있습니다. 키·암호는 SDK가 로컬 프로필에서 참조하고 AI 입력으로 전달하지 않습니다. 고객사마다 프로필·조회 범위·출력 디렉터리를 분리합니다. IAM 정책 변경은 수행하지 않습니다. API별 권한은 [IAM 문서](docs/IAM.md)에 정리했습니다.

## 표시 범위와 결과

- 리전 인벤토리와 VCN별 상세 페이지
- Public/Private Subnet, Compute와 VNIC, Load Balancer와 Backend Set
- Internet/NAT/Service Gateway, Route 목적지·다음 홉, NSG 연결
- 범위 밖·모호한 관계의 `대상 미확인` 표시
- `architecture.drawio`, `region.png`, `vcn-N.png`, `coverage.json`, `validation.json`

예시 사진은 시각적 기준입니다. 리소스나 연결의 존재는 OCI 응답을 기준으로 판단하며 실제 트래픽 도달성을 보장하지 않습니다. DB·OKE·DRG·피어링은 후속 범위입니다.

공유 PNG는 OCID·IP와 원래 리소스 이름 대신 표시용 별칭을 사용하며 원본 XML을 포함하지 않습니다. Draw.io 파일·스냅샷에는 내부 식별자가 남으므로 고객사 결과는 저장소 밖에 보관하세요. AI에는 별칭과 리소스 유형·관계 및 사용자가 지정한 참고 사진을 전달합니다.

가상 환경의 실제 생성 예시는 [샘플 산출물](artifacts/sample)에 있습니다. 실제 고객사 OCI 조회, Linux 서버 실행 및 사용자 제공 사진에 대한 스타일 검수는 해당 환경·입력으로 추가 검증해야 합니다. 복잡하거나 큰 환경의 배치는 추가 개선이 필요합니다.

## 개발 문서

- [개발 및 테스트](CONTRIBUTING.md)
- [설치·실행·제약사항](docs/USAGE.md)
- [스킬 선정·출처](docs/SKILLS.md)
- [공식 아이콘 출처·매핑](assets/oci/SOURCE.md)
- [요구사항](docs/PRD.md) · [아키텍처](docs/ARCHITECTURE.md) · [설계 결정](docs/ADR.md)
