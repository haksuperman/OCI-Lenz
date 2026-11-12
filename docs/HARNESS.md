# Codex Harness

## Workflow
1. `AGENTS.md`와 docs의 PRD, ARCHITECTURE, ADR을 읽는다.
2. 작업을 한 모듈씩 나누고 사용자 요구사항과 완료 조건을 구체화한다.
3. `phases/index.json`, `phases/<phase>/index.json`, `stepN.md`를 작성한다.
4. `--check`로 구조를 검증한 뒤 실행한다.
5. 테스트 및 산출물 근거로 완료 여부를 판단하고 결과를 보고한다.

각 step 문서는 독립 세션에서 이해할 수 있어야 한다. 읽을 파일, 작업 인터페이스,
범위, AC, 금지사항을 명시한다. 다음 step은 앞선 산출물을 직접 읽는다.

## Index format
```json
{
  "project": "OCI-Lenz",
  "phase": "example-phase",
  "steps": [
    {
      "step": 0,
      "name": "example-step",
      "status": "pending",
      "ac": [["python3", "-m", "unittest", "discover", "-s", "tests", "-v"]]
    }
  ]
}
```

AC는 shell 문자열이 아닌 argv 배열이다. 각 명령은 프로젝트 루트에서 실행된다.
AC는 신뢰된 저장소 코드로서 **부모 프로세스의 권한**으로 실행되므로 실행 전에 검토한다.
`--check`는 구조만 확인하며 명령의 안전성이나 기능을 보증하지 않는다.
Step 번호는 0부터 연속이어야 하고 AC는 비어 있을 수 없다.
상위 인덱스는 `{"phases":[{"dir":"example-phase","status":"pending"}]}` 형식이다.

## Execution
```sh
python3 scripts/execute.py 0-harness-check --check
python3 scripts/execute.py 0-harness-check --timeout 1800
```

`codex exec --sandbox workspace-write --ephemeral`에 stdin으로 프롬프트를 전달한다.
설치된 Codex의 로그인과 승인 정책을 따른다. 외부 인증·네트워크·추가 승인이 필요한
작업을 자동 승인하지 않는다. Git 저장소가 필요하며 하네스가 git init, 브랜치 변경,
커밋, push를 대신 수행하지 않는다. `--push` 옵션은 제공하지 않는다.

각 호출은 새 세션이며 AGENTS.md, docs/*.md, 이전 완료 단계와 현재 step 문서를 전달한다.
에이전트가 completed를 반환하고 모든 AC가 0으로 끝난 경우에만 completed로 기록한다.
실패·타임아웃·잘못된 결과는 최대 3회 시도한다. AC 종료 코드와 일반 오류만 다음 시도에 전달한다.
blocked는 재시도하지 않는다. 종료 코드는 성공 0, 실패 1, blocked 2다.
완료 단계는 재실행 시 건너뛰므로 AC를 다시 검증하려면 직접 실행한다.

`stepN-output.json`에는 시도별 상태·AC 종료 코드만 저장한다.
원문 stdout/stderr는 터미널이나 저장소에 남기지 않는다. 일시적 최종 응답 파일에는
status enum만 허용하고 호출 종료 시 삭제한다. Codex 자체나 실행한 도구의 모든 저장
동작까지 이 하네스가 통제하지는 않으므로 비밀정보를 프롬프트에 넣지 않는다.

## Recovery
실패 원인을 로컬에서 확인·수정한 후 해당 step status를 pending으로 바꾸고
error_message/blocked_reason 및 이전 완료 타임스탬프를 제거해 재실행한다.
프로세스 강제 종료 후 `.executor.lock`이 남으면 실행 중인 프로세스가 없는지 확인한 뒤 제거한다.
같은 작업 폴더에서 여러 phase를 동시에 실행하지 않는다.

실제 OCI 접근이 없는 동안에는 synthetic phase만 실행하고 live validation은 별도로 둔다.

## References
- https://learn.chatgpt.com/docs/non-interactive-mode
- 실행 환경의 `codex exec --help`에서 sandbox, ephemeral, output-schema, stdin 지원 확인.
