# AGENTS.md

코딩 에이전트를 위한 프로젝트 작업 지침서입니다.

## 프로젝트 개요

"급식배틀"은 NEIS(교육정보 공시) 공개 API를 활용해 학교 급식 메뉴를 조회하고,
두 학교의 급식을 비교하는 "오늘의 왕" 기능을 제공하는 학교 급식 조회 웹 앱입니다.

- **오픈API 명세서**: `data/`의 엑셀 파일(학교 기본정보, 급식 식단 정보)과 이를 변환한
  `data/openapi.json` — NEIS API의 실제 계약(엔드포인트, 파라미터, 코드값)
- **백엔드**(`backend/`): FastAPI 기반 API 서버. NEIS API를 호출해 학교 검색/급식 조회를
  제공하고, "오늘의 왕" 결과는 SQLite(`backend/data/app.db`)에 저장해 하루 한 번만 재계산
- **프론트엔드**(`frontend/`): React + TypeScript + Vite. 백엔드 API만 호출하며 NEIS를
  직접 호출하지 않음
- **MCP 서버**(`src/mcp/`): 학교 검색/급식 조회 도구를 제공하는 독립 실행형 Model Context
  Protocol 서버 (Streamable HTTP, backend 비의존)
- **배포**: GitHub Actions CI(`.github/workflows/ci.yml`), Docker Compose로 3개 서비스
  (backend:8000, mcp:8100, frontend:3000) 동시 실행

### 저장소 구조

```
data/                    # NEIS API 명세 원본 (엑셀 2종 + 생성된 openapi.json)
src/
  openapi.json            # 생성 파일: 백엔드 자체 API(프론트-백엔드 계약) 스냅샷
  mcp/                    # MCP 서버 (Python, FastMCP, Streamable HTTP)
    app/                  # config, errors, neis_client, formatting, validators, server
    tests/                # 단위(test_neis_client.py) + 통합(test_server.py) 테스트
backend/                 # FastAPI 백엔드
  app/
    main.py, config.py, database.py, models.py, schemas.py
    neis_client.py, scheduler.py
    routers/              # schools.py, meals.py, tournament.py
    services/             # scoring.py, tournament_service.py
  tests/                  # 라우터/서비스별 단위·통합 테스트
  data/                   # app.db (SQLite, 실행 시 생성 — 커밋/삭제 금지)
frontend/                 # React + TypeScript + Vite
  src/
    App.tsx, App.test.tsx # 루트 컴포넌트 + MSW 기반 통합 테스트
    api/client.ts          # 백엔드 API 호출 전용 (NEIS 직접 호출 금지)
    components/            # SchoolSearch, DateRangePicker, MealResults, TodayKing 등
    test/setup.ts           # vitest + MSW 셋업
scripts/                  # run-dev.ps1/.sh, convert_excel*.py/.ps1, generate_openapi.ps1
docker-compose.yml        # backend + mcp + frontend
```

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
- **`data/openapi.json` vs `src/openapi.json`을 혼동하지 않습니다**:
  - `data/openapi.json`은 **NEIS 외부 API** 계약(엔드포인트, 파라미터, 코드값)입니다.
    `data/*.xlsx`에서 `scripts/convert_excel_to_openapi.ps1`(또는 `convert_excel.py`)로
    생성되므로, NEIS 스펙이 바뀌면 엑셀→스크립트 재실행 순으로 갱신하고 직접 손으로
    수정하지 않습니다.
  - `src/openapi.json`은 **이 프로젝트 자체 백엔드 API**(프론트-백엔드 계약) 스냅샷입니다.
    백엔드 라우터가 실제 계약의 출처이므로, 라우터를 바꾼 뒤 이 파일도 맞춰 갱신하되
    직접 손으로 편집하기보다는 실제 스키마와 일치하도록 갱신 여부를 확인합니다.

---

## 실제 사용 기술 스택

