# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 🚨 CRITICAL FILE PATH RULES 🚨

**이 규칙을 어기면 파일 수정이 실패합니다. 매번 반드시 준수하세요.**

### 필수 규칙:
1. **항상 상대 경로만 사용** (절대 경로 금지)
2. **Forward slash(/) 필수** (Backslash(\) 절대 금지)
3. **Windows 드라이브 문자 사용 금지** (D:\, C:\ 등)

### 올바른 예시 ✅
- `src/infrastructure/repositories/todo_repository_impl.py`
- `./src/components/Component.tsx`
- `tests/unit/test_user.py`

### 잘못된 예시 ❌
- `src\infrastructure\repositories\todo_repository_impl.py` (백슬래시)
- `D:\dev_proj\new-todo-panel\src\...` (절대 경로)
- `C:/Users/user/project/src/...` (절대 경로)

**이 규칙은 Claude Code 버그 #7443 회피를 위한 필수 규칙입니다.**

## 프로젝트 개요

**Simple ToDo**는 화면의 1/4 크기로 실행되는 심플한 할일 관리 데스크톱 애플리케이션입니다.

- **플랫폼**: Windows 데스크톱
- **권장 해상도**: 420x600 (최소 300x400)
- **기술 스택**: (구현 예정 - Python/Electron/WPF 등)
- **아키텍처**: CLEAN Architecture 기반

---

## 프로젝트 구조

```
new-todo-panel/
├── docs/
│   ├── Simple_ToDo_기능_명세서.md    # 전체 기능 명세서 (필독)
│   └── todo-app-ui.html              # UI 프로토타입 (레이아웃/색상 참고)
├── TodoPanel_Data/                   # 런타임 데이터 디렉토리 (자동 생성)
│   ├── data.json                     # TODO 데이터 + 설정
│   └── data_*.json                   # 백업 파일들
└── (소스 코드 디렉토리 - 구현 예정)
```

---

## 핵심 기능

### 1. TODO 관리
- **생성**: Enter 키 또는 추가 버튼
- **수정**: 더블클릭으로 편집 다이얼로그
- **삭제**: 호버 시 ✕ 버튼 (확인 다이얼로그 표시)
- **완료 처리**: 체크박스로 진행중 ⟷ 완료 섹션 이동

### 2. 정렬 및 순서
- **정렬**: 납기일 빠른순/늦은순 (드롭다운)
- **드래그 앤 드롭**: ☰ 핸들로 순서 변경 (섹션 내부만 가능)

### 3. 섹션 관리
- **진행중/완료 섹션**: 독립적 스크롤 영역
- **분할바**: 드래그로 섹션 비율 조정 (최소 10% 제한)
- **비율 저장**: 재시작 시 유지

### 4. 납기일
- **설정**: 편집 다이얼로그에서 캘린더 UI로 선택
- **표시**: "X일 남음", "오늘", "X일 지남"
- **시각적 구분**:
  - 만료 (지난 날짜): `rgba(204, 120, 92, 0.2)` 배경
  - 오늘: `rgba(204, 120, 92, 0.2)` 배경
  - 임박 (3일 이내): `rgba(204, 120, 92, 0.15)` 배경

