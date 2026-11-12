# 개발 참여

프로젝트 규칙은 [AGENTS.md](AGENTS.md), 요구사항은 [PRD](docs/PRD.md)를 기준으로 합니다.
사용자용 설치·실행 안내는 README에, 개발 도구와 작업 절차는 이 문서와 docs에 기록합니다.
개발 진행 상황은 phases의 상태와 작업 기록으로 관리합니다.

## 개발 환경과 검증

현재 개발 하네스는 Python 3.10+ 표준 라이브러리를 사용합니다.

```sh
git clone <GITHUB_REPOSITORY_URL> OCI-Lenz
cd OCI-Lenz
python3 -m venv .venv
. .venv/bin/activate
python3 -m unittest discover -s tests -v
python3 scripts/execute.py 0-harness-check --check
```

테스트와 phase 구조 검사는 Codex 인증이나 OCI 접근 없이 실행할 수 있습니다.
새 기능은 의미 있는 테스트를 먼저 작성하고 구현합니다.

## 개발 하네스

개발 작업 자동 실행에는 인증된 Codex CLI가 필요합니다.

```sh
python3 scripts/execute.py 0-harness-check --timeout 1800
```

이 명령은 실제 Codex를 호출합니다. 자동 커밋·푸시는 수행하지 않습니다.
단계 정의, AC 검증, 재시도와 복구는 [HARNESS.md](docs/HARNESS.md)를 참고하세요.
개발에 사용하는 기반 하네스 출처와 변경 사항은 [UPSTREAM.md](docs/UPSTREAM.md)에 기록합니다.

## 문서 갱신 원칙

- README는 제품 목적, 기능, 설치·사용 방법, 고객사별 설정, 산출물을 설명합니다.
- 개발 상태표와 작업 순서는 README에 누적하지 않고 phases와 개발 기록에서 관리합니다.
- README의 출시 전 안내는 설치·실행 절차가 검증되면 삭제하고 실제 명령으로 교체합니다.
- 구현 전 기능과 예시를 이미 제공되는 기능으로 표현하지 않습니다.
- OCI 인증과 고객사 실데이터를 테스트·문서·커밋에 포함하지 않습니다.
