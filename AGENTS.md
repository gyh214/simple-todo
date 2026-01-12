# PROJECT KNOWLEDGE BASE

**Generated:** 2025-01-13 12:24 AM
**Version:** 2.7.6
**Branch:** main

## OVERVIEW
PyQt6 데스크톱 TodoPanel 애플리케이션 - CLEAN Architecture, JSON 저장소, 자동 업데이트 기능 포함

## STRUCTURE
```
new-todo-panel/
├── src/
│   ├── core/           # DI Container (싱글톤)
│   ├── domain/         # 비즈니스 로직 (entities, value objects, services)
│   ├── application/    # 유스케이스, 앱 서비스
│   ├── infrastructure/ # JSON 리포지토리, 파일 시스템, GitHub API
│   └── presentation/  # PyQt6 UI (위젯, 다이얼로그, 시스템 매니저)
├── tests/             # 단 1개 테스트 파일만 존재
├── main.py            # 앱 진입점
├── config.py          # 중앙 설정 (경로, 색상, UI 메트릭)
├── build.py           # PyInstaller 빌드 스크립트
└── TodoPanel_Data/    # 데이터 저장소 (자동 생성)
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| 도메인 비즈니스 로직 | `src/domain/entities/`, `src/domain/services/` | Todo, SubTask, RecurrenceService, TodoSearchService |
| 밸류 오브젝트 | `src/domain/value_objects/` | TodoId, Content, DueDate, RecurrenceRule (불변 dataclass) |
| 유스케이스 | `src/application/use_cases/` | SortTodos, ReorderTodo, CheckForUpdates, DownloadUpdate, InstallUpdate |
| CRUD 서비스 | `src/application/services/todo_service.py` | TodoService (중앙 비즈니스 로직) |
| JSON 저장소 | `src/infrastructure/repositories/todo_repository_impl.py` | 자동 백업 + debounce 저장 (300ms) |
| UI 위젯 | `src/presentation/widgets/` | TodoItemWidget, SectionWidget, RichTextWidget, CustomSplitter |
| 이벤트 핸들러 | `src/presentation/ui/event_handlers/` | MainWindowEventHandler (시그널/슬롯 연결) |
| 빌드/배포 | `build.py`, `simple_todo.spec` | PyInstaller 단일 exe, 아이콘, 버전 정보 자동 생성 |
| 설정/스타일 | `config.py` | 경로, 색상 테마, UI 메트릭, 윈도우 설정 |

## CONVENTIONS

### CLEAN Architecture Layering
```
Presentation (PyQt6) → Application → Domain ← Infrastructure
```
- Domain: 외부 의존성 없음, 순수 비즈니스 로직
- Application: 유스케이스 조율, Domain 서비스 사용
- Infrastructure: JSON 파일, GitHub API, 파일 시스템
- Presentation: PyQt6 UI, Application/Infrastructure 의존

### DI Container Pattern
- `src/core/container.py` - 싱글톤 Container 클래스
- `ServiceNames` 상수로 타입 안전한 서비스 이름 관리
- 등록: `Container.register(ServiceNames.TODO_REPOSITORY, repository)`
- 조회: `Container.resolve(ServiceNames.TODO_SERVICE)`

### 밸류 오브젝트 (불변)
- `@dataclass(frozen=True)` 사용
- 팩토리 메서드: `.create()`, `.from_string()`, `.from_dict()`
- 예: `TodoId.generate()`, `Content(value="text")`, `DueDate.from_string("2025-12-31")`

### Repository 패턴
- 인터페이스: `src/domain/interfaces/repository_interface.py` (ABC)
- 구현체: `src/infrastructure/repositories/todo_repository_impl.py`
- 메서드: `find_all()`, `find_by_id()`, `save()`, `delete()`

### PyQt6 시그널/슬롯
- 위젯 간 통신: `pyqtSignal` → `.connect(handler)`
- 이벤트 핸들러: `src/presentation/ui/event_handlers/main_window_event_handler.py`
- 예: `todo_widget.edited.connect(self.event_handler.handle_edit)`

### 로깅
- 모든 모듈: `logger = logging.getLogger(__name__)`
- 로그 파일: 개발 환경 `logs/app_*.log`, 배포 환경 `%TEMP%/SimpleTodo_*/app.log` (종료 시 삭제)
- 디버그 모드: `main.py --debug` → 영구 로그 저장

## ANTI-PATTERNS (THIS PROJECT)
- ❌ 계획 없이 코드 작성 시작 (CLAUDE.md)
- ❌ 테스트 없이 구현 (CLAUDE.md - 현재 테스트 커버리지 매우 낮음: 1개 파일)
- ❌ TODO/임시방편 코드 작성 (CLAUDE.md)
- ❌ 중복 코드 작성 (CLAUDE.md - 기존 코드 재사용 우선)
- ❌ 명확하지 않은 커밋 메시지 (CLAUDE.md)
- ❌ README에 SQLite 명시 (실제는 JSON 저장) - 오류 수정 필요

## UNIQUE STYLES

### 센티넬 패턴 (Sentinel Object)
- `_UNDEFINED = object()` - None과 구별하는 용도
- 사용처: `TodoService.update_subtask(due_date=_UNDEFINED)` → 납기일 변경 생략

### 비동기 배치 저장 (Debounce)
- `DebounceManager` - 300ms 딜레이로 UI 블로킹 최소화
- 위치: `src/infrastructure/utils/debounce_manager.py`
- 사용처: `TodoRepositoryImpl.save()` → 자동 백업 + 디스크 저장 딜레이

### 원자적 저장
- 임시 파일 생성 → 원본 파일 교체 (os.replace)
- 위치: `TodoRepositoryImpl._save_to_disk()`
- 목적: 데이터 무결성 보장

### 레거시 마이그레이션
- `MigrationService` - 레거시 데이터 포맷 자동 감지 및 변환
- 위치: `src/infrastructure/file_system/migration_service.py`

### 전역 다크 모드 팔레트
- `setup_global_palette(app)` - Windows 시스템 테마 무시
- 위치: `main.py`
- 색상: `config.py`의 `COLORS` 딕셔너리 기반

### 단일 인스턴스 실행
- `SingleInstanceManager` - 포트 65432로 이미 실행 여부 체크
- 위치: `src/presentation/system/single_instance.py`
- 동작: 중복 실행 시 기존 창 활성화

## COMMANDS
```bash
# 개발 실행
python main.py                # 기본 모드
python main.py --debug        # 디버그 모드 (영구 로그)

