# Simple ToDo

> 화면의 1/4 크기로 실행되는 심플하고 우아한 할일 관리 데스크톱 애플리케이션

![Version](https://img.shields.io/badge/version-1.0-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![Python](https://img.shields.io/badge/python-3.7+-green)
![License](https://img.shields.io/badge/license-MIT-yellow)
[![Download](https://img.shields.io/github/v/release/gyh214/simple-todo?label=Download&color=success)](https://github.com/gyh214/simple-todo/releases/latest)

---

## 📋 목차

- [소개](#-소개)
- [주요 기능](#-주요-기능)
- [설치 방법](#-설치-방법)
- [사용 방법](#-사용-방법)
- [개발 가이드](#-개발-가이드)
- [기술 스택](#-기술-스택)
- [프로젝트 구조](#-프로젝트-구조)
- [라이선스](#-라이선스)

---

## 🎯 소개

**Simple ToDo**는 Windows 데스크톱 환경에서 작동하는 미니멀한 할일 관리 애플리케이션입니다.
화면의 1/4 크기(420x600)로 실행되어 작업 중에도 부담 없이 할일을 관리할 수 있습니다.

### 특징
- 🎨 **다크 모드 테마**: 눈의 피로를 줄이는 세련된 다크 UI
- 📌 **항상 위**: 작업 중에도 항상 화면에 표시 가능
- 🔄 **드래그 앤 드롭**: 직관적인 순서 변경
- 📅 **납기일 관리**: 시각적 구분으로 우선순위 파악
- 🔗 **링크/경로 인식**: URL과 파일 경로 자동 감지 및 실행
- 💾 **자동 백업**: 모든 변경사항 즉시 저장 및 백업
- 🖥️ **시스템 트레이**: 최소화 시 트레이로 이동

---

## ✨ 주요 기능

### 1. TODO 관리
- **생성**: Enter 키 또는 추가 버튼으로 간편하게 생성
- **수정**: 더블클릭으로 편집 다이얼로그 열기
- **삭제**: 호버 시 나타나는 ✕ 버튼 (확인 다이얼로그 표시)
- **완료 처리**: 체크박스로 진행중 ⟷ 완료 섹션 이동

### 2. 정렬 및 순서
- **정렬**: 납기일 빠른순/늦은순 드롭다운
- **드래그 앤 드롭**: ☰ 핸들로 순서 변경 (섹션 내부만 가능)

### 3. 섹션 관리
- **진행중/완료 섹션**: 독립적 스크롤 영역
- **분할바**: 드래그로 섹션 비율 조정 (최소 10% 제한)
- **비율 저장**: 재시작 시 유지

### 4. 납기일
- **설정**: 편집 다이얼로그에서 캘린더 UI로 선택
- **표시**: "X일 남음", "오늘", "X일 지남"
- **시각적 구분**:
  - 만료 (지난 날짜): 빨간색 배경
  - 오늘: 주황색 배경
  - 임박 (3일 이내): 연한 주황색 배경

### 5. 링크 및 경로 인식
- **웹 링크**: `http://`, `https://`, `www.`로 시작하는 URL 자동 감지
- **파일 경로**: `C:\`, `D:\`, `\\server\` 등 자동 감지
- **클릭 동작**: 브라우저/탐색기/연결 프로그램으로 열기

### 6. 시스템 통합
- **시스템 트레이**: 최소화 시 트레이로 이동
- **단일 인스턴스**: 중복 실행 방지 (포트 65432 기반)
- **항상 위**: 토글 기능으로 다른 창 위에 고정

---

## 🚀 설치 방법

### 실행 파일 사용 (권장)

1. [Releases](../../releases) 페이지에서 최신 버전의 `SimpleTodo.exe` 다운로드
2. 원하는 위치에 저장
3. `SimpleTodo.exe` 실행

### 소스 코드에서 실행

#### 1. 저장소 클론
```bash
git clone https://github.com/your-username/new-todo-panel.git
cd new-todo-panel
```

#### 2. 가상환경 생성 및 활성화
```bash
python -m venv venv
venv\Scripts\activate
```

#### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

#### 4. 실행
```bash
python main.py
```

---

## 📖 사용 방법

### 기본 사용법

1. **TODO 추가**: 상단 입력창에 할일을 입력하고 Enter 키 또는 추가 버튼 클릭
2. **완료 처리**: TODO 왼쪽의 체크박스 클릭
3. **수정**: TODO를 더블클릭하여 편집 다이얼로그 열기
4. **삭제**: TODO에 마우스를 올려 나타나는 ✕ 버튼 클릭
5. **순서 변경**: ☰ 핸들을 드래그하여 위아래로 이동

### 납기일 설정

1. TODO 더블클릭 → 편집 다이얼로그 열기
2. 캘린더에서 날짜 선택
3. "완료" 버튼 클릭

### 정렬 변경

- 상단 드롭다운에서 "납기일 빠른순" 또는 "납기일 늦은순" 선택

### 섹션 비율 조정

- 진행중/완료 섹션 사이의 분할바를 드래그하여 비율 조정

### 키보드 단축키

- **Enter**: 입력창에서 TODO 추가
- **Esc**: 다이얼로그 닫기
- **Ctrl+N**: 새 TODO 추가 (입력창 포커스)
- **Delete**: 선택된 TODO 삭제
- **F2**: 선택된 TODO 편집

---

## 🛠️ 개발 가이드

### 개발 환경 설정

#### 필수 요구사항
- Python 3.7 이상
- Windows 10 이상

#### 개발 모드 실행
```bash
# 가상환경 활성화
venv\Scripts\activate

# 개발 모드 실행
python main.py

# 디버그 모드 실행 (상세 로그)
python debug_main.py
```

### 빌드

#### 실행 파일 빌드
```bash
# 기본 빌드
python build.py

# 디버그 빌드 (상세 출력)
python build.py --debug

# 빌드 + 임시 파일 유지 (디버깅용)
python build.py --keep-temp
```

빌드 결과물은 `dist/SimpleTodo.exe`에 생성됩니다.

### 프로젝트 구조

```
new-todo-panel/
├── src/                    # 소스 코드 (CLEAN Architecture)
│   ├── domain/            # 도메인 레이어
│   ├── application/       # 애플리케이션 레이어
│   ├── infrastructure/    # 인프라 레이어
│   ├── presentation/      # 프레젠테이션 레이어
│   └── core/              # DI Container
├── docs/                   # 문서
├── main.py                 # 애플리케이션 진입점
├── config.py               # 전역 설정
├── build.py                # 빌드 스크립트
└── requirements.txt        # Python 패키지 의존성
```

자세한 아키텍처 및 개발 가이드는 [CLAUDE.md](CLAUDE.md)를 참고하세요.

---

## 🔧 기술 스택

- **언어**: Python 3.7+
- **GUI 프레임워크**: PyQt6
- **아키텍처**: CLEAN Architecture
- **빌드 도구**: PyInstaller
- **의존성 관리**: pip, requirements.txt

### 주요 라이브러리
- **PyQt6**: GUI 프레임워크
- **python-dateutil**: 날짜 처리 유틸리티
- **PyInstaller**: 실행 파일 빌드
- **psutil**: 시스템 유틸리티

---

## 📂 프로젝트 구조

### CLEAN Architecture 레이어

```
┌─────────────────────────────────────┐
│      Presentation Layer              │  UI, Event Handlers, Managers
│  - MainWindow, Widgets, Dialogs     │
│  - TrayManager, WindowManager       │
│  - SingleInstanceManager            │
├─────────────────────────────────────┤
│      Application Layer               │  Use Cases, Services
│  - TodoService                      │
│  - SortTodos, ReorderTodo           │
│  - DataPreservationService          │
├─────────────────────────────────────┤
│      Domain Layer                    │  Entities, Value Objects
│  - Todo Entity                      │
│  - TodoId, Content, DueDate         │
│  - TodoSortService                  │
├─────────────────────────────────────┤
│      Infrastructure Layer            │  External Dependencies
│  - TodoRepositoryImpl               │
│  - MigrationService                 │
│  - DebounceManager                  │
└─────────────────────────────────────┘
```

### 데이터 저장

- **위치**: `TodoPanel_Data/data.json`
- **백업**: `TodoPanel_Data/backups/` (최근 10개 유지)
- **형식**: JSON
- **자동 저장**: 모든 변경사항 즉시 저장
- **레거시 마이그레이션**: 구형 포맷 자동 변환

---

## 🎨 색상 테마

Simple ToDo는 다크 모드를 기본으로 사용합니다.

```css
Primary Background:   #1A1A1A
Secondary Background: #2A2A2A
Card/Surface:         #2D2D2D
Text Primary:         rgba(255, 255, 255, 0.92)
Text Secondary:       #B0B0B0
Accent Color:         #CC785C (Claude 주황색)
Border/Divider:       rgba(64, 64, 64, 0.3)
```

---

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참고하세요.

---

## 🤝 기여

버그 리포트, 기능 제안, Pull Request는 언제나 환영합니다!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📧 문의

프로젝트에 대한 문의사항이 있으시면 이슈를 등록해주세요.

---

## 📌 참고 문서

- [CLAUDE.md](CLAUDE.md) - 개발자를 위한 상세 가이드
- [기능 명세서](docs/초기기획/초기_Simple_ToDo_기능_명세서.md) - 전체 기능 상세 설명
- [UI 프로토타입](docs/초기기획/초기_todo-app-ui.html) - 실제 레이아웃/색상 참고

---

<p align="center">Made with ❤️ for productivity</p>