### 5. 링크 및 경로 인식
- **웹 링크**: `http://`, `https://`, `www.`로 시작하는 URL 자동 감지
- **파일 경로**: `C:\`, `D:\`, `\\server\` 등 자동 감지
- **클릭 동작**: 브라우저/탐색기/연결 프로그램으로 열기

---

## 색상 테마 (Dark Mode)

반드시 `docs/todo-app-ui.html` 프로토타입의 색상을 따를 것:

```css
Primary Background:  #1A1A1A
Secondary Background: #2A2A2A
Card/Surface:         #2D2D2D
Text Primary:         rgba(255, 255, 255, 0.92)
Text Secondary:       #B0B0B0
Text Disabled:        #6B6B6B
Accent Color:         #CC785C (Claude 주황색)
Accent Hover:         #E08B6F
Border/Divider:       rgba(64, 64, 64, 0.3)
```

---

## 데이터 구조

### data.json 형식
```json
{
  "version": "1.0",
  "settings": {
    "sortOrder": "dueDate_asc",      // "dueDate_asc" | "dueDate_desc"
    "splitRatio": [1, 1],            // [진행중 비율, 완료 비율]
    "alwaysOnTop": false
  },
  "todos": [
    {
      "id": "uuid-1",
      "content": "할일 내용",
      "completed": false,
      "createdAt": "2025-01-01T10:00:00Z",
      "dueDate": "2025-01-05T00:00:00Z",  // optional
      "order": 0
    }
  ]
}
```

### 데이터 관리 원칙
1. **자동 저장**: 모든 변경사항 즉시 저장
2. **비동기 배치 저장**: UI 블로킹 없음
3. **원자적 저장**: 임시 파일 → 원본 교체
4. **백업**: 저장 시마다 생성, 최근 10개 유지
5. **레거시 마이그레이션**: `text` → `content` 자동 변환

### 레거시 데이터 마이그레이션

기존 data.json (구형 포맷)을 자동으로 새 형식으로 변환합니다.

#### 1. 레거시 형식 감지
```python
# 파일 로드 시 형식 확인
def detect_legacy_format(data):
    # 배열이면 레거시 형식
    if isinstance(data, list):
        return True
    # version 필드 없으면 레거시
    if isinstance(data, dict) and "version" not in data:
        return True
    return False
```

#### 2. 필드 변환 규칙

| 레거시 필드 | 새 필드 | 비고 |
|------------|---------|------|
| `text` | `content` | 필수 |
| `created_at` | `createdAt` | 필수 |
| `due_date` | `dueDate` | 선택 (null 허용) |
| `position` | `order` | 필수 |
| `modified_at` | (삭제) | 신규 버전에서는 미사용 |

#### 3. 자동 마이그레이션 로직
```python
def migrate_legacy_data(legacy_data):
    """
    레거시 형식을 새 형식으로 변환

    입력 (레거시):
    [
      {
        "id": "...",
        "text": "할일",
        "completed": false,
        "created_at": "2025-09-21T20:26:04.532355",
        "due_date": "2025-09-02",
        "position": 0
      }
    ]

    출력 (새 형식):
    {
      "version": "1.0",
      "settings": {
        "sortOrder": "dueDate_asc",
        "splitRatio": [1, 1],
        "alwaysOnTop": false
      },
      "todos": [
        {
          "id": "...",
          "content": "할일",
          "completed": false,
          "createdAt": "2025-09-21T20:26:04.532355",
          "dueDate": "2025-09-02",
          "order": 0
        }
      ]
    }
    """

    # 레거시 배열을 todos로 변환
    if isinstance(legacy_data, list):
        todos = legacy_data
    else:
        todos = legacy_data.get("todos", [])

    # 각 TODO 항목 변환
    migrated_todos = []
    for todo in todos:
        migrated_todo = {
            "id": todo["id"],
            "content": todo.get("text", todo.get("content", "")),
            "completed": todo.get("completed", False),
            "createdAt": todo.get("created_at", todo.get("createdAt", "")),
            "order": todo.get("position", todo.get("order", 0))
        }

        # dueDate는 선택적
        due_date = todo.get("due_date", todo.get("dueDate"))
        if due_date:
            migrated_todo["dueDate"] = due_date

        migrated_todos.append(migrated_todo)

    # 새 형식으로 구성
    return {
        "version": "1.0",
        "settings": {
            "sortOrder": "dueDate_asc",  # 기본값: 납기일 빠른순
            "splitRatio": [1, 1],         # 기본값: 1:1 비율
            "alwaysOnTop": False          # 기본값: 항상 위 비활성화
        },
        "todos": migrated_todos
    }
```

#### 4. 마이그레이션 실행 시점
- **앱 시작 시**: data.json 로드 직후 자동 실행
- **형식 감지**: `detect_legacy_format()` 으로 확인
- **변환 후 즉시 저장**: 변환된 데이터를 data.json에 덮어쓰기
- **백업 생성**: 변환 전 원본을 `data_legacy_backup_YYYYMMDD_HHMMSS.json`으로 저장

#### 5. 기본값 설정

누락된 필드는 다음 기본값을 사용:

```python
DEFAULT_SETTINGS = {
    "sortOrder": "dueDate_asc",    # 납기일 빠른순
    "splitRatio": [1, 1],          # 진행중:완료 = 1:1
    "alwaysOnTop": False           # 항상 위 비활성화
}