# 빌드
python build.py               # 기본 빌드
python build.py --debug      # 디버그 빌드
python build.py --keep-temp  # 임시 파일 유지

# 테스트
pytest tests/                # 테스트 실행 (현재 1개 파일)
```

---

## src/infrastructure

### OVERVIEW
JSON 저장소, 파일 시스템, GitHub API 외부 연동 계층

### WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Todo CRUD | `repositories/todo_repository_impl.py` | 300ms debounce 저장, 자동 백업, 레거시 마이그레이션 |
| GitHub 릴리스 | `repositories/github_release_repository.py` | SimpleTodo.exe 에셋 검색, Release 엔티티 변환 |
| 업데이트 설정 | `repositories/update_settings_repository.py` | lastUpdateCheck, skippedVersion, autoCheckEnabled 관리 |
| 백업 시스템 | `file_system/backup_service.py` | 자동 백업 생성 (data_YYYYMMDD_HHMMSS.json), 최대 N개 유지, 복구 지원 |
| 데이터 마이그레이션 | `file_system/migration_service.py` | 레거시 포맷 감지, manualOrder 필드 추가/제거 |
| 업데이트 다운로드 | `services/update_downloader_service.py` | HTTP 스트리밍, 8KB 청크, 진행률 콜백, 3회 재시도 |
| 업데이트 설치 | `services/update_installer_service.py` | 배치 스크립트 생성, 파일 교체, 프로세스 종료 대기 |
| Debounce 유틸 | `utils/debounce_manager.py` | QTimer 기반, 300ms 지연, 콜백 데이터 전달 |

### CONVENTIONS

#### 원자적 파일 조작
- 임시 파일(.tmp) 생성 → 원본 교체(os.replace/shutil.move)
- 예: `TodoRepositoryImpl._save_to_disk()`, `UpdateSettingsRepository._save_data()`
- 목적: 쓰기 중단 시 데이터 무결성 보장

#### Thread-safe 리포지토리
- `RLock` 사용: 재진입 가능한 스레드 락
- 위치: `TodoRepositoryImpl._lock`, `UpdateSettingsRepository._lock`
- 용도: PyQt6 메인 스레드 + 비동기 저장 스레드 동시 접근 보호

#### Debounce 패턴 (저장 최적화)
- `DebounceManager.schedule(data)` → 연속 호출 시 마지막만 300ms 후 실행
- 드래그 앤 드롭 등 즉시 저장 필요 시 `immediate=True`
- 사용처: `TodoRepositoryImpl._save_data(immediate=False/True)`

#### GitHub API 요청
- 기본 타임아웃: 10초
- User-Agent: `SimpleTodo-AutoUpdater/1.0`
- 에러 처리: 404(None), 403(rate limit), 네트워크 오류(None)

### ANTI-PATTERNS (INFRASTRUCTURE)
- ❌ 원자적 저장 누락 → 쓰기 중단 시 데이터 손상
- ❌ RLock 데드락 → context manager 사용 권장
- ❌ 파일 읽기/쓰기 오류 미복구 → 백업에서 복구 로직 필요

---

## NOTES
- **데이터 저장**: JSON 파일 (`TodoPanel_Data/data.json`) - README의 SQLite 명시는 오류
- **백업**: `TodoPanel_Data/backups/data_YYYYMMDD_HHMMSS.json` - 무제한 보관
- **업데이트**: GitHub Releases API 연동, 24시간마다 자동 체크
- **CI/CD**: 없음 (빌드는 로컬 수동)
- **패키징**: `pyproject.toml` 없음, `requirements.txt`만 사용
- **LSP 서버**: 미설치됨 (basedpyright 설치 권장)
- **테스트 커버리지**: 매우 낮음 (1개 테스트 파일: `test_todo_service_subtask_update.py`)
