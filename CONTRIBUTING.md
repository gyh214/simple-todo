# 기여 가이드

Simple ToDo 프로젝트에 기여해주셔서 감사합니다! 이 문서는 프로젝트에 기여하는 방법을 설명합니다.

## 🚀 빠른 시작

### 개발 환경 설정

#### 필수 요구사항
- Python 3.7 이상
- Windows 10 이상
- Git

#### 저장소 클론
```bash
git clone https://github.com/gyh214/simple-todo.git
cd new-todo-panel
```

#### 가상환경 설정
```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

#### 앱 실행
```bash
# 기본 모드
python main.py

# 디버그 모드 (상세 로그 포함)
python debug_main.py
```

---

## 📋 개발 워크플로우

### 1. 이슈 생성 또는 선택

**새로운 기능이나 버그를 발견했다면:**
1. [Issues](../../issues) 페이지 확인
2. 기존 이슈가 없으면 새로운 이슈 생성
3. 레이블 지정: `bug`, `enhancement`, `documentation` 등

**이슈 작성 가이드:**
- **제목**: 명확하고 간결하게
- **설명**: 문제 상황, 기대 결과, 재현 방법 기술
- **스크린샷**: 가능하면 스크린샷 포함
- **환경**: Python 버전, Windows 버전 명시

### 2. Feature 브랜치 생성

```bash
# 최신 코드 업데이트
git checkout main
git pull origin main

# Feature 브랜치 생성
git checkout -b feature/your-feature-name
```

**브랜치 네이밍 규칙:**
- `feature/`: 새로운 기능 (예: `feature/add-recurring-todos`)
- `fix/`: 버그 수정 (예: `fix/crash-on-empty-input`)
- `docs/`: 문서 개선 (예: `docs/update-readme`)
- `refactor/`: 코드 리팩토링 (예: `refactor/clean-architecture`)

### 3. 코드 작성

#### 코드 스타일 가이드

**Python PEP 8 준수:**
```python
# Good
def add_todo(content: str, due_date: Optional[datetime] = None) -> Todo:
    """새로운 TODO를 추가합니다.

    Args:
        content: TODO 내용
        due_date: 납기일 (선택)

    Returns:
        생성된 Todo 객체
    """
    return Todo(content=content, due_date=due_date)

# Bad
def AddTodo(content,dueDate=None):
    return Todo(content, dueDate)
```

**스타일 규칙:**
- 클래스명: `PascalCase` (예: `MainWindow`, `TodoService`)
- 함수/변수명: `snake_case` (예: `add_todo`, `due_date`)
- 상수명: `UPPER_SNAKE_CASE` (예: `DEFAULT_TIMEOUT`)
- 4칸 들여쓰기 (탭 금지)

**Type Hints 사용:**
```python
from typing import Optional, List

def get_todos_by_status(status: str) -> List[Todo]:
    """상태별로 TODO를 조회합니다."""
    pass
```

**Docstring (Google Style):**
```python
def reorder_todos(todo_ids: List[str], section: str) -> bool:
    """여러 TODO의 순서를 변경합니다.

    Args:
        todo_ids: TODO ID 리스트
        section: 섹션명 ('pending' 또는 'completed')

    Returns:
        성공 여부

    Raises:
        ValueError: 유효하지 않은 섹션명
    """
    if section not in ['pending', 'completed']:
        raise ValueError(f"Invalid section: {section}")
    # ... 구현
```

#### CLEAN Architecture 준수

프로젝트는 CLEAN Architecture를 따릅니다. 각 레이어의 책임을 명확히 하세요:

```
src/
├── domain/              # 비즈니스 로직 (외부 의존성 없음)
│   ├── entities/        # Todo, SubTask 등 도메인 객체
│   ├── value_objects/   # TodoId, DueDate 등 값 객체
│   └── services/        # 도메인 서비스 (TodoSortService 등)
│
├── application/         # 유스케이스 (도메인 사용)
│   └── services/        # TodoService 등 애플리케이션 서비스
│
├── infrastructure/      # 외부 의존성 (DB, 파일 시스템)
│   └── repositories/    # TodoRepositoryImpl 등
│
└── presentation/        # UI (PyQt6)
    ├── system/          # 시스템 통합 (트레이, 단일 인스턴스)
    └── ui/              # UI 컴포넌트
