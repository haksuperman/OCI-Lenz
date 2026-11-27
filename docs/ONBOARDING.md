# 다른 사용자의 설치와 첫 실행

Python 3.10 이상과 Git이 필요합니다. PNG 생성에는 Draw.io Desktop이 필요합니다.
AI 배치는 본인의 Codex CLI 로그인 또는 OpenAI API 연결을 사용합니다.
가상 데이터의 로컬 진단에는 OCI 프로필과 AI 인증이 필요하지 않습니다.
고객사별 스냅샷·참고 원본·결과는 저장소 밖에 보관합니다.

## 1. 저장소와 가상환경 준비

```sh
git clone https://github.com/haksuperman/OCI-Lenz.git
cd OCI-Lenz
python3 --version
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python -m pip check
```

`python3`가 3.10 미만이면 먼저 설치한 지원 버전의 실행 파일로 가상환경을
만듭니다. `.venv`나 다른 사람의 로그인 파일을 복사하지 않습니다.

저장소 없이 설치 패키지만 사용할 때는 빌드된 wheel을 새 가상환경에 설치할
수 있습니다. 공식 아이콘·기본 참고 이미지·두 스킬은 패키지에 포함됩니다.
프로젝트 코드 개선과 `scripts/`의 개발 검증에는 clone한 저장소를 사용합니다.

## 2. AI 연결 없이 설치 결과 확인

```sh
oci-lenz sample --output "$HOME/oci-lenz-work/sample"
oci-lenz draw --snapshot "$HOME/oci-lenz-work/sample/snapshot.json" \
  --output "$HOME/oci-lenz-work/diagnostic" --no-ai
```

이 명령은 가상 데이터로 편집 가능한 `architecture.drawio`, `architecture.png`,
`information-index.png` 등을 만듭니다. `--no-ai`는 설치 진단용 배치이며
일반적인 AI 생성 결과의 품질을 뜻하지 않습니다. Draw.io가 없는 장비에서는
`--no-png`를 추가해 XML 생성만 확인할 수 있습니다.

PNG 실행 파일이 표준 경로에 없으면 해당 장비의 `DRAWIO_BIN`을 지정합니다.
macOS에서는 `/Applications`와 현재 사용자의 `Applications` 폴더를 확인합니다.
화면 없는 Linux는 Draw.io Desktop과 Xvfb 또는 DISPLAY가 필요합니다.
설치 도구나 외부 서비스를 앱이 자동으로 설치하지 않습니다.

## 3. 본인 AI 연결과 진단

Codex 방식:

```sh
codex login
codex login status
oci-lenz doctor --ai-provider codex
oci-lenz draw --snapshot "$HOME/oci-lenz-work/sample/snapshot.json" \
  --output "$HOME/oci-lenz-work/ai-example" --ai-provider codex
```

