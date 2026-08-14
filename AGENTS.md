# AGENTS.md

코딩 에이전트를 위한 프로젝트 작업 지침서입니다.

## 프로젝트 개요

이 프로젝트는 학교 급식 관리 시스템의 통합 플랫폼입니다:
- **오픈API 명세서**: `data/` 디렉토리의 엑셀 파일로 제공되는 학교 기본정보, 급식 식단 정보 API
- **백엔드**: Python 기반 API 서버 (MCP 서버, 멀티에이전트 앱)
- **배포**: GitHub Actions를 활용한 CI/CD 파이프라인
- **목표**: 완성된 서비스 배포까지 진행

## 일반 작업 지침

### 변경 범위와 우선순위

- **기존 규칙 우선**: 이미 작성된 코드, 문서, 구조를 존중합니다.
- **최소 변경**: 요청된 작업에만 필요한 변경만 합니다.
- **불필요한 추상화 금지**: 단순한 작업을 과도하게 복잡하게 하지 않습니다.
- **명확한 커밋**: 각 변경사항은 명확한 목적과 함께 커밋합니다.

### 문서와 파일 이해

- `data/` 디렉토리의 엑셀 파일들을 참고하여 API 명세를 이해합니다.
- README.md, PRD.md, TRD.md 등 기존 문서를 우선 확인합니다.
- 새로운 문서나 가이드는 프로젝트 구조와 일관되게 작성합니다.

---

## Python 코딩 가이드라인

### 타입 안정성

- **Type Hints 필수**: 모든 함수와 메서드에 타입 힌트를 작성합니다.
  ```python
  def fetch_school_data(school_id: str) -> dict[str, Any]:
      pass
  ```
- **pydantic 사용**: API 요청/응답 데이터는 Pydantic 모델로 정의합니다.
  ```python
  from pydantic import BaseModel
  
  class SchoolInfo(BaseModel):
      school_id: str
      school_name: str
      address: str
  ```

### 오류 처리

- **구체적인 예외 처리**: 광범위한 `except Exception`보다 구체적인 예외를 처리합니다.
  ```python
  try:
      response = requests.get(url)
      response.raise_for_status()
  except requests.HTTPError as e:
      logger.error(f"HTTP Error: {e}")
  except requests.RequestException as e:
      logger.error(f"Request Error: {e}")
  ```
- **로깅**: 에러는 반드시 로깅하고, 사용자에게 적절한 메시지를 전달합니다.

### 의존성 관리

- **requirements.txt 또는 pyproject.toml 사용**: 모든 외부 라이브러리를 명시적으로 관리합니다.
- **버전 고정**: 프로덕션 환경에서는 정확한 버전을 지정합니다.
  ```
  requests==2.31.0
  pydantic==2.5.0
  ```
- **가상환경 사용**: 프로젝트는 독립적인 가상환경에서 실행됩니다.

### 코드 품질

