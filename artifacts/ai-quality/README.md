# AI로 생성한 가상 아키텍처 예시

고객사 정보 없이 `oci_lenz.model.sample`과 `oci_lenz.synthetic`에서 만든
독립 가상 환경입니다. 고객사 참고 사진·원본 Draw.io·실제 수집 데이터는
사용하지 않았습니다. 이름, 주소, 관계는 모두 가상 데이터입니다.

Codex CLI의 로컬 모델 설정과 저장소의 Draw.io 스킬, Oracle 공식 편집 가능
아이콘, `assets/reference/layout-guide.png`를 사용했습니다. AI가 좌표를 설계하고
익명화된 PNG를 검토했으며, 실제 가상 리소스 라벨은 로컬에서 적용했습니다.
각 PNG는 옆의 `architecture.drawio`를 Draw.io Desktop으로 내보낸 결과입니다.

| 사례 | 구성 | PNG | 편집 원본 |
| --- | --- | --- | --- |
| basic | VCN 1개, Compute 1개, Backend Set 1개 | [architecture.png](basic/architecture.png) | [architecture.drawio](basic/architecture.drawio) |
| overview | 컴파트먼트 2개, VCN 3개 | [architecture.png](overview/architecture.png) | [architecture.drawio](overview/architecture.drawio) |
| fanout | Backend Set 3개, Compute 8개 | [architecture.png](fanout/architecture.png) | [architecture.drawio](fanout/architecture.drawio) |
| dense | Compute 24개, 빈 Subnet 4개 | [architecture.png](dense/architecture.png) | [architecture.drawio](dense/architecture.drawio) |

각 폴더에는 입력 `snapshot.json`, `coverage.json`, 최종 `skill-layout.json`,
AI의 `visual-review.json`, 생성 경로의 `validation.json` 및 정보 부록 PNG가
있습니다. [matrix-report.json](matrix-report.json)은 관계·경계 검증, 정확한 XML
재현, PNG 크기, 편집 가능한 라벨·벡터 그룹 수, 파일 SHA-256을 기록합니다.

## 재현

저장소 루트에서 가상환경과 Draw.io Desktop을 준비한 뒤 실행합니다.
저장된 예시는 모델 호출 없이 재검증할 수 있습니다.

```sh
python scripts/validate_scenarios.py --ai --resume \
  --case basic --case overview --case fanout --case dense --output artifacts/ai-quality
```

배치를 그대로 별도 경로에 렌더링하는 명령입니다. 추가 AI 호출은 없습니다.

```sh
oci-lenz draw --snapshot artifacts/ai-quality/fanout/snapshot.json \
  --reuse-layout artifacts/ai-quality/fanout/skill-layout.json \
  --output /tmp/oci-lenz-fanout-replay
```

사용자 본인의 AI로 새 결과를 생성하려면 저장소 밖의 새 출력 경로를 사용합니다.
AI가 새로 설계하는 배치는 실행마다 다를 수 있습니다. 동일한 배치를 재현하려면
`--reuse-layout`을 사용합니다.

```sh
python scripts/validate_scenarios.py --ai --case basic --case overview \
  --case fanout --case dense --output /tmp/oci-lenz-new-ai-quality
```

## 검수 범위와 한계

2026-11-17 생성 결과에서 리소스·근거 연결 보존, 공식 아이콘의 벡터 구성,
리소스 자체 라벨과 독립 연결선, 잘림·겹침 검증, 최종 배치의 XML 재현을
확인했습니다. PNG는 전체 청크·CRC·픽셀 데이터와 텍스트 메타데이터 부재를
검사합니다. 구성도 PNG를 직접 열어 아이콘 누락과 라벨 잘림도 확인합니다.
[inspection.json](inspection.json)에 사례별 육안 점검과 남은 디자인 관찰을
기록했습니다. 각 폴더의 `flow-design-validation.json`에는 연결선의 직교성,
네이티브 포트 정합성 및 다른 리소스·제목 침범 검사가 있습니다.
[편집 왕복 검증](editability-verification.json)은 fanout 사본의 라벨·아이콘 위치·
연결선 스타일을 수정한 뒤 Draw.io Desktop의 XML 내보내기로 해당 편집과
364개 셀 ID가 유지되는지 확인한 결과입니다. 수정 사본은 예시에 포함하지 않습니다.

`accepted`는 해당 익명화 미리보기에 대한 AI의 판정입니다. 모든 고객사 환경의
디자인 품질을 보증하거나 트래픽 도달성을 검증한 결과는 아닙니다. 작은 환경의
넓은 여백, 긴 연결선과 밀집 환경의 선 교차는 별도로 판단할 여지가 있습니다.
단일 리전의 현재 지원 유형만 다루며 DB·OKE·DRG·Peering 수집은 포함하지 않습니다.