```

**레이어 간 의존성 규칙:**
- ✅ Presentation → Application → Domain
- ✅ Infrastructure → Domain
- ❌ Domain → Application
- ❌ Domain → Presentation

### 4. 테스트

프로젝트에 테스트 스위트가 있다면 다음을 실행하세요:

```bash
# 모든 테스트 실행
python -m pytest

# 특정 테스트만 실행
python -m pytest tests/unit/test_todo_service.py

# 테스트 커버리지 확인
python -m pytest --cov=src tests/
```

**테스트 작성 가이드:**
- 모든 새로운 기능에 대해 테스트 작성
- 테스트 파일: `tests/unit/`, `tests/integration/`
- 테스트 네이밍: `test_<function_name>_<scenario>`

### 5. 빌드 확인

변경사항을 반영하여 빌드가 성공하는지 확인하세요:

```bash
# 기본 빌드
python build.py

# 디버그 빌드 (상세 출력)
python build.py --debug

# 빌드 결과 확인
ls dist/SimpleTodo.exe
```

빌드 성공 확인:
- `dist/SimpleTodo.exe` 파일 생성됨
- 컴파일 에러/경고 없음
- 실행 파일이 정상 작동함

### 6. Commit 작성

```bash
git add .
git commit -m "feat: 새로운 기능 설명"
```

**Commit Message 규칙:**
```
<type>: <subject>

<body>

<footer>
```

**Type:**
- `feat`: 새로운 기능
- `fix`: 버그 수정
- `docs`: 문서 변경
- `refactor`: 코드 리팩토링
- `style`: 코드 스타일 (공백, 포맷 등)
- `test`: 테스트 추가/수정
- `chore`: 빌드 스크립트, 의존성 등

**예시:**
```
feat: 반복 할일 기능 추가

매주/매달 반복되는 할일을 자동으로 생성하는 기능 추가

- 반복 주기 설정: 매일, 매주, 매달
- 다음 반복 날짜 자동 계산
- EditDialog에 반복 옵션 UI 추가

