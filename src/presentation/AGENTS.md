# src/presentation

## OVERVIEW
PyQt6 UI layer - MainWindow, widgets, dialogs, system managers, event handlers

## STRUCTURE
```
src/presentation/
├── ui/              # MainWindow + event_handlers (central orchestration)
├── widgets/         # TodoItem, Section, Header, Footer, RichText, SubTask, Splitter, mixins/draggable
├── dialogs/         # Edit, BackupManager, DatePicker, SubTaskList, UpdateAvailable, UpdateProgress
├── system/          # WindowManager, TrayManager, SingleInstance (port 65432), UpdateManager
├── workers/         # UpdateCheckWorker, UpdateDownloadWorker (threaded)
└── utils/           # color_utils, link_parser
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| UI 레이아웃 구성 | `ui/main_window.py` | Header, sections, splitter composition |
| 시그널/슬롯 연결 | `ui/event_handlers/main_window_event_handler.py` | Central event orchestration |
| TODO 위젯 스타일 | `widgets/todo_item_widget.py` | QSS styling, hover effects, opacity |
| 드래그앤드롭 구현 | `widgets/mixins/draggable_mixin.py` | Reusable mixin, requires get_drag_data() |
| 섹션 스크롤 관리 | `widgets/section_widget.py` | QScrollArea, drop position calculation |
| 다이얼로그 복잡한 UI | `dialogs/edit_dialog.py` | Calendar, subtasks, recurrence settings |
| 윈도우 상태 저장 | `system/window_manager.py` | Geometry, always-on-top, screen validation |
| 시스템 트레이 | `system/tray_manager.py` | Minimize to tray, menu actions |
| 자동 업데이트 | `system/update_manager.py` | GitHub Releases API, worker threads |
| UI 색상/메트릭 | `config.py` | COLORS, UI_METRICS, LAYOUT_MARGINS |

## CONVENTIONS

### PyQt6 시그널/슬롯 패턴
- **위젯 → Section → EventHandler** 시그널 전파 체인
- `pyqtSignal(str, bool)` 정의 → `.connect(handler)` 연결
- 시그널 네이밍: `*_requested`, `*_toggled`, `*_changed`

### 이벤트 위임 패턴
- **MainWindow**: UI 구성만, 이벤트는 **EventHandler** 위임
- **MainWindowEventHandler**: `connect_signals()`, `load_todos()`, `on_*` 핸들러

### Mixin 패턴 (다중 상속)
- `DraggableMixin`: 드래그앤드롭 재사용
- 추상 메서드: `get_drag_data()`, `get_widget_styles()`
- **Cooperative Multiple Inheritance**: `hasattr(super(), 'method')` 체크 후 호출

### 다이얼로그 재사용 패턴
- 싱글톤 인스턴스 재사용 (EventHandler에 저장)
- `if not self.edit_dialog:` → 생성 → `set_todo(...)` → 재사용

### QSS 스타일링
- `setStyleSheet(f"...{config.COLORS['accent']}...")` 인라인 스타일
- `config.py`에서 색상/메트릭 중앙 관리

### Opacity 효과
- `QGraphicsOpacityEffect()`로 호버/완료 상태 표현
- 삭제 버튼: 호버 시 나타남 (hidden → visible)
- 완료된 TODO: 모든 요소에 opacity 적용

### Throttled 저장
- `DebounceManager(delay_ms=100)`로 Splitter 이동 저장 최적화
- `splitterMoved` → `is_active()` 체크 → `schedule()`

### 시그널 블로킹
- `widget.blockSignals(True)` → UI 업데이트 → `blockSignals(False)`
- 핸들러 호출 방지용

## ANTI-PATTERNS (PRESENTATION LAYER)
- ❌ MainWindow에 이벤트 처리 로직 직접 작성 → EventHandler 위임 필수
- ❌ 위젯 간 직접 참조 → 시그널/슬롯 사용
- ❌ Mixin에서 `super()` 무조건 호출 → `hasattr` 체크 필수
- ❌ 다이얼로그 매번 생성 → 인스턴스 재사용
- ❌ 하드코딩된 색상 → `config.py` 사용
- ❌ 드래그 핸들 누락 → DraggableMixin + `drag_handle` 속성 필수
