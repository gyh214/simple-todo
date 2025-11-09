---
id: structure
version: 1.0.0
status: active
created: 2025-11-09
updated: 2025-11-09
author: @tdd-implementer
language: ko
---

# Simple ToDo - 아키텍처 명세서

@DOC:STRUCTURE

## HISTORY

### v1.0.0 (2025-11-09)
- **INITIAL**: 프로젝트 기술 구조 정의
- **AUTHOR**: tdd-implementer
- **SCOPE**: CLEAN Architecture 설명, 데이터 흐름

---

## 1. 아키텍처 개요

### 1.1 CLEAN Architecture 원칙

Simple ToDo는 CLEAN Architecture 원칙을 따릅니다.
각 계층은 명확한 책임을 가지며, 의존성은 안쪽을 향합니다.

```
┌─────────────────────────────────────┐
│    Presentation Layer                │  UI Components
│  - MainWindow, Dialogs, Widgets    │  Event Handlers
├─────────────────────────────────────┤
│    Application Layer                 │  Use Cases
│  - Services, Use Cases              │  Business Logic
├─────────────────────────────────────┤
│    Domain Layer                      │  Entities
│  - Entities, Value Objects          │  Business Rules
├─────────────────────────────────────┤
│    Infrastructure Layer              │  External I/O
│  - Repositories, Database           │  External Services
└─────────────────────────────────────┘
```

### 1.2 계층 다이어그램

의존성 흐름: Presentation → Application → Domain ← Infrastructure

외부 의존성 (PyQt6, JSON 저장소)은 Infrastructure에만 위치합니다.

---

## 2. 계층별 설명

### 2.1 Presentation Layer

**책임**: 사용자 인터페이스 및 이벤트 처리

**주요 컴포넌트**:
- `MainWindow`: 애플리케이션 주 창 (QMainWindow 상속)
- `TodoWidget`, `SubTaskWidget`: 각 할일 항목 표현
- `EditDialog`, `DatePickerDialog`: 편집 UI
- `TrayManager`: 시스템 트레이 관리
- `SingleInstanceManager`: 단일 인스턴스 보장

**의존성**: PyQt6, Application Layer 서비스

### 2.2 Application Layer

**책임**: 비즈니스 로직 및 사용 사례 구현

**주요 컴포넌트**:
- `TodoService`: Todo 생성/수정/삭제 중앙 관리
- `SortTodosUseCase`: 정렬 로직
- `ReorderTodoUseCase`: 순서 변경 로직
- `DataPreservationService`: 자동 저장 및 백업
- `UpdateManagerService`: 자동 업데이트 확인 (SPEC-002)

**의존성**: Domain Layer, Infrastructure Layer

### 2.3 Domain Layer

**책임**: 핵심 비즈니스 엔티티 및 규칙

**주요 컴포넌트**:
- `Todo` Entity: 핵심 할일 엔티티 (ID, 제목, 설명, 완료 여부, 납기일, SubTasks)
- `SubTask` Entity: 하위 할일 엔티티
- `TodoId`, `Content`, `DueDate`: Value Objects
- `TodoSortService`: 정렬 규칙 (도메인 로직)

**특징**: 외부 의존성 없음 (순수 Python)

### 2.4 Infrastructure Layer

**책임**: 외부 시스템과의 통신

**주요 컴포넌트**:
- `TodoRepositoryImpl`: JSON 기반 저장소
- `BackupManager`: 백업 관리 (최근 10개 유지)
- `MigrationService`: 레거시 데이터 마이그레이션
- `DebounceManager`: 빈번한 저장 요청 병합

**의존성**: PyQt6, JSON, psutil, requests

---

## 3. 핵심 엔티티

### 3.1 Todo Entity

```
Todo
├── id: TodoId (고유 식별자)
├── content: Content (제목/설명)
├── dueDate: Optional[DueDate] (납기일)
├── isCompleted: bool (완료 여부)
├── subtasks: List[SubTask] (하위 할일)
├── createdAt: datetime (생성 시간)
└── updatedAt: datetime (수정 시간)
```

### 3.2 SubTask Entity

```
SubTask
├── id: str (고유 식별자)
├── content: str (제목)
├── isCompleted: bool (완료 여부)
└── parentId: TodoId (부모 할일)
```