Fixes #123
```

### 7. Push 및 Pull Request 생성

```bash
# 브랜치 푸시
git push origin feature/your-feature-name
```

**Pull Request (PR) 작성:**

1. GitHub에서 PR 생성
2. 제목: 커밋 메시지와 동일하게
3. 설명에 다음 포함:
   - 변경사항 요약
   - 관련 이슈 (Fixes #123)
   - 테스트 방법
   - 스크린샷 (UI 변경 시)
4. 체크리스트 확인:
   - [ ] 코드 스타일 준수 (PEP 8)
   - [ ] 기능 테스트 완료
   - [ ] 빌드 성공 확인
   - [ ] 문서 업데이트 (필요 시)
   - [ ] 커밋 메시지 명확함

### 8. Code Review

PR이 생성되면:
- 자동 CI 체크 실행
- 메인테이너의 코드 리뷰
- 피드백 반영
- 승인 후 머지

**Code Review 대기 중:**
- 1-2주 내 피드백 제공
- 질문이나 추가 정보 필요 시 언급됨
- 대기하지 마시고 다른 작업 진행 가능

---

## 🎯 기여 아이디어

### 버그 리포트
- 앱 크래시, 성능 문제, UI 오류 보고
- 재현 방법, 예상 결과, 실제 결과 명시

### 기능 제안
- 새로운 기능 아이디어
- 사용자 경험 개선 방안
- 성능 최적화 제안

### 문서 개선
- README, CONTRIBUTING.md 개선
- 개발 가이드 확충
- 주석/Docstring 추가

### 코드 리팩토링
- CLEAN Architecture 준수
- 코드 중복 제거
- 테스트 커버리지 향상

---

## 📐 프로젝트 구조

```
new-todo-panel/
├── src/
│   ├── domain/                 # 도메인 로직
│   ├── application/            # 애플리케이션 로직
│   ├── infrastructure/         # 외부 의존성
│   ├── presentation/           # UI
│   └── core/                   # DI Container
├── tests/                      # 테스트
├── docs/                       # 문서
├── main.py                     # 진입점
├── config.py                   # 설정
├── build.py                    # 빌드 스크립트
└── requirements.txt            # 의존성
```

자세한 내용은 [DEVELOPMENT.md](docs/DEVELOPMENT.md)를 참고하세요.

---

## 🔍 개발 팁

### 자동 저장 메커니즘
```python
# TodoService의 auto_save 메서드가 모든 변경사항을 즉시 저장
# JSON 파일과 백업이 자동 업데이트됨
```

### 단일 인스턴스 관리
```python
# 포트 65432를 사용하여 중복 실행 방지
# 이미 실행 중인 앱을 활성화
```

### 데이터 백업
```python
# 최근 10개 백업을 TodoPanel_Data/backups/에 유지
# 데이터 손실 시 복구 가능
```

### 디버그 모드
```bash
# debug_main.py 실행으로 상세 로그 확인
# 문제 해결에 유용
python debug_main.py
```

---

## ❓ FAQ

### Q: PR은 언제 머지되나요?
**A:** 보통 코드 리뷰 후 1-2주 내 머지됩니다. 긴급 버그 수정은 빠르게 처리합니다.

### Q: 큰 기능 구현은 어떻게 진행하나요?
**A:** 먼저 이슈를 생성하여 논의 후 Feature 브랜치에서 개발하세요. PR 초안으로 진행상황을 공유할 수 있습니다.

### Q: 테스트는 필수인가요?
**A:** 새로운 기능에 대해서는 테스트 작성을 권장합니다. 버그 수정 시에는 재현 테스트를 추가해주세요.

### Q: 코드 스타일 자동 검사가 있나요?
**A:** 현재는 수동 리뷰입니다. PR에서 PEP 8 준수를 확인합니다. `black` 또는 `autopep8` 사용을 권장합니다.

### Q: 문서는 어디에 작성하나요?
**A:**
- 일반 사용자: `docs/USER_GUIDE.md`
- 개발자: `docs/DEVELOPMENT.md`
- 아키텍처: `docs/ARCHITECTURE.md`
- 기여 방법: `CONTRIBUTING.md`

---

## 📞 문의 및 지원

- **버그 리포트**: [Issues 페이지](../../issues)
- **기능 제안**: [Discussions](../../discussions) (있다면)
- **PR 피드백**: PR 페이지의 댓글

---

## 📝 릴리스 노트 작성 가이드

GitHub Release를 생성할 때 릴리스 노트를 작성해야 합니다. **릴리스 노트는 항상 사용자의 관점**에서 작성되어야 합니다.

> **언어 선택**: 한국어 또는 영어 모두 가능합니다. 한국어가 권장됩니다.

### 릴리스 노트 작성 원칙

#### ✅ 사용자 관점에서 작성

**좋은 예:**
```markdown
## v2.6.45 — 업데이트 체크 간격 개선 및 보안 안내

### 개선사항
- 업데이트 확인 주기를 1시간에서 1일로 변경하여 앱 성능 개선
- 보안 & 프라이버시 정보 추가로 사용자 신뢰도 향상
- Windows Defender 경고 안내 문서 추가

### 사용자에게 미치는 영향
- 앱이 더 빠르고 가볍게 실행됩니다
- 더 이상 매시간 업데이트를 확인하지 않습니다
- 새 사용자들이 Windows Defender 경고를 이해할 수 있습니다
```

**나쁜 예:**
```markdown
## v2.6.45 — Technical Updates