- **DRY (Don't Repeat Yourself)**: 반복되는 코드는 함수로 추상화합니다.
- **SOLID 원칙**: 단일 책임, 개방-폐쇄 원칙을 따릅니다.
- **문서화**: 복잡한 로직은 docstring으로 설명합니다.
  ```python
  def parse_menu_data(excel_path: str) -> list[MenuItem]:
      """
      엑셀 파일에서 급식 식단 정보를 파싱합니다.
      
      Args:
          excel_path: 엑셀 파일 경로
          
      Returns:
          MenuItem 객체의 리스트
          
      Raises:
          FileNotFoundError: 파일이 없을 때
          ValueError: 파일 형식이 잘못되었을 때
      """
  ```

---

## TypeScript 코딩 가이드라인

### 타입 안정성

- **strict mode 활성화**: tsconfig.json에서 `strict: true` 설정합니다.
- **인터페이스 정의**: API 데이터 구조는 인터페이스로 정의합니다.
  ```typescript
  interface SchoolInfo {
    schoolId: string;
    schoolName: string;
    address: string;
  }
  ```
- **제네릭 활용**: 재사용 가능한 컴포넌트는 제네릭으로 작성합니다.

### 오류 처리

- **명시적 에러 처리**: try-catch와 함께 타입 안전한 에러 처리합니다.
  ```typescript
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } catch (error) {
    logger.error('Failed to fetch:', error);
    throw error;
  }
  ```

### 의존성 관리

- **package.json 관리**: 모든 의존성을 package.json에 명시합니다.
- **버전 범위 지정**: 호환성을 고려하되 보안 업데이트는 자동 포함합니다.
  ```json
  {
    "dependencies": {
      "axios": "^1.6.0",
      "pydantic-ts": "^2.0.0"
    }
  }
  ```

---

## 검증 원칙

### 테스트

- **테스트 프레임워크**: Python은 `pytest`, TypeScript는 `jest` 사용
- **테스트 작성**: 모든 API 엔드포인트와 핵심 로직에 단위 테스트 작성
  ```bash
  # Python 테스트 실행
  pytest tests/ -v --cov=src
  
  # TypeScript 테스트 실행
  npm test
  ```
- **최소 커버리지**: 80% 이상의 코드 커버리지 목표

### 포맷팅

- **Python**: `black` 사용
  ```bash
  black src/ --line-length=100
  ```
- **TypeScript/JavaScript**: `prettier` 사용
  ```bash
  prettier --write src/
  ```

### 린트

- **Python**: `pylint` 또는 `ruff` 사용
  ```bash
  pylint src/
  # 또는
  ruff check src/
  ```
- **TypeScript**: `eslint` 사용
  ```bash
  eslint src/ --fix
  ```

### 타입 검사

- **Python**: `mypy` 사용
  ```bash
  mypy src/
  ```
- **TypeScript**: `tsc` 사용
  ```bash
  tsc --noEmit
  ```

### 빌드 및 검증 스크립트

모든 검증은 다음 순서로 진행합니다:
```bash
# Python 프로젝트
python -m pytest tests/
python -m mypy src/
python -m pylint src/
python -m black --check src/

# TypeScript 프로젝트
npm test
npm run lint
npm run type-check
npm run build
```

---

## 보안 지침

### 민감한 정보 보호

- **환경변수 사용**: API 키, 토큰, 데이터베이스 연결 정보는 환경변수로 관리합니다.
  ```python
  import os
  API_KEY = os.getenv("API_KEY")
  if not API_KEY:
      raise ValueError("API_KEY environment variable not set")
  ```
- **.gitignore 확인**: `.env`, `secrets.json` 등이 git에 커밋되지 않도록 확인합니다.
- **secrets in code 금지**: 하드코딩된 키나 토큰은 절대 금지입니다.

### 의존성 보안

- **정기적 업데이트**: 보안 취약점이 있는 의존성을 정기적으로 업데이트합니다.
- **보안 감사**: 중요한 라이브러리는 `safety` (Python) 또는 `npm audit`로 검사합니다.
  ```bash
  # Python
  safety check
  
  # Node.js
  npm audit
  ```

### API 보안

- **인증**: API 엔드포인트에 적절한 인증 메커니즘(JWT, OAuth) 적용
- **권한 검증**: 각 엔드포인트에서 사용자 권한을 검증합니다.
- **SQL Injection 방지**: ORM 사용 또는 Prepared Statements 사용

---

## 문서화 지침

### 코드 주석

- **주석은 "왜"를 설명**: "무엇"이 아니라 "왜 이렇게 했는지" 설명합니다.
  ```python
  # 나쁜 예
  x = y + 1  # x에 1을 더한다
  
  # 좋은 예
  # API 응답에서 페이지 번호는 1부터 시작하지만, 내부적으로는 0부터 시작해야 함
  zero_based_page = page_number - 1
  ```

### README와 API 문서

- **README.md**: 프로젝트 개요, 설정 방법, 실행 방법 포함
- **API 문서**: OpenAPI/Swagger 스펙 문서 유지
- **CHANGELOG.md**: 주요 변경사항 기록

### 모듈 및 함수 문서

- **docstring 작성**: 모든 공개 함수/클래스에 docstring 작성
  ```python
  def process_meal_data(file_path: str) -> list[MealInfo]:
      """
      급식 데이터를 처리하고 구조화된 정보로 변환합니다.
      
      Args:
          file_path: 엑셀 파일의 경로
          
      Returns:
          MealInfo 객체의 리스트
          
      Raises:
          FileNotFoundError: 파일을 찾을 수 없을 때
          ValueError: 파일 형식이 올바르지 않을 때
      """
  ```

---

## 주의사항 및 가드레일

### 코드 리뷰

- **모든 변경은 PR로**: 직접 main 브랜치에 커밋하지 않습니다.
- **피드백 반영**: 리뷰어의 의견을 적극 수렴합니다.

### 성능

- **과도한 최적화 금지**: 읽기 쉬운 코드 > 과도하게 최적화된 코드
- **병목 지점 분석**: 필요한 경우에만 성능 최적화합니다.

### 호환성

- **버전 호환성**: Python 3.9+, Node.js 18+ 지원
- **크로스 플랫폼**: Windows, macOS, Linux에서 동작하도록 개발

### 의존성 변경

- **최소 필요한 것만**: 필수적인 라이브러리만 추가합니다.
- **버전 충돌 확인**: 새로운 의존성이 기존 라이브러리와 충돌하지 않는지 확인합니다.

---

## Git 커밋 규칙

### 커밋 메시지 형식

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 타입 (Type)

- `feat`: 새로운 기능
- `fix`: 버그 수정
- `docs`: 문서 수정
- `style`: 코드 스타일 변경 (포맷팅, 세미콜론 등)
- `refactor`: 코드 리팩토링
- `perf`: 성능 개선
- `test`: 테스트 추가 또는 수정
- `chore`: 빌드, 의존성 업데이트 등

### 예제

```
feat(api): Add school information endpoint

- Implement GET /api/schools endpoint
- Add validation for school ID
- Include error handling for not found cases

Closes #5
```

```
fix(parser): Handle missing meal data gracefully

The parser would crash when encountering empty cells in the excel file.
Now it logs a warning and continues processing.

Fixes #12
```

### 커밋 작성 시 주의사항

- **원자적 커밋**: 하나의 커밋은 하나의 논리적 변화만 포함
- **명확한 메시지**: 3-6개월 뒤에 읽어도 의도를 알 수 있도록
- **Signed-off**: `git commit -s` 옵션으로 sign-off 추가

---

## Pull Request (PR) 작성 규칙

### PR 제목

```
[<type>] <description>
```

예제:
- `[feat] Add OpenAPI JSON generation from Excel`
- `[fix] Fix meal data parsing error`
- `[docs] Update README with setup instructions`

### PR 본문 (Description)

```markdown
## 개요
이 PR의 목적을 간단히 설명합니다.

## 변경사항
- 변경사항 1
- 변경사항 2
- 변경사항 3

## 테스트 방법
다음 명령어로 변경사항을 테스트할 수 있습니다:
```bash
pytest tests/test_new_feature.py
```

## 관련 이슈
Closes #5, #6

## 스크린샷 또는 로그
(필요한 경우)
```

### PR 리뷰 전 체크리스트

- [ ] 코드가 스타일 가이드를 따릅니다.
- [ ] 테스트를 작성했거나, 기존 테스트가 통과합니다.
- [ ] 문서를 업데이트했습니다. (해당하는 경우)
- [ ] 커밋 메시지가 명확합니다.
- [ ] 민감한 정보(키, 토큰)가 포함되지 않았습니다.

### PR 병합 전 요구사항

- 최소 1명 이상의 리뷰 승인
- 모든 CI/CD 체크 통과
- 머인 브랜치와 충돌 없음

---

## GitHub Actions CI/CD

### 자동 실행되는 체크

다음 작업들이 모든 PR과 커밋에서 자동으로 실행됩니다:

1. **테스트**: pytest 또는 jest로 테스트 스위트 실행
2. **린트**: pylint/ruff 또는 eslint로 코드 스타일 확인
3. **타입 검사**: mypy 또는 tsc로 타입 안전성 확인
4. **빌드**: 컨테이너 이미지 또는 배포 아티팩트 빌드

### 배포 파이프라인

- `main` 브랜치에 병합되면 자동으로 스테이징 환경에 배포
- 태그 생성 시 프로덕션 환경에 배포

---

## 마지막 체크사항

작업을 완료하기 전에 다음을 확인하세요:

- [ ] 이슈의 인수 조건을 모두 만족했는가?
- [ ] 테스트가 통과하는가?
- [ ] 코드가 이 문서의 지침을 따르는가?
- [ ] 문서가 최신 상태인가?
- [ ] 비밀 정보가 노출되지 않았는가?

