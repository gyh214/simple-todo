# Simple ToDo - 기능 명세서

## 1. 프로젝트 개요

### 1.1 목적
- 화면의 1/4 크기로 실행되는 심플한 할일 관리 데스크톱 애플리케이션
- 최소한의 기능으로 직관적이고 빠른 할일 관리 제공

### 1.2 타겟 플랫폼
- Windows 데스크톱 애플리케이션
- 해상도: 최소 300x400, 권장 420x600
- 항상 위 옵션 지원

---

## 2. UI 구조

### 2.1 전체 레이아웃
```
┌─────────────────────────────────────┐
│ Header (고정)                        │
│  - 타이틀 + 정렬 드롭다운            │
│  - 입력창 + 추가 버튼                │
├─────────────────────────────────────┤
│ Content (스크롤 가능)                │
│  ┌───────────────────────────────┐  │
│  │ 진행중 섹션 (가변 크기)        │  │
│  │  - 할일 아이템 리스트          │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │ 분할바 (드래그 가능)           │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │ 완료 섹션 (가변 크기)          │  │
│  │  - 완료된 아이템 리스트        │  │
│  └───────────────────────────────┘  │
├─────────────────────────────────────┤
│ Footer (고정)                        │
│  - 상태 정보 (진행중/완료/전체)     │
└─────────────────────────────────────┘
```

### 2.2 색상 테마 (Dark Mode)
- Primary Background: #1A1A1A
- Secondary Background: #2A2A2A
- Card/Surface: #2D2D2D
- Text Primary: rgba(255, 255, 255, 0.92)
- Text Secondary: #B0B0B0
- Text Disabled: #6B6B6B
- Accent Color: #CC785C (Claude 주황색)
- Accent Hover: #E08B6F
- Border/Divider: rgba(64, 64, 64, 0.3)

---

## 3. 핵심 기능 명세

### 3.1 TODO 생성
- 입력창에 텍스트 입력
- Enter 키 또는 "추가" 버튼 클릭으로 생성
- 새 항목은 "진행중" 섹션에 추가
- 생성 시 자동으로 생성일 타임스탬프 기록
- 빈 텍스트는 추가 불가

**데이터 필드:**
```json
{
  "id": "unique_id",
  "content": "할일 내용",
  "completed": false,
  "createdAt": "2025-01-03T10:30:00Z",
  "dueDate": "2025-01-10T00:00:00Z" (optional),
  "order": 0
}
```

### 3.2 TODO 수정
- 더블클릭으로 편집 모드 진입
- 편집 다이얼로그 표시:
  - 텍스트 수정 가능
  - 납기일 추가/수정/제거 가능
  - 취소/저장 버튼
- 모든 메타데이터(생성일, 순서 등) 자동 보존

### 3.3 TODO 삭제
- 항목 호버 시 ✕ 버튼 표시
- 클릭 시 삭제 확인 다이얼로그
- 확인 후 즉시 삭제 및 데이터 저장

### 3.4 TODO 완료 처리
- 체크박스 클릭으로 완료/미완료 토글
- 진행중 항목 체크 → 완료 섹션으로 자동 이동
- 완료 항목 체크 해제 → 진행중 섹션으로 복귀
- 이동 시 completed 필드 업데이트
- 섹션 카운트 자동 갱신

### 3.5 TODO 순서 변경 (드래그 앤 드롭)
- 각 항목 좌측의 ☰ 핸들을 드래그
- 같은 섹션 내에서만 순서 변경 가능
- 드롭 시 order 필드 재계산 및 저장
- 진행중/완료 섹션 각각 독립적인 순서 관리

### 3.6 정렬 기능
- 드롭다운 위치: 헤더 우측 (Simple ToDo 옆)
- 정렬 옵션 2가지:
  1. "정렬: 납기일 빠른순" (기본값)
  2. "정렬: 납기일 늦은순"
- 정렬 변경 시 즉시 UI 업데이트
- 정렬 상태 로컬 저장 (재시작 시 유지)
- 납기일 없는 항목은 맨 뒤로 배치

---

## 4. 섹션 관리

### 4.1 진행중/완료 섹션
- 독립적인 스크롤 영역
- 각 섹션 헤더에 항목 개수 표시
- 최소 높이: 100px (완전 축소 방지)

### 4.2 분할바 (Resizable Divider)
- 진행중/완료 섹션 사이에 위치
- 마우스 커서: ns-resize
- 드래그로 섹션 비율 조정
- 최소 비율: 10% (각 섹션)
- 호버/드래그 시 #CC785C 색상 강조
- 분할 비율 로컬 저장 (재시작 시 유지)