### Changes
- Modified UPDATE_CHECK_INTERVAL_HOURS from 1 to 24
- Added security section to README.md with privacy info
- Updated CONTRIBUTING.md with release notes guidelines
```

#### 📋 포함해야 할 요소

1. **버전과 제목**: 사용자가 한눈에 알 수 있는 요약
   - 예: `v2.6.45 — 업데이트 체크 개선 및 보안 안내`

2. **개선사항**: 사용자가 체감할 수 있는 변경사항
   - "더 빠른", "더 쉬운", "새롭게", "수정된" 등의 표현

3. **사용자 영향**: 실제로 사용할 때 어떻게 달라지는가
   - "이제 ~할 수 있습니다"
   - "더 이상 ~하지 않습니다"

#### 🚫 피해야 할 표현

- 기술 용어: "UPDATE_CHECK_INTERVAL_HOURS", "config.py" 등
- 내부 구조 설명: "CONTRIBUTING.md 업데이트", "README.md 수정"
- 개발자 관점: "리팩토링", "레이어 분리", "CI/CD 설정"

#### 🔄 기술 용어 → 사용자 언어 변환

| 기술 용어 | 사용자 언어 |
|----------|-----------|
| UPDATE_CHECK_INTERVAL_HOURS 변경 | 업데이트 확인 주기 개선 |
| README 보안 섹션 추가 | 보안 & 프라이버시 정보 공개 |
| Windows Defender 경고 안내 | Windows 보안 경고 해결 방법 안내 |
| Performance improvement | 앱이 더 빠르고 가볍게 실행됩니다 |
| Bug fix | 문제 해결: [사용자가 겪은 문제 설명] |

#### 📊 릴리스 노트 템플릿

```markdown
## v[VERSION] — [한 문장 요약]

### ✨ 개선사항
- [사용자 관점의 개선사항 1]
- [사용자 관점의 개선사항 2]
- [사용자 관점의 개선사항 3]

### 🐛 수정된 문제
- [사용자가 겪었던 문제 해결]

### 📝 기타 사항
- [알아두면 좋은 정보]

### 💾 설치
[최신 릴리스](https://github.com/gyh214/simple-todo/releases/latest)에서 `SimpleTodo.exe` 다운로드
```

### 예시

#### 한국어 릴리스 노트 예시 (권장)

**좋은 예:**
```markdown
## v2.6.45 — 성능 개선 및 보안 투명성 강화

### ✨ 개선사항
- 배터리 사용량 감소: 업데이트 확인이 매시간에서 하루에 한 번으로 변경됩니다
- 보안 정보 공개: "🔒 보안 & 프라이버시" 섹션에서 데이터 보호 방식을 확인하세요
- Windows 보안 경고 안내: 새 사용자도 쉽게 이해할 수 있도록 가이드 추가

### 📱 새 사용자를 위한 안내
README.md의 "🔒 보안 & 프라이버시" 섹션을 확인하세요.

### 💾 설치
[이곳](https://github.com/gyh214/simple-todo/releases/latest)에서 `SimpleTodo.exe` 다운로드
```

#### 영어 릴리스 노트 예시

**좋은 예:**
```markdown
## v2.6.45 — Performance boost & better security transparency

### ✨ What's New
- Reduced battery usage: App now checks for updates once a day instead of every hour
- Security information added: See exactly what data is kept private in our new "Security & Privacy" section
- Windows security warning guide: New users won't be confused by Windows Defender alerts

### 📱 For New Users
Check README.md's **"Security & Privacy"** section to learn how your data stays safe.

### 💾 Installation
Download `SimpleTodo.exe` from [here](https://github.com/gyh214/simple-todo/releases/latest)
```

#### 한국어 vs 영어 선택 가이드

| 상황 | 권장 언어 |
|------|---------|
| 일반 릴리스 | 한국어 (기본) |
| 국제 프로젝트 | 영어 |
| 양쪽 모두 지원해야 할 경우 | 한국어 + 영어 섹션 분리 |

---

## 📜 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.
기여하신 코드도 동일한 라이선스 적용됩니다.

---

**감사합니다! 함께 더 좋은 Simple ToDo를 만들어가겠습니다.** 🚀
