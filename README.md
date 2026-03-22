# Claude Code Templates

Claude Code에서 사용할 프로젝트 템플릿을 웹으로 관리하고, 클립보드 복사 또는 CLAUDE.md 파일로 내보내는 도구입니다.

## 주요 기능

- **템플릿 CRUD** - 프로젝트 템플릿 등록/조회/수정/삭제
- **검색** - 이름, 프로젝트명, 기술스택, 목표 기준 키워드 검색
- **엑셀 가져오기** - `.xlsx` 파일에서 템플릿 일괄 가져오기
- **프롬프트 복사** - 템플릿을 마크다운 프롬프트로 변환하여 클립보드 복사
- **CLAUDE.md 내보내기** - 템플릿을 CLAUDE.md 형식으로 변환 및 다운로드

## 기술 스택

| 구분 | 기술 |
|------|------|
| Backend | Flask 3.0, Python |
| Database | SQLite (WAL 모드) |
| Frontend | Vanilla JS, CSS (반응형) |

## 프로젝트 구조

```
claude-code-templates/
├── app.py              # Flask 메인 앱 (라우트 정의)
├── database.py         # SQLite DB 관리 (TemplateDB 클래스)
├── requirements.txt    # Python 의존성
├── .env.example        # 환경변수 템플릿
├── .gitignore
├── templates/
│   ├── base.html       # 기본 레이아웃
│   ├── index.html      # 템플릿 목록 (메인)
│   ├── form.html       # 등록/수정 폼
│   └── detail.html     # 상세 + 내보내기
└── static/
    ├── css/style.css   # 스타일시트
    └── js/app.js       # 클립보드 복사, 탭 전환, 다운로드
```

## 실행 방법

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

엑셀 가져오기 기능을 사용하려면 추가로:

```bash
pip install openpyxl
```

### 2. 환경변수 설정 (선택)

```bash
cp .env.example .env
# .env 파일에서 SECRET_KEY 수정
```

### 3. 서버 실행

```bash
python app.py
```

서버가 `http://localhost:5002` 에서 실행됩니다.

### 4. 접속

브라우저에서 http://localhost:5002 접속

## 사용 흐름

1. **템플릿 등록** - `+ 새 템플릿` 버튼으로 프로젝트 정보 입력
2. **엑셀 가져오기** - 기존 엑셀 파일이 있으면 `엑셀 가져오기`로 일괄 등록
3. **상세 확인** - 카드 클릭하여 상세 정보 확인
4. **Claude Code로 내보내기**
   - `프롬프트 복사` 탭 → 복사 버튼 → Claude Code에 붙여넣기
   - `CLAUDE.md 생성` 탭 → 다운로드 → 프로젝트 루트에 배치

## 템플릿 필드

| 필드 | 설명 |
|------|------|
| 이름 | 템플릿 이름 (필수) |
| 유형 | new / update / refactor / bugfix |
| 프로젝트명 | 대상 프로젝트 이름 |
| 기술스택 | 사용 기술 (쉼표 구분) |
| 작업파일 | 작업 대상 파일 목록 |
| 목표 | 프로젝트가 달성할 목표 |
| 배경 | 프로젝트 배경 설명 |
| 요구사항 | 기능 요구사항 목록 |
| 입력 | 입력 데이터 설명 |
| 산출물 | 기대 산출물 |
| 금지사항 | 제외할 내용 |
| 참고패턴 | 참고할 코드/패턴 |

## API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | `/` | 템플릿 목록 (검색: `?q=키워드`) |
| GET | `/template/new` | 등록 폼 |
| GET | `/template/<id>` | 상세 페이지 |
| GET | `/template/<id>/edit` | 수정 폼 |
| POST | `/api/template` | 템플릿 생성 |
| POST | `/api/template/<id>` | 템플릿 수정 |
| POST | `/api/template/<id>/delete` | 템플릿 삭제 |
| GET | `/api/template/<id>/prompt` | 프롬프트 텍스트 (JSON) |
| GET | `/api/template/<id>/claude-md` | CLAUDE.md 텍스트 (JSON) |
| POST | `/api/import-excel` | 엑셀 파일 가져오기 |
