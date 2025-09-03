# Windows TODO Panel

🚀 **Magic UI 스타일링과 스마트 링크 시스템을 갖춘 차세대 Windows TODO 관리 애플리케이션**

시스템 트레이 통합, 폴더/파일 경로 인식, 보안 검증 기능을 제공하는 모던하고 컴팩트한 데스크탑 TODO 관리 솔루션입니다.

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com)
[![Size](https://img.shields.io/badge/size-26.6MB-orange.svg)](https://github.com)

## ✨ 핵심 기능

### 🎨 **Magic UI 스타일링**
- **다크 테마 기반** 모던한 UI/UX 디자인
- **단일 라인 표시**: 모든 TODO가 한 줄로 최적화된 컴팩트 디자인
- **부드러운 애니메이션**: 호버 효과와 전환 애니메이션
- **사용자 친화적**: 직관적인 인터페이스와 시각적 피드백

### 🔗 **스마트 링크 시스템**
**다중 링크 타입 자동 인식 및 색상 구분**
- 🌐 **웹 링크** (파랑색): `https://example.com`, `www.example.com`
- 📄 **파일 경로** (주황색): `C:\Documents\file.txt`, `./config.json`
- 📁 **폴더 경로** (녹색): `C:\Program Files\`, `D:\Projects\`

**지원하는 경로 형식**
- **절대 경로**: `C:\Users\Username\Documents\`
- **상대 경로**: `./folder/`, `../parent/folder/`
- **네트워크 경로**: `\\server\share\folder\`
- **공백 포함 경로**: `C:\Program Files\Windows Defender\`

### 🛡️ **고급 보안 검증 시스템**
- **실행 파일 보안**: `.exe`, `.bat`, `.cmd` 등 위험한 파일 실행 전 사용자 승인 요구
- **시스템 폴더 보호**: 중요 시스템 디렉토리 접근 시 경고 및 승인 절차
- **네트워크 경로 검증**: 네트워크 연결 상태 확인 후 폴더 열기
- **안전한 기본값**: 보안 대화상자의 기본값을 "아니오"로 설정

### 💻 **시스템 통합**
- **시스템 트레이**: 창을 닫아도 백그라운드에서 지속 실행
- **단일 인스턴스**: 중복 실행 방지 (포트 65432 사용)
- **데이터 영구저장**: JSON 형식으로 사용자 데이터 안전 보관
- **자동 백업**: 데이터 손실 방지를 위한 자동 백업 시스템

## 📦 설치 및 실행

### 🚀 즉시 실행 (권장)
**완성된 실행파일 사용**
```bash
# dist 폴더에서 실행파일 실행
./dist/TodoPanel.exe  # 26.6MB, 모든 기능 포함
```

### 🔧 개발 모드 실행
```bash
# 의존성 설치
pip install -r requirements.txt

# 개발 모드로 실행
cd src
python main.py

# 디버그 모드로 실행
python main.py --debug
```

### 🏗️ 빌드하기
```bash
# PyInstaller spec 파일 사용 (권장)
pyinstaller --clean --noconfirm todo_panel.spec

# 빌드 스크립트 사용
python build.py                    # 표준 빌드
python build.py --debug            # 디버그 빌드
python build.py --no-upx           # UPX 압축 없이 빌드
python build.py --keep-temp        # 임시 파일 유지
```

## 📖 사용법

### 기본 사용법
1. **애플리케이션 시작**: `TodoPanel.exe` 실행 또는 시스템 트레이 아이콘 더블클릭
2. **할일 추가**: 상단 입력창에 내용 입력 후 Enter
3. **링크 활용**: URL, 파일 경로, 폴더 경로를 TODO에 포함
4. **트레이 관리**: 창을 닫아도 시스템 트레이에서 계속 실행

### 💡 링크 사용 예시

**웹 링크 (파랑색으로 표시)**
```
프로젝트 문서 확인 https://docs.example.com
참고 사이트 www.stackoverflow.com 검색
```

**파일 링크 (주황색으로 표시)**
```
회의록 검토 C:\Documents\meeting_notes.docx
설정 파일 수정 ./config/app.json
```

**폴더 링크 (녹색으로 표시)**
```
프로젝트 폴더 정리 D:\Projects\TodoPanel\
백업 확인 C:\Program Files\Backup Tool\
네트워크 자료 정리 \\server\shared\documents\
```

### 🔒 보안 기능

**실행 파일 보안 확인**
- 위험한 확장자(`.exe`, `.bat`, `.cmd` 등) 클릭 시 확인 대화상자 표시
- 기본값 "아니오"로 설정하여 실수 방지

**시스템 폴더 보호**
- 시스템 중요 폴더 접근 시 자동 경고
- 사용자 승인 후에만 폴더 열기 허용

## 🛠️ 기술 스택

### **핵심 기술**
- **Python 3.9+**: 안정적인 런타임 환경
- **Tkinter**: 네이티브 GUI 프레임워크
- **Magic UI**: 모던한 UI/UX 디자인 시스템
- **정규식 엔진**: 6가지 경로 패턴 인식 시스템

### **시스템 통합**
- **Pystray**: 시스템 트레이 통합
- **Pillow**: 동적 아이콘 생성
- **Psutil**: 시스템 리소스 모니터링
- **PyInstaller**: 단일 실행파일 패키징

### **데이터 관리**
- **AsyncTodoManager**: 비동기 배치 처리
- **JSON 스키마**: 구조화된 데이터 저장
- **자동 백업**: 데이터 무결성 보장

## 🏗️ 아키텍처 개요

### **다층 구조**
```
┌─────────────────────────────────────┐
│         Presentation Layer          │  UI Components, Magic UI
├─────────────────────────────────────┤
│         Business Logic Layer        │  Todo Management, Validation  
├─────────────────────────────────────┤
│         System Integration          │  Tray, File System, Security
└─────────────────────────────────────┘
```

### **핵심 컴포넌트**
- **`main.py`**: 시스템 트레이 통합 및 애플리케이션 진입점
- **`ui_components.py`**: Magic UI 스타일링 및 링크 처리 시스템
- **`todo_manager.py`**: 동기 데이터 관리
- **`async_todo_manager.py`**: 비동기 배치 처리
- **`tooltip.py`**: 커스텀 툴팁 시스템

### **링크 처리 파이프라인**
```
텍스트 입력 → 정규식 매칭 → 우선순위 결정 → 색상 태그 → 클릭 핸들러 → 보안 검증 → 실행
```

## 📊 성능 및 품질

### **빌드 정보**
- **파일 크기**: 26.6MB (최적화된 단일 실행파일)
- **메모리 사용량**: ~15MB (유휴 상태)
- **시작 시간**: < 2초
- **데이터 처리**: 비동기 배치 저장으로 응답성 보장

### **테스트 상태**
- ✅ **E2E 테스트**: 100% 통과
- ✅ **보안 테스트**: 완료
- ✅ **링크 처리**: 모든 경로 타입 검증 완료
- ✅ **시스템 호환성**: Windows 10/11 완전 지원

## 🚀 개발자 가이드

### **프로젝트 구조**
```
todo-panel/
├── src/                    # 소스 코드
│   ├── main.py            # 메인 애플리케이션
│   ├── ui_components.py   # UI 컴포넌트 및 Magic UI
│   ├── todo_manager.py    # 데이터 관리
│   └── async_todo_manager.py  # 비동기 처리
├── dist/                  # 빌드된 실행파일
├── build.py              # 빌드 스크립트
├── todo_panel.spec       # PyInstaller 설정
├── requirements.txt      # 의존성
└── README.md            # 이 문서
```

### **개발 환경 설정**
```bash
# 프로젝트 클론
git clone <repository-url>
cd todo-panel

# 가상환경 생성 및 활성화
python -m venv venv
venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt

# 개발 모드 실행
cd src && python main.py --debug
```

### **코딩 가이드라인**
- **정수 값 사용**: 모든 크기 관련 매개변수는 정수만 사용 (float 금지)
- **보안 우선**: 모든 외부 경로 접근은 검증 절차 필수
- **테마 일관성**: Magic UI 색상 체계 준수
- **에러 처리**: 사용자 친화적인 에러 메시지 제공

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 라이선스

MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참고하세요.

## 🏆 특장점

- **🎯 컴팩트한 디자인**: 화면 공간을 최소한으로 사용하면서 최대한의 정보 제공
- **🔗 스마트 링크**: 6가지 경로 패턴을 지원하는 고급 링크 인식 시스템
- **🛡️ 기업급 보안**: 시스템 보안을 고려한 검증 및 승인 시스템
- **⚡ 고성능**: 비동기 처리와 배치 저장으로 빠른 응답성
- **🎨 Magic UI**: 현대적이고 직관적인 사용자 인터페이스
- **💾 데이터 안전**: 자동 백업과 복구 시스템

---
**Windows TODO Panel** - 더 스마트하고 안전한 TODO 관리의 시작