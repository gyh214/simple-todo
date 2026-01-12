# src/domain KNOWLEDGE BASE

**Generated:** 2025-01-13
**Version:** 2.7.6
**Branch:** main

## OVERVIEW
도메인 계층 - 엔티티, 밸류 오브젝트, 도메인 서비스, 리포지토리 인터페이스

## STRUCTURE
```
src/domain/
├── entities/           # Todo, SubTask, BaseTask, Release
├── value_objects/      # TodoId, Content, DueDate, RecurrenceRule, AppVersion (불변)
├── services/          # TodoSortService, RecurrenceService, TodoSearchService, LinkDetectionService, VersionComparisonService
└── interfaces/        # ITodoRepository (추상 인터페이스)
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| 할일 비즈니스 로직 | `entities/todo.py` | Todo 엔티티 (하위 할일, 반복, 정렬) |
| 하위 할일 | `entities/subtask.py` | 1-depth만 지원, BaseTask 상속 |
| 공통 할일 메서드 | `entities/base_task.py` | complete(), toggle_complete(), update_content() |
| 불변 ID | `value_objects/todo_id.py` | UUID, .generate(), .from_string() |
| 내용 검증 | `value_objects/content.py` | 1-1000자, 공백 자동 제거 |
| 납기일 상태 | `value_objects/due_date.py` | overdue_severe/mild/mild, today, upcoming, normal |
| 반복 규칙 | `value_objects/recurrence_rule.py` | daily/weekly/monthly, end_date, weekdays, copy_subtasks |
| 버전 비교 | `value_objects/app_version.py` | Semantic Versioning, __lt__, __gt__ 등 지원 |
| 정렬 로직 | `services/todo_sort_service.py` | dueDate_asc/desc, today_first, manual |
| 반복 날짜 계산 | `services/recurrence_service.py` | 다음 반복 날짜, 종료일 체크 |
| 검색 로직 | `services/todo_search_service.py` | 메인 할일 + 하위 할일 검색 |
| 링크 감지 | `services/link_detection_service.py` | URL, Windows 경로 정규식 |
| 버전 비교 서비스 | `services/version_comparison_service.py` | major/minor/patch 업데이트 체크 |
| GitHub 릴리스 | `entities/release.py` | version, download_url, release_notes |
| 리포지토리 인터페이스 | `interfaces/repository_interface.py` | find_all(), find_by_id(), save(), delete() |

## CONVENTIONS

### 밸류 오브젝트 (불변)
- **@dataclass(frozen=True)** 사용하여 불변성 보장
- 팩토리 메서드 필수:
  - `.generate()` - 새 인스턴스 생성 (예: TodoId)
  - `.from_string()` - 문자열 파싱 (예: TodoId, DueDate, AppVersion)
  - `.from_dict()` - JSON 역직렬화 (예: RecurrenceRule, Todo)
  - `.create()` - 검증 포함 생성 (예: RecurrenceRule, Content)
- `__post_init__()`에서 검증 수행
- 불변 필드 수정 시 `object.__setattr__(self, 'field', value)` 사용 (Content의 공백 제거 예시)

### 엔티티 (가변)
- @dataclass 사용 (frozen 아님)
- BaseTask 추상 클래스 상속 (Todo, SubTask)
- `to_dict()`, `from_dict()` - JSON 직렬화/역직렬화
- 하위 할일 추가 시 자동 정렬 (`_sort_subtasks()`)
- SubTask는 하위 할일 없음 (1-depth만 지원)

### 도메인 서비스 (상태 없음)
- 모든 메서드 static
- 순수 비즈니스 로직만 포함
- 상태 없으므로 인스턴스화 불필요

### Semantic Versioning
- AppVersion: major.minor.patch
- 비교 연산자 오버로딩 (__lt__, __le__, __eq__, __ne__, __gt__, __ge__)
- "v" 접두사 자동 제거

### 리포지토리 패턴
- ITodoRepository 인터페이스 (ABC)
- 구현체는 infrastructure 레이어

## ANTI-PATTERNS (DOMAIN)

- ❌ 직접 인스턴스화 대신 팩토리 메서드 사용 (TodoId(), Content() 대신 TodoId.generate(), Content(value=...))
- ❌ @dataclass(frozen=True) 밸류 오브젝트 직접 수정 시도 (불변성 위반)
- ❌ 도메인 로직을 Application/Presentation 레이어에 배치
- ❌ 엔티티에서 외부 의존성 (Repository, Service) 직접 참조
- ❌ 도메인 서비스에 상태 저장 (모든 메서드 static)
- ❌ 밸류 오브젝트에서 복잡한 비즈니스 로직 포함 (도메인 서비스 사용)
- ❌ BaseTask 직접 인스턴스화 (추상 클래스, Todo/SubTask만 사용)