### 프론트엔드 (`frontend/`)

- **프레임워크**: React 19 + TypeScript(strict) 5, **Vite 8** (빌드/개발 서버)
- **패키지 매니저**: npm (`package-lock.json` 커밋)
- **테스트**: Vitest 4 + Testing Library + **MSW**(백엔드 API 목킹, 실네트워크 호출 없음)
- **린트**: **oxlint** (Rust 기반 고속 린터, eslint 아님)
- **타입 검사**: `tsc` (빌드 스크립트 `tsc -b`에 포함, 별도 포맷터는 미도입)
- **런타임**: Node.js 18+ (CI는 Node 24)

### 백엔드 (`backend/`)

- **프레임워크**: FastAPI + uvicorn, SQLAlchemy(SQLite) + APScheduler(오늘의 왕 일 1회 계산)
- **패키지 매니저**: pip + `requirements.txt` (⚠️ `pyproject.toml`이 아닙니다 — 아래 참고)
- **HTTP 클라이언트**: httpx (NEIS 호출), 테스트는 respx로 목킹
- **테스트**: pytest + pytest-asyncio
- **런타임**: Python 3.12 (CI 기준)

### MCP 서버 (`src/mcp/`)

- **프레임워크**: `mcp`(FastMCP) **1.9.4** 고정 — 최신 2.x는 `cryptography`(Rust 빌드) 의존성이
  추가되어 환경에 따라 빌드가 실패할 수 있어 의도적으로 1.9.4를 사용합니다. 업그레이드 시
  반드시 로컬에서 `pip install`과 테스트가 통과하는지 먼저 확인하세요.
- **전송 방식**: Streamable HTTP (`streamable_http_path="/mcp"`), backend와 완전히 독립 실행
- **기타**: httpx, pydantic-settings, 테스트는 pytest + respx

### ⚠️ CONTRIBUTING.md / CI와의 알려진 불일치

`CONTRIBUTING.md`와 `.github/workflows/ci.yml`은 `backend/pyproject.toml`이 존재하고
`pip install -e ".[dev]"`로 설치한다고 가정하지만, 실제 `backend/`와 `src/mcp/`는
`requirements.txt`만 사용합니다. 그 결과 CI의 backend 잡은 `pyproject.toml` 부재 조건으로
**현재 실질적으로 스킵**되고 있고, `src/mcp/`는 CI에 아예 잡이 없습니다. 이 문서의 명령은
실제로 동작하는 `requirements.txt` 기준으로 작성했으니 이 명령을 따르세요. CI/CONTRIBUTING.md
정합화는 별도 이슈로 다루는 것을 권장합니다.

## 검증된 명령

### 프론트엔드

```bash
cd frontend
npm install
npm run dev          # 로컬 개발 서버 (:3000)
npm run build         # tsc -b && vite build (타입 검사 포함)
npm test              # vitest run
npm run lint           # oxlint
```

### 백엔드

```bash
cd backend
python -m venv .venv   # 활성화 후 진행
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000   # 로컬 개발 서버
pytest                                                   # 단위 + 통합 테스트
```

### MCP 서버

```bash
cd src/mcp
pip install -r requirements.txt
python -m app.server    # 로컬 개발 서버 (:8100, Streamable HTTP)
pytest
```

### 한 번에 로컬 실행 (backend + frontend)

```powershell
./scripts/run-dev.ps1   # Windows, 각각 새 PowerShell 창에서 기동
```
```bash
./scripts/run-dev.sh    # bash
```

사전에 루트 `.env.example`을 `.env`로 복사하고 `NEIS_API_KEY`를 채워야 합니다.

### Docker Compose

```bash
docker compose up --build     # backend(8000) + mcp(8100) + frontend(3000) 동시 기동
docker compose config          # 문법 검증만 (CI의 compose 잡이 사용, 실제 빌드 아님)
```

## 테스트 위치와 원칙