`--model`을 생략하면 본인의 Codex 설정을 사용합니다. 필요하면 사용 가능한
모델을 `--model`로 지정합니다. 로그인 상태 확인은 모델 권한·잔여 한도나
실제 이미지 입력 가능 여부까지 검증하지 않습니다. 실제 `draw`로 확인합니다.
Codex 설치·인증은 [공식 안내](https://learn.chatgpt.com/docs/codex/cli)를 따릅니다.

OpenAI API 방식은 로컬 비밀 관리 도구로 `OPENAI_API_KEY`를 실행 환경에
제공하고, 해당 계정에서 사용 가능한 이미지·구조화 출력 지원 모델을 선택합니다.
키를 명령어·문서·채팅에 직접 붙여 넣지 않습니다.

```sh
oci-lenz doctor --ai-provider openai --model YOUR_API_MODEL
oci-lenz draw --snapshot "$HOME/oci-lenz-work/sample/snapshot.json" \
  --output "$HOME/oci-lenz-work/api-example" \
  --ai-provider openai --model YOUR_API_MODEL
```

API 방식은 Codex CLI가 필요하지 않습니다. 진단은 키의 존재 여부만 확인하며
키 값과 모델 설정 값, 인증 응답을 출력하지 않습니다. 기본 제공 API 어댑터는
OpenAI Responses API용이며 다른 Agent의 모델 설정을 자동으로 가져오지 않습니다.

`oci-lenz doctor --json`으로 기계 판독용 결과를 확인합니다. 준비 항목이 충족되면
종료 코드 0, 누락·사용 불가가 있으면 2입니다. `--no-png`는 Draw.io 검사를
생략합니다. 진단은 OCI 프로필 내용을 읽거나 OCI·AI 모델을 호출하지 않습니다.
Codex 방식은 출력이 억제된 `codex login status`만 실행합니다.

## 4. 실제 고객사 범위 수집

본인의 로컬 OCI SDK 읽기 전용 프로필을 구성한 후 아래 자리표시자를 바꿉니다.
개인 키·암호·config 내용은 Agent 대화나 저장소에 입력하지 않습니다.

```sh
oci-lenz collect --profile READONLY --region REGION \
  --compartment-id COMPARTMENT_OCID --output "$HOME/oci-lenz-work/customer/inventory"
oci-lenz draw --snapshot "$HOME/oci-lenz-work/customer/inventory/snapshot.json" \
  --output "$HOME/oci-lenz-work/customer/diagrams"
```

여러 컴파트먼트는 `--compartment-id`를 반복합니다. 하위 컴파트먼트를 자동으로
탐색·수집하지 않습니다. 필요한 조회 권한은 [IAM 문서](IAM.md)를 확인합니다.
`coverage.json`의 성공·실패·미지원 상태를 먼저 확인합니다. Base DB·MySQL·
Autonomous DB·ExaCC·ExaCI·Exascale과 DRG·Peering·VPN·FastConnect를 지원합니다.
Kubernetes 내부 워크로드·DB 카탈로그·DRG 라우팅 정책은 후속 범위입니다. 구성도 연결은 설정된
관계이며 도달성 검증이 아닙니다.
운영 결과는 실제 이름·IP를 표시하므로 공개 예시로 올리지 않습니다.

## 5. Codex 또는 Hermes에서 대화로 프로젝트 개선

두 Agent 모두 파일과 터미널에 접근할 수 있는 환경에서 clone한 프로젝트를
작업 대상으로 사용합니다. Agent와 구성도 생성기의 AI 연결은 별개입니다.
프로젝트를 Hermes에서 개선해도 `draw`의 모델은 여전히 Codex 또는 OpenAI입니다.
`scripts/execute.py`의 자동 phase 실행은 현재 Codex CLI가 필요합니다. Hermes가
직접 코드와 테스트를 다루는 것과 자동 하네스의 실행 엔진은 구분합니다.

Codex Work에서는 clone한 폴더를 열고 아래 요청을 전달합니다. Hermes 사용자는
이미 설정한 Hermes 환경에서 해당 폴더로 이동해 실행할 수 있습니다.

```sh
# clone한 OCI-Lenz 저장소 루트에서 실행
hermes
```

Hermes의 [CLI](https://hermes-agent.nousresearch.com/docs/user-guide/cli)와
[AGENTS.md 지원](https://hermes-agent.nousresearch.com/docs/user-guide/features/context-files)은
공식 문서를 참고합니다. 이 저장소에서는 Hermes 실행을 실증하지 않았으며
`.agents/skills` 자동 인식을 가정하지 않습니다. 필요한 두 `SKILL.md`를 직접
읽도록 요청할 수 있습니다. Agent의 실행 환경이 컨테이너·원격 장비라면 그
환경에서 프로젝트와 입력·Draw.io 실행 파일에 접근할 수 있어야 합니다.

첫 요청 예:

> AGENTS.md, docs/ONBOARDING.md와 프로젝트 문서를 읽어 구조를 파악해줘.
> .agents/skills/drawio/SKILL.md와 .agents/skills/oci-drawio/SKILL.md도 읽어줘.
> 먼저 가상 데이터로 설치와 PNG 생성을 확인해줘. 실제 OCI 조회는 지정한
> 프로필·리전·컴파트먼트가 준비된 뒤 실행해. 고객사 파일은 저장소 밖에 두고,
> 서비스 소속은 추론하지 마. 커밋·푸시는 요청할 때만 수행해.

개선 요청에서는 대상 범위를 명시합니다.

- 프로그램 개선: 테스트로 문제를 재현하고 공통 코드 수정, 가상·로컬 결과 비교
- 이번 구성도 편집: 소스 코드와 수집 관계를 유지하고 해당 결과만 편집

자연어로 기존 배치를 수정·승인·되돌리는 전용 앱 기능은 아직 없습니다.
Agent가 고객사 원본을 직접 읽는 동작은 생성기의 별칭 입력 경로와 별개이므로
해당 Agent에 전달할 파일 범위도 사용자가 정해야 합니다.

## 지원 검증 범위

macOS의 별도 wheel 설치와 저장소 밖 가상 실행을 검증합니다. Linux CI에서는
설치 패키지의 XML 경로를 검사하며, Linux PNG·Windows·Hermes 실사용과
OpenAI API 실제 계정 호출은 별도 검증 대상으로 유지합니다. 인증이 없거나
권한·한도가 부족한 환경의 성공을 보장하지 않습니다.