**구현 방식:**
- Flexbox 기반 레이아웃
- mousedown, mousemove, mouseup 이벤트 처리
- flex 속성 동적 조정

---

## 5. 납기일 관리

### 5.1 날짜 선택 다이얼로그
- TODO 더블클릭 → 편집 다이얼로그 내에서 날짜 설정
- 캘린더 UI 제공
- 월 이동 버튼 (< >)
- 오늘 날짜 강조 표시
- 선택 날짜 강조 표시
- 과거 날짜 선택 가능

### 5.2 날짜 표시
- 납기일이 있는 항목에만 표시
- 표시 형식: "X일 남음", "오늘", "X일 지남"
- 상태별 시각적 구분:
  - **만료** (지난 날짜): rgba(204, 120, 92, 0.2) 배경, opacity 0.7
  - **오늘** (당일): rgba(204, 120, 92, 0.2) 배경
  - **임박** (3일 이내): rgba(204, 120, 92, 0.15) 배경, opacity 0.8
  - **일반** (여유): rgba(64, 64, 64, 0.3) 배경

### 5.3 날짜 계산 로직
```python
def calculate_due_status(due_date, current_date):
    days_diff = (due_date - current_date).days
    
    if days_diff < 0:
        return {
            "status": "overdue",
            "text": f"{abs(days_diff)}일 지남"
        }
    elif days_diff == 0:
        return {
            "status": "today",
            "text": "오늘"
        }
    elif days_diff <= 3:
        return {
            "status": "upcoming",
            "text": f"{days_diff}일 남음"
        }
    else:
        return {
            "status": "normal",
            "text": f"{days_diff}일 남음"
        }
```

---

## 6. 링크 및 경로 인식

### 6.1 웹 링크 자동 감지
- 패턴: `http://`, `https://`, `www.`로 시작하는 URL
- 시각적 표시: #CC785C 색상, 밑줄
- 클릭 동작: 기본 브라우저에서 열기
- 호버 툴팁: "웹사이트 열기"

**정규식 예시:**
```regex
(https?://[^\s]+)|(www\.[^\s]+)
```

### 6.2 파일 경로 자동 감지
- 절대 경로: `C:\Users\...`, `D:\...`
- 상대 경로: `..\folder\file.txt`
- 네트워크 경로: `\\server\share\...`
- 시각적 표시: #CC785C 색상, 밑줄, opacity 0.8
- 클릭 동작: 
  - 파일 존재 확인
  - 실행 파일(.exe, .bat 등)은 경고 다이얼로그
  - 폴더는 탐색기 열기
  - 일반 파일은 연결된 프로그램으로 열기

**정규식 예시:**
```regex
([A-Za-z]:\\[\\\w\s\-\.]+)|(\\\\[\w\-\.]+\\[\\\w\s\-\.]+)
```

---

## 7. 데이터 관리

### 7.1 저장 위치
- 실행 파일 기준: `./TodoPanel_Data/data.json`
- 개발 모드: 프로젝트 루트의 `TodoPanel_Data/data.json`
- 디렉토리 자동 생성

### 7.2 저장 방식
- 자동 저장: 모든 변경사항 즉시 저장
- 비동기 배치 저장: UI 블로킹 없음
- 원자적 저장: 임시 파일 → 원본 파일 교체
- JSON 형식, UTF-8 인코딩

**데이터 구조:**
```json
{
  "version": "1.0",
  "settings": {
    "sortOrder": "dueDate_asc",
    "splitRatio": [1, 1],
    "alwaysOnTop": false
  },
  "todos": [
    {
      "id": "uuid-1",
      "content": "프로젝트 기획서 작성하기",
      "completed": false,
      "createdAt": "2025-01-01T10:00:00Z",
      "dueDate": "2025-01-05T00:00:00Z",
      "order": 0
    }
  ]
}
```

### 7.3 백업 시스템
- 저장 시마다 백업 생성
- 파일명 형식: `data_YYYYMMDD_HHMMSS.json`
- 최근 10개 백업 유지
- 데이터 손상 시 자동 복구

### 7.4 레거시 데이터 마이그레이션

기존 data.json (구형 포맷)을 자동으로 새 형식으로 변환합니다.

#### 레거시 형식 감지

파일 로드 시 다음 조건으로 레거시 형식을 감지:
- 최상위가 배열 형식인 경우
- `version` 필드가 없는 경우