- **프론트엔드 통합 테스트**: `frontend/src/**/*.test.tsx` (예: `App.test.tsx`). MSW로 백엔드
  API를 목킹해 실제 네트워크 없이 사용자 흐름(학교 검색 → 선택 → 기간 지정 → 급식 조회)을
  검증합니다. `npm test`로 실행합니다.
- **백엔드 단위·통합 테스트**: `backend/tests/*.py`. FastAPI `TestClient` + respx(NEIS 호출
  목킹)로 라우터별 동작(`test_schools_router.py`, `test_meals_router.py`), 점수 계산
  (`test_scoring.py`), 오늘의 왕 캐싱·스케줄러(`test_tournament_router.py`,
  `test_tournament_service.py`)를 검증합니다. `pytest`로 실행합니다.
- **MCP 서버 테스트**: `src/mcp/tests/*.py`. `test_neis_client.py`(단위, respx),
  `test_server.py`(통합, `FastMCP.call_tool()` 직접 호출로 도구 검증). `pytest`로 실행합니다.
- **E2E 관련 유의사항**: 이 프로젝트의 "E2E 검증"은 실제로는 프론트엔드 통합 테스트(MSW
  목킹) + 개발 중 브라우저를 통한 수동 크로스서비스 확인 수준입니다. backend·frontend·mcp를
  모두 실제로 띄워 자동으로 검증하는 크로스서비스 E2E 스위트는 아직 없습니다.
- **원칙**: 새 기능/버그 수정 시 반드시 대응하는 테스트를 함께 추가합니다. 외부 API(NEIS)
  호출은 실제 네트워크 대신 respx(Python)/MSW(TypeScript)로 목킹해 결정론적으로 테스트합니다.

## 프로젝트 고유 가드레일

- **NEIS API 직접 호출 금지**: 프론트엔드는 NEIS Open API를 절대 직접 호출하지 않습니다.
  반드시 백엔드(`/api/...`) 또는 MCP 서버를 통해서만 데이터를 가져오며, 호출 주소는
  `frontend/src/api/client.ts`의 `API_BASE_URL` 하나로 관리합니다.
- **`data/openapi.json` 계약 준수**: NEIS를 호출하는 모든 코드(`neis_client.py`, backend·mcp
  양쪽)는 `data/openapi.json`에 정의된 엔드포인트·파라미터·코드값(예: `MMEAL_SC_CODE`
  `2`=중식)을 따릅니다.
- **생성 파일 직접 수정 금지**: `data/openapi.json`, `src/openapi.json`은 각각 스크립트/구현
  스냅샷으로 생성되는 파일입니다. 스펙이 바뀌면 원본(엑셀, 백엔드 라우터)을 수정한 뒤
  재생성하고, 생성된 JSON 자체를 손으로 편집하지 않습니다.
- **비밀 정보 관리**: `NEIS_API_KEY` 등은 각 컴포넌트의 `.env`(루트/`backend/`/`src/mcp/`
  `.env.example` 참고)로만 관리하며 커밋하지 않습니다(`.gitignore`에 포함). GitHub Actions에서
  필요하면 리포지토리 Secrets를 사용합니다.
- **DB/캐시 파일 보존**: "오늘의 왕" 결과는 `backend/data/app.db`(SQLite)에 저장되어 하루
  한 번(스케줄러, 기본 00:10, `TOURNAMENT_RUN_HOUR`/`TOURNAMENT_RUN_MINUTE`)만 재계산됩니다.
  로컬 검증 중 이 파일을 임의로 삭제하지 않습니다.
