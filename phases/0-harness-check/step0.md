# Step 0: harness-check

## 읽어야 할 파일
- AGENTS.md
- docs/HARNESS.md
- docs/ARCHITECTURE.md
- tests/test_execute.py
- scripts/execute.py

## 작업
현재 하네스의 테스트를 실행해 기본 구조가 정상인지 확인한다. 이 단계는 변경 없는
실행 점검용이다. 기능 구현이나 저장소 파일 변경을 하지 않는다.
CLI 인터페이스는 `python3 scripts/execute.py <phase> [--check] [--timeout SECONDS]`이다.

## Acceptance Criteria
```sh
python3 -m unittest discover -s tests -v
```

## 금지사항
- OCI 프로필이나 비밀정보를 읽지 않는다. 이 단계는 네트워크 없는 하네스 검사다.
- phase index나 테스트를 수정하지 않는다. 완료 여부는 실행기가 판단한다.
- 하위 에이전트 또는 다른 하네스 실행기를 시작하지 않는다. 중첩 실행을 방지한다.