```python
def detect_legacy_format(data):
    if isinstance(data, list):
        return True
    if isinstance(data, dict) and "version" not in data:
        return True
    return False
```

#### 필드 변환 규칙

| 레거시 필드 | 새 필드 | 비고 |
|------------|---------|------|
| `text` | `content` | 필수 변환 |
| `created_at` | `createdAt` | 필수 변환 |
| `due_date` | `dueDate` | 선택적 (null 허용) |
| `position` | `order` | 필수 변환 |
| `modified_at` | (삭제) | 신규 버전에서는 미사용 |

#### 자동 마이그레이션 프로세스

**입력 (레거시 형식):**
```json
[
  {
    "id": "abc-123",
    "text": "할일 내용",
    "completed": false,
    "created_at": "2025-09-21T20:26:04.532355",
    "due_date": "2025-09-25",
    "position": 0,
    "modified_at": "2025-09-21T20:30:00.000000"
  }
]
```

**출력 (새 형식):**
```json
{
  "version": "1.0",
  "settings": {
    "sortOrder": "dueDate_asc",
    "splitRatio": [1, 1],
    "alwaysOnTop": false
  },
  "todos": [
    {
      "id": "abc-123",
      "content": "할일 내용",
      "completed": false,
      "createdAt": "2025-09-21T20:26:04.532355",
      "dueDate": "2025-09-25",
      "order": 0
    }
  ]
}
```

#### 변환 로직 구현

```python
def migrate_legacy_data(legacy_data):
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
            "sortOrder": "dueDate_asc",
            "splitRatio": [1, 1],
            "alwaysOnTop": False
        },
        "todos": migrated_todos
    }
```

#### 실행 시점 및 백업

- **실행 시점**: 앱 시작 시 data.json 로드 직후
- **백업 생성**: 변환 전 원본을 `TodoPanel_Data/backups/data_legacy_backup_YYYYMMDD_HHMMSS.json`으로 저장
- **변환 후 저장**: 변환된 데이터를 data.json에 덮어쓰기

#### 기본값 설정

누락된 필드는 다음 기본값 적용:

**Settings 기본값:**
- `sortOrder`: `"dueDate_asc"` (납기일 빠른순)
- `splitRatio`: `[1, 1]` (진행중:완료 = 1:1)
- `alwaysOnTop`: `false` (항상 위 비활성화)

**TODO 필드 기본값:**
- `content`: 빈 문자열
- `completed`: `false`
- `createdAt`: 현재 시각
- `order`: `0`

#### 에러 처리

- **변환 실패**: 원본 보존, 에러 로그 기록, 사용자에게 알림
- **필수 필드 누락**: 기본값으로 채우되 경고 로그
- **잘못된 데이터 타입**: 타입 변환 시도, 실패 시 해당 항목 건너뛰기
- **파일 시스템 오류**: 백업 실패 시 변환 중단

---

## 8. 시스템 통합

### 8.1 시스템 트레이
- 최소화 시 트레이로 이동
- 트레이 아이콘: 파란색 체크마크
- 좌클릭: 창 표시/숨김 토글
- 우클릭 메뉴:
  - "TODO Panel 표시"
  - "TODO Panel 숨기기"
  - 구분선
  - "종료"

### 8.2 단일 인스턴스
- 중복 실행 방지
- 포트 기반 락: 65432
- 이미 실행 중이면 기존 창 활성화

### 8.3 윈도우 관리
- 크기 조절 가능
- 최소 크기: 300x400
- 최대 크기: 제한 없음
- 초기 위치: 화면 중앙
- "항상 위" 토글 기능

---

## 9. 사용자 인터랙션

### 9.1 키보드 단축키
- **Enter**: 입력창에서 TODO 추가
- **Esc**: 다이얼로그 닫기
- **Ctrl+N**: 새 TODO 추가 (입력창 포커스)
- **Delete**: 선택된 TODO 삭제 (선택 시)
- **F2**: 선택된 TODO 편집 (선택 시)

### 9.2 마우스 인터랙션
- **클릭**: 체크박스 토글
- **더블클릭**: 편집 다이얼로그 열기
- **드래그 (☰)**: 순서 변경
- **호버**: 삭제 버튼 표시

### 9.3 애니메이션
- 체크박스 체크/해제: 0.2s transition
- 항목 이동: 부드러운 애니메이션
- 호버 효과: 0.2s ease
- 버튼 클릭: transform scale

---

## 10. 에러 처리

### 10.1 데이터 저장 실패
- 최대 3회 재시도
- 실패 시 사용자에게 알림
- 임시 메모리에 데이터 유지
- 로그 파일에 에러 기록