DEFAULT_TODO_FIELDS = {
    "content": "",                 # 빈 문자열
    "completed": False,            # 미완료
    "createdAt": current_time(),   # 현재 시각
    "order": 0                     # 첫 번째 위치
}
```

#### 6. 에러 처리
- 변환 실패 시: 원본 보존, 에러 로그 기록, 사용자에게 알림
- 필수 필드 누락 시: 기본값으로 채우되 경고 로그
- 잘못된 데이터 타입: 타입 변환 시도, 실패 시 항목 건너뛰기

---

## 아키텍처

### CLEAN Architecture 레이어
```
┌─────────────────────────────────────┐
│      Presentation Layer              │  UI, Event Handlers, Managers
├─────────────────────────────────────┤
│      Application Layer               │  TodoService, Use Cases
├─────────────────────────────────────┤
│      Domain Layer                    │  Todo Entity, Value Objects
├─────────────────────────────────────┤
│      Infrastructure Layer            │  Repository, File System, System
└─────────────────────────────────────┘
```

### 핵심 컴포넌트 (구현 시 생성)
- **TodoService**: 비즈니스 로직 (생성/수정/삭제/완료/정렬)
- **TodoRepository**: 데이터 영속성 (저장/로드/백업)
- **UIManager**: UI 구성 및 업데이트
- **EventHandler**: 사용자 입력 처리
- **DataPreservationService**: 데이터 무결성 보장

---

## 시스템 통합

### 시스템 트레이
- 최소화 시 트레이로 이동
- 좌클릭: 창 표시/숨김 토글
- 우클릭 메뉴: "표시", "숨기기", "종료"

### 단일 인스턴스
- 포트 65432 기반 락
- 중복 실행 시 기존 창 활성화

### 윈도우 관리
- 최소 크기: 300x400
- "항상 위" 토글 기능

---

## 키보드 단축키

- **Enter**: 입력창에서 TODO 추가
- **Esc**: 다이얼로그 닫기
- **Ctrl+N**: 새 TODO 추가 (입력창 포커스)
- **Delete**: 선택된 TODO 삭제
- **F2**: 선택된 TODO 편집

---

## 성능 요구사항

- **UI 업데이트**: 50ms 이내
- **스크롤**: 60fps 유지
- **최대 TODO**: 1000개 이상 지원
- **초기 메모리**: 50MB 이하
- **1000개 TODO 메모리**: 100MB 이하

---

## 개발 가이드라인

### 코드 작성 시 준수사항
1. **UI 프로토타입 엄수**: `docs/todo-app-ui.html`의 레이아웃, 색상, 간격을 정확히 따를 것
2. **데이터 무결성**: 모든 필드(createdAt, order 등) 자동 보존
3. **에러 처리**: 저장 실패 시 최대 3회 재시도, 로그 기록
4. **비동기 처리**: 파일 I/O는 비동기로 처리하여 UI 블로킹 방지
5. **정규식 검증**: 링크/경로 인식 시 명세서의 정규식 사용

### 테스트 필수 항목
- 드래그 앤 드롭 동작
- 분할바 리사이징
- 날짜 계산 로직 (만료/오늘/임박/일반)
- URL/경로 감지 정규식
- 데이터 저장/로드/백업/복구
- **레거시 데이터 마이그레이션** (구형 포맷 → 신규 포맷)

### Windows 환경 특이사항
- 절대 경로 사용: `C:\...`, `D:\...`
- Python 파일 읽기 시 UTF-8 인코딩 명시: `open(..., encoding='utf-8')`
- 가상환경에서 작업
- Pager 사용 금지 명령어 옵션 추가

---

## 참고 문서

- **기능 명세서**: `docs/Simple_ToDo_기능_명세서.md` (전체 기능 상세 설명)
- **UI 프로토타입**: `docs/todo-app-ui.html` (실제 레이아웃/색상/간격 참고)

---

## 향후 확장 가능성

- 태그/카테고리 시스템
- 검색/필터링
- 반복 TODO
- 클라우드 백업/동기화
- 캘린더/이메일/슬랙 연동
