# Simple ToDo - LLM Context

PyQt6 기반 CLEAN Architecture TODO 앱 (Windows, 420x600px)

## 🚨 파일 경로 규칙
**상대 경로 + Forward slash(/)만 사용. 절대 경로/백슬래시(\) 금지**
- ✅ `src/domain/entities/todo.py`
- ❌ `src\domain\...`, `D:\dev_proj\...`

## 기술 스택 & 실행
- Python 3.7+ / PyQt6 / CLEAN Architecture
- 실행: `python main.py` | 빌드: `python build.py`
- 의존성: PyQt6, python-dateutil, PyInstaller, psutil

## 프로젝트 구조
```
src/
├── domain/          # Entity, Value Objects, Services
│   ├── entities/todo.py              # Todo 엔티티 (id, content, completed, createdAt, dueDate, order)
│   └── services/
│       ├── todo_sort_service.py      # 정렬 로직 (납기일, order)
│       ├── link_detection_service.py # URL/경로 감지
│       └── todo_search_service.py    # TODO 검색 기능
├── application/     # Use Cases, TodoService, DataPreservation
│   ├── services/
│   │   ├── todo_service.py                  # CRUD 비즈니스 로직
│   │   └── data_preservation_service.py     # 데이터 필드 자동 보존
│   └── use_cases/
│       ├── sort_todos.py             # 정렬 유스케이스
│       ├── reorder_todo.py           # 드래그앤드롭 재정렬
│       └── change_sort_order.py      # 정렬 순서 변경
├── infrastructure/  # Repository 구현, Migration, Debounce
│   ├── repositories/todo_repository_impl.py # JSON 저장/로드/백업
│   ├── file_system/migration_service.py     # 레거시 마이그레이션
│   └── utils/debounce_manager.py            # 저장 디바운싱
├── presentation/    # UI, Widgets, Dialogs, System Managers
│   ├── ui/
│   │   ├── main_window.py            # 메인 윈도우
│   │   └── event_handlers/           # 이벤트 핸들러
│   ├── widgets/
│   │   ├── custom_splitter.py        # 드래그 분할바
│   │   ├── custom_splitter_handle.py # 분할바 핸들
│   │   ├── section_widget.py         # 섹션 (진행중/완료)
│   │   ├── header_widget.py          # 헤더 (제목, 정렬)
│   │   ├── footer_widget.py          # 푸터
│   │   ├── todo_item_widget.py       # TODO 아이템 위젯
│   │   ├── rich_text_widget.py       # 리치 텍스트 위젯
│   │   └── mixins/                   # 믹스인 (드래그 등)
│   ├── dialogs/edit_dialog.py        # TODO 편집 다이얼로그
│   ├── utils/link_parser.py          # 링크 파싱 유틸
│   └── system/
│       ├── tray_manager.py           # 시스템 트레이
│       ├── window_manager.py         # 윈도우 관리
│       └── single_instance.py        # 단일 인스턴스 (포트 65432)
└── core/container.py # DI Container

config.py                           # 전역 설정 (색상, UI 메트릭, 경로)
main.py                             # 진입점 (DI 초기화)
TodoPanel_Data/data.json            # TODO 데이터 + 설정 (자동 저장/백업)
docs/초기기획/초기_todo-app-ui.html # 초기 UI 프로토타입 (참고용, 현재는 변경되었을 수 있음)
```

## 색상 테마 (Dark Mode)
**`config.py` 색상 테마 (초기 프로토타입 기반, 현재는 확장됨)**:
```css
Body BG: #0D0D0D | Primary BG: #1A1A1A | Secondary BG: #2A2A2A
Card: #2D2D2D | Card Hover: #353535
Text: rgba(255,255,255,0.92) | Secondary: #B0B0B0 | Disabled: #6B6B6B
Accent: #CC785C | Hover: #E08B6F
Border: rgba(64,64,64,0.3) | Border Strong: rgba(64,64,64,0.5)
```

## 데이터 구조 (data.json)
```json
{
  "version": "1.0",
  "settings": {
    "sortOrder": "dueDate_asc",  // "dueDate_asc" | "dueDate_desc" | "today_first" | "manual"
    "splitRatio": [9, 1],         // [진행중, 완료] 비율 (기본: 진행중 최대화)
    "alwaysOnTop": false
  },
  "todos": [
    {
      "id": "uuid",
      "content": "할일",
      "completed": false,
      "createdAt": "2025-01-01T10:00:00Z",
      "dueDate": "2025-01-05T00:00:00Z",  // optional
      "order": 0
    }
  ]
}
```

**데이터 관리**: 자동 저장, 비동기 배치, 원자적 저장 (임시파일→원본 교체), 백업 10개 유지

### 레거시 마이그레이션
| 레거시 필드 | 신규 필드 | | 레거시 필드 | 신규 필드 |
|---|---|---|---|---|
| `text` | `content` | | `position` | `order` |
| `created_at` | `createdAt` | | `modified_at` | (삭제) |
| `due_date` | `dueDate` | | | |

**감지**: 배열 또는 `version` 없음 → 앱 시작 시 자동 변환 + 백업

## 아키텍처 (CLEAN)
```
Presentation → Application → Domain ← Infrastructure
   (UI)         (UseCase)    (Entity)   (Repository)
```
**의존성 역전**: Infrastructure가 Domain 인터페이스 구현
**DI Container**: `src/core/container.py` 에서 모든 의존성 주입

## 핵심 기능 요약
1. **TODO**: 생성(Enter), 수정(더블클릭), 삭제(✕), 완료 체크
2. **정렬**: 납기일 빠른순/늦은순/오늘 우선, 수동 정렬(드래그앤드롭)
3. **섹션**: 진행중/완료, 드래그 분할바 (최소 10%), 비율 저장
4. **납기일**: 캘린더 선택, "X일 남음/지남/오늘" 표시, 시각적 구분 (만료/임박 배경색)
5. **링크**: `http://`, `https://`, `www.`, `C:\`, `D:\`, `\\server\` 자동 감지/클릭 열기
6. **시스템**: 트레이 아이콘, 단일 인스턴스 (포트 65432), 항상 위, 최소 크기 300x400

## 개발 가이드라인
1. **색상/레이아웃**: `config.py` 사용 (초기 프로토타입 기반, 확장됨)
2. **데이터 무결성**: 모든 필드(createdAt, order) 자동 보존
3. **에러 처리**: 저장 실패 최대 3회 재시도, 로그 기록
4. **비동기**: 파일 I/O 비동기, UI 블로킹 방지
5. **CLEAN 준수**: 레이어 간 의존성 규칙, DI Container 사용
6. **Windows 특이사항**: UTF-8 인코딩 (`open(..., encoding='utf-8')`), 가상환경, PyInstaller 빌드

## 참고 문서
- `docs/초기기획/초기_Simple_ToDo_기능_명세서.md` - 초기 기능 명세 (참고용)
- `docs/초기기획/초기_todo-app-ui.html` - 초기 UI 프로토타입 (참고용)