- **서버 프로세스 관리**: 로컬에서 백엔드/프론트엔드/MCP 서버를 장시간 띄워둘 때는 세션·터미널
  종료로 죽지 않도록 완전히 분리된 프로세스로 실행하고, `python`/`npm` 실행 전 PATH가 제대로
  설정되어 있는지 확인합니다.

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
      "react": "^19.2.8"
    },
    "devDependencies": {
      "msw": "^2.15.0"
    }
  }
  ```

---

## 검증 원칙

> 실제로 동작하는 명령은 위 [검증된 명령](#검증된-명령), 테스트 위치는
> [테스트 위치와 원칙](#테스트-위치와-원칙)을 참고하세요. 이 섹션은 일반 원칙만 다룹니다.

- **작업 전 확인**: 코드를 바꾸기 전에 해당 컴포넌트(frontend/backend/src/mcp)의 테스트를
  먼저 실행해 현재 상태를 파악합니다.
- **테스트 작성**: 새 기능이나 버그 수정에는 반드시 대응하는 테스트를 함께 추가합니다.
- **포맷팅/린트/타입 검사 도구가 없는 영역**: 현재 `backend/`, `src/mcp/`에는 black·ruff·mypy
  같은 전용 포맷터/린터/타입 체커가 도입되어 있지 않습니다. 이 영역은 타입 힌트 작성 규칙
  (아래 Python 코딩 가이드라인)과 Pydantic 런타임 검증, 코드 리뷰로 대신합니다. 새로 도구를
  추가하려면 먼저 사용자와 상의하세요(불필요한 의존성 추가 금지 원칙).
- **작업 후 확인**: 변경한 컴포넌트의 검증된 명령(테스트, 빌드/lint)을 실행해 회귀가 없는지
  확인한 뒤 커밋합니다.

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

## 일반 가드레일

> 프로젝트 고유 가드레일(NEIS 직접 호출 금지 등)은 위 [프로젝트 고유
> 가드레일](#프로젝트-고유-가드레일) 섹션을 참고하세요.

### 코드 리뷰

- **모든 변경은 PR로**: 직접 main 브랜치에 커밋하지 않습니다.
- **피드백 반영**: 리뷰어의 의견을 적극 수렴합니다.

### 성능

- **과도한 최적화 금지**: 읽기 쉬운 코드 > 과도하게 최적화된 코드
- **병목 지점 분석**: 필요한 경우에만 성능 최적화합니다.

### 호환성

- **버전 호환성**: Python 3.12(CI 기준), Node.js 18+ 지원(CI는 Node 24)
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

### 실제 워크플로 (`.github/workflows/ci.yml`)

`main`으로의 push와 PR마다 3개 잡이 실행됩니다:

1. **frontend** (`frontend/package-lock.json`이 있을 때만): `npm ci` → `npm run build`
   (tsc 타입 검사 포함) → `npm test`
2. **backend** (`backend/pyproject.toml`이 있을 때만): `pip install -e ".[dev]"` → `pytest`
   — ⚠️ 현재 `backend/`는 `pyproject.toml`이 아니라 `requirements.txt`를 사용하므로 이
   조건이 거짓이 되어 **이 잡은 사실상 스킵됩니다**. `src/mcp/`용 CI 잡은 아직 없습니다.
   CI에서 backend·mcp 테스트를 실제로 돌리려면 워크플로 정합화가 필요합니다(별도 이슈 권장).
3. **compose** (compose 파일이 있을 때만): `docker compose config`로 **문법만** 검증하며
   실제 이미지 빌드는 하지 않습니다.

현재 워크플로에는 별도의 lint 전용 잡이나 배포(스테이징/프로덕션) 단계가 없습니다. Azure
배포는 `docs/06-deplopy-to-azure.md` 단계에서 별도로 진행합니다.

---

## 마지막 체크사항

작업을 완료하기 전에 다음을 확인하세요:

- [ ] 이슈의 인수 조건을 모두 만족했는가?
- [ ] 테스트가 통과하는가?
- [ ] 코드가 이 문서의 지침을 따르는가?
- [ ] 문서가 최신 상태인가?
- [ ] 비밀 정보가 노출되지 않았는가?