### 3.3 Value Objects

- `TodoId`: 불변 ID (UUID 기반)
- `Content`: 제목/설명 (길이 제한 있음)
- `DueDate`: 납기일 (유효성 검증 포함)

---

## 4. 데이터 흐름

### 4.1 Todo 생성 흐름

```
1. 사용자 입력 (Presentation)
   ↓
2. MainWindow → TodoService.createTodo()
   ↓
3. Application 검증
   ↓
4. Domain Entity 생성 (Todo)
   ↓
5. Infrastructure 저장 (TodoRepositoryImpl.save)
   ↓
6. UI 갱신 (Presentation)
```

### 4.2 Todo 수정 흐름

```
1. 사용자 더블클릭 → EditDialog 열기
   ↓
2. 기존 데이터 로드 (Infrastructure)
   ↓
3. 사용자 수정
   ↓
4. TodoService.updateTodo() 호출
   ↓
5. 저장소 업데이트 (Infrastructure)
   ↓
6. UI 갱신 (Presentation)
```

### 4.3 SubTask 관리 흐름

```
1. EditDialog에서 SubTask 추가/수정/삭제
   ↓
2. Todo Entity의 subtasks 리스트 변경
   ↓
3. 전체 Todo 객체 저장 (부모와 자식 함께)
   ↓
4. 펼침 상태 유지 (별도 관리)
```

---

## 5. 의존성 관리

### 5.1 DI Container

`src/core/container.py`에서 모든 서비스 생성을 관리합니다.

```python
class Container:
    - create_todo_service()
    - create_repository()
    - create_backup_manager()
```

### 5.2 의존성 그래프

```
TodoService
├── TodoRepository (저장소)
├── DataPreservationService (백업)
└── TodoSortService (정렬)

TodoRepository
├── BackupManager (백업)
└── MigrationService (마이그레이션)
```

---

## 6. 확장 포인트

### 6.1 새로운 저장소

기존 `TodoRepositoryImpl`을 상속하여 새로운 저장소 구현 가능:
- 클라우드 저장소 (SPEC-007)
- 데이터베이스 (SQLite, PostgreSQL)

**구현 방식**: `TodoRepository` 인터페이스를 상속하고 다음 메서드 구현:
- `save(todo: Todo) -> None`
- `load(todo_id: TodoId) -> Todo`
- `delete(todo_id: TodoId) -> None`
- `list_all() -> List[Todo]`

### 6.2 새로운 서비스

Application Layer에 새로운 UseCase 추가:
- 협업 기능 (SPEC-005): `ShareTodoUseCase`, `CommentTodoUseCase`
- 고급 필터링 (SPEC-006): `FilterTodosUseCase`, `SearchTodosUseCase`
- 분석 대시보드: `GenerateReportUseCase`, `AnalyzeTrendUseCase`

**구현 방식**: UseCase 인터페이스를 상속하고 `execute()` 메서드 구현

### 6.3 새로운 UI 컴포넌트

Presentation Layer에서 PyQt6 위젯 확장:
- 모바일 앱 (SPEC-008): 별도 `mobile/` 패키지
- 플러그인 아키텍처: `plugins/` 패키지에서 동적 로드

**구현 방식**: `QWidget` 상속 후 UI 설계, `Signal` 이용해 MainWindow와 통신

---

## 7. 의존성 방향성

### 7.1 의존성 규칙

1. **단방향**: Presentation → Application → Domain
2. **양방향 금지**: Domain은 상위 계층을 의존하지 않음
3. **Infrastructure 독립**: Domain은 Infrastructure 모름

### 7.2 테스트 용이성

각 계층은 의존성 주입으로 테스트 가능:
```python
# Domain 테스트 (외부 의존성 없음)
def test_todo_creation():
    todo = Todo(content="Test")
    assert todo.is_valid()

# Application 테스트 (Mock Repository 사용)
def test_create_todo_use_case():
    mock_repo = MockTodoRepository()
    use_case = CreateTodoUseCase(mock_repo)
    use_case.execute("Test")
    assert mock_repo.save_called
```

---

**상태**: ACTIVE (공개 문서)
**최종 검토**: 완료
**버전 기록**:
- v1.0.0 (2025-11-09): 초기 아키텍처 문서 작성