### 10.2 파일 시스템 에러
- 권한 부족: 관리자 권한 요청 안내
- 디스크 공간 부족: 경고 메시지
- 경로 오류: 백업 위치로 전환

### 10.3 링크/경로 에러
- 존재하지 않는 URL: 브라우저에서 처리
- 존재하지 않는 파일: "파일을 찾을 수 없습니다" 메시지
- 실행 권한 없음: "권한이 없습니다" 메시지

---

## 11. 성능 요구사항

### 11.1 응답성
- UI 업데이트 지연: 50ms 이내
- 저장 작업: 비동기 처리
- 최대 TODO 개수: 1000개 이상 지원
- 스크롤 성능: 60fps 유지

### 11.2 메모리 사용
- 초기 실행: 50MB 이하
- 1000개 TODO: 100MB 이하
- 메모리 누수 없음

### 11.3 파일 크기
- 실행 파일: 20MB 이하
- 데이터 파일: TODO당 1KB 이하

---

## 12. 아키텍처 권장사항

### 12.1 CLEAN Architecture
```
┌─────────────────────────────────────┐
│         Presentation Layer           │
│  (UI, Event Handlers, Managers)      │
├─────────────────────────────────────┤
│        Application Layer             │
│    (TodoService, Use Cases)          │
├─────────────────────────────────────┤
│          Domain Layer                │
│    (Todo Entity, Value Objects)      │
├─────────────────────────────────────┤
│      Infrastructure Layer            │
│  (Repository, File System, System)   │
└─────────────────────────────────────┘
```

### 12.2 핵심 컴포넌트
- **TodoService**: 비즈니스 로직 처리
- **TodoRepository**: 데이터 영속성
- **UIManager**: UI 구성 및 업데이트
- **EventHandler**: 사용자 입력 처리
- **DataPreservationService**: 데이터 무결성 보장

### 12.3 의존성 주입
- DI Container 사용
- 인터페이스 기반 설계
- 테스트 가능한 구조

---

## 13. 테스트 요구사항

### 13.1 단위 테스트
- 각 비즈니스 로직 함수
- 데이터 변환 로직
- 날짜 계산 로직
- URL/경로 감지 정규식

### 13.2 통합 테스트
- 파일 저장/로드
- 섹션 간 이동
- 정렬 기능
- 백업/복구

### 13.3 UI 테스트
- 드래그 앤 드롭
- 분할바 리사이징
- 다이얼로그 표시/숨김
- 체크박스 상태 변경

---

## 14. 배포 요구사항

### 14.1 패키징
- 단일 실행 파일 (exe)
- 디지털 서명 (선택사항)
- 설치 프로그램 (선택사항)

### 14.2 실행 환경
- Windows 10 이상
- .NET Framework 또는 Python 런타임 포함
- 관리자 권한 불필요

### 14.3 업데이트
- 버전 체크 기능 (선택사항)
- 자동 업데이트 (선택사항)

---

## 15. 향후 확장 가능성

### 15.1 기능 확장
- 태그/카테고리 시스템
- 검색 기능
- 필터링
- 반복 TODO
- 첨부파일 지원

### 15.2 동기화
- 클라우드 백업
- 멀티 디바이스 동기화

### 15.3 통합
- 캘린더 연동
- 이메일 연동
- 슬랙/디스코드 알림

---

## 16. UI 프로토타입 참고

**프로토타입 파일:** `todo-app-ui.html`

- 실제 구현 시 프로토타입의 레이아웃, 색상, 간격을 정확히 따를 것
- 모든 인터랙션 동작은 프로토타입과 동일하게 구현
- 애니메이션 타이밍과 이징도 프로토타입 기준

---

## 요약

Simple ToDo는 최소한의 기능으로 빠르고 직관적인 할일 관리를 제공하는 데스크톱 애플리케이션입니다. 

**핵심 기능:**
- TODO 생성/수정/삭제/완료 처리
- 드래그 앤 드롭 순서 변경
- 납기일 빠른순/늦은순 정렬
- 진행중/완료 섹션 분할 및 비율 조정
- 웹 링크 및 파일 경로 자동 인식
- 자동 저장 및 백업 시스템

**기술 요구사항:**
- CLEAN Architecture 기반 설계
- 비동기 데이터 저장
- 시스템 트레이 통합
- 단일 인스턴스 실행
- 60fps UI 성능

**제공 자료:**
- UI 프로토타입 (HTML)
- 기능 명세서 (본 문서)
- 색상 테마 정의
- 데이터 스키마