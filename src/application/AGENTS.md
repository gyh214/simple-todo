# src/application

## OVERVIEW
비즈니스 로직 조율 및 Use Case 구현

## STRUCTURE
```
src/application/
├── services/          # 애플리케이션 서비스
│   ├── todo_service.py
│   ├── data_preservation_service.py
│   └── update_scheduler_service.py
├── use_cases/         # 유즈케이스
│   ├── sort_todos.py
│   ├── reorder_todo.py
│   ├── change_sort_order.py
│   ├── check_for_updates.py
│   ├── download_update.py
│   └── install_update.py
└── interfaces/        # 서비스 인터페이스
    └── service_interface.py
```

## WHERE TO LOOK
| 작업 | 위치 | 설명 |
|------|------|------|
| TODO CRUD | `services/todo_service.py` | 중앙 비즈니스 로직 - 생성, 수정, 삭제, 완료 토글, 일괄 작업 |
| 하위 할일 관리 | `services/todo_service.py` | SubTask CRUD, 순서 재정렬, 완료 토글 |
| 반복 할일 처리 | `services/todo_service.py` | RecurrenceRule 설정, 완료 시 다음 인스턴스 자동 생성 |
| 데이터 무결성 | `services/data_preservation_service.py` | ID 중복 검증, createdAt 보장, order 일관성 |
| 정렬 | `use_cases/sort_todos.py` | 납기일 기반 정렬 (진행중/완료 섹션 독립적) |
| 드래그 앤 드롭 | `use_cases/reorder_todo.py` | 섹션 내 순서 변경 (order 재계산, MANUAL 모드 전환) |
| 정렬 모드 변경 | `use_cases/change_sort_order.py` | 정렬 드롭다운 변경 시 order 동기화 |
| 업데이트 스케줄링 | `services/update_scheduler_service.py` | 앱 시작 시 체크 결정, 건너뛴 버전 관리 |
| 업데이트 확인 | `use_cases/check_for_updates.py` | GitHub Releases API, check_interval_hours 준수 |
| 업데이트 다운로드 | `use_cases/download_update.py` | 진행률 콜백, 파일 크기 검증, 임시 파일 정리 |
| 업데이트 설치 | `use_cases/install_update.py` | Batch script 생성, 프로세스 종료 후 파일 교체, 자동 재시작 |
| 서비스 인터페이스 | `interfaces/service_interface.py` | ITodoService 인터페이스 (ABC) |

## CONVENTIONS

### Use Case 패턴
- 모든 Use Case는 `execute()` 메서드로 진입점 제공
- 단일 책임: 하나의 비즈니스 작업만 담당
- Domain Service 위임: 복잡 로직은 Domain Service에 위임

### UpdateSchedulerService 조율 역할
- Use Case (`CheckForUpdatesUseCase`)와 Repository (`UpdateSettingsRepository`) 사이 중재
- 비즈니스 규칙:
  - 자동 체크 비활성화 시 체크 건너뜀
  - 건너뛴 버전은 알림 표시 안 함
  - 사용자 수동 체크 시 건너뛴 버전 초기화

### 드래그 앤 드롭 자동 모드 전환
- `ReorderTodoUseCase` 드롭 완료 시 자동으로 MANUAL 모드 전환
- 드래그 시작 전 현재 표시 순서를 order에 동기화

### 센티넬 패턴 (TodoService)
- `_UNDEFINED = object()` 사용: None과 구별하는 용도
- 예: `update_subtask(due_date=_UNDEFINED)` → 납기일 변경 생략

### DataPreservationService
- 저장 전 데이터 자동 검증 및 수정
- 호출됨: `TodoRepositoryImpl._save_to_disk()` 내부
- 검증 규칙: ID 중복 방지, order 연속성 보장, createdAt 누락 보완

## ANTI-PATTERNS
- ❌ Use Case에서 직접 UI 로직 구현 (UI는 Presentation 계층 담당)
- ❌ Repository에 비즈니스 로직 포함 (비즈니스 로직은 Service/Use Case 담당)
- ❌ 섹션 간 드래그 앤 드롭 (섹션 이동은 완료 처리로만 수행)
