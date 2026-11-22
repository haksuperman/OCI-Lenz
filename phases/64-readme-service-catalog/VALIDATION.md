# 검증 근거

- 수집기·서비스 모델·USAGE/IAM과 기존 README의 지원 범위를 대조해
  7개 콘솔 대분류, 19개 서비스 행으로 정리했다. 기본 페이지에서 숨기는
  기술 도형, Attachment 생략, 범위 밖 대상과 NLB 등록 IP 태그의 차이를 유지한다.
- Oracle 공식 Console 안내에서 Oracle AI Database/Databases 분리,
  GoldenGate의 Oracle AI Database 소속, WAF의 Identity & Security 소속,
  API Gateway/Functions/Container Registry/DevOps의 Developer Services 소속을
  확인했다. README에는 해당 분류의 공식 출처 링크를 제공한다.
- Object Storage/Container Registry/DevOps의 문서 끝 별도 안내를 표에 통합하고,
  생성 파일 안내도 독립 표로 분리했다. 미구현 OKE/Database 카탈로그/
  Data Guard/DRG 라우팅 정책 등의 한계는 그대로 유지한다.
- 서비스 표의 열 수/행 수/대분류와 모든 README 로컬 링크를 검사했다.
  하네스 구조 검사와 git diff --check 통과. 문서 변경으로 런타임 코드는
  변경하지 않으며 전체 Python 테스트는 다시 실행하지 않았다.
- 공개 대상은 문서와 phase 기록뿐이다. 고객사 파일·개인정보·인증정보,
  이미지/다이어그램 바이너리는 추가하지 않는다. phase 상태는 실행기가 관리한다.
