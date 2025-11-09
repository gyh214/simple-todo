---
id: tech
version: 1.0.0
status: active
created: 2025-11-09
updated: 2025-11-09
author: @tdd-implementer
language: ko
---

# Simple ToDo - 기술 스택 명세서

@DOC:TECH

## HISTORY

### v1.0.0 (2025-11-09)
- **INITIAL**: 기술 스택 및 개발 환경 정의
- **AUTHOR**: tdd-implementer
- **SCOPE**: 라이브러리, 개발 환경, 빌드 프로세스

---

## 1. 시스템 요구사항

### 최소 사양

| 항목 | 요구사항 |
|------|---------|
| OS | Windows 10 이상 |
| Python | 3.7+ (권장: 3.9+) |
| RAM | 최소 256MB (권장: 512MB) |
| 저장소 | 최소 50MB (데이터: 수십 KB) |

### 개발 환경

| 항목 | 버전 |
|------|------|
| Python | 3.9.13 |
| pip | 23.2.1 |
| Git | 2.42+ |

---

## 2. 핵심 기술

### 2.1 Python

**선택 이유:**
- 크로스 플랫폼 호환성
- 빠른 개발 속도
- 풍부한 생태계 (PyQt6, psutil 등)

**사용 패턴:**
- 객체지향 프로그래밍 (CLEAN Architecture)
- 타입 힌팅 (Python 3.7+)
- 데코레이터 패턴 (Signal/Slot)

### 2.2 PyQt6

**선택 이유:**
- 네이티브 Windows UI
- 강력한 이벤트 시스템 (Signal/Slot)
- 풍부한 위젯 라이브러리

**버전**: 6.6.0 이상
**사용 모듈**:
- `QMainWindow`: 메인 애플리케이션 창
- `QDialog`: 모달 대화상자
- `QListWidget`: 할일 목록 표현
- `QSystemTrayIcon`: 시스템 트레이

### 2.3 기타 라이브러리

| 라이브러리 | 버전 | 용도 |
|-----------|------|------|
| python-dateutil | >= 2.8.2 | 날짜 처리 |
| psutil | >= 5.9.0 | 시스템 유틸리티 (메모리 모니터링) |
| requests | >= 2.31.0 | HTTP 요청 (업데이트 확인) |
| PyInstaller | >= 6.0.0 | 실행 파일 빌드 |

---

## 3. 개발 환경 설정

### 3.1 가상환경 생성

```bash
# 가상환경 생성
python -m venv venv

# 활성화 (Windows)
venv\Scripts\activate

# 활성화 (macOS/Linux)
source venv/bin/activate
```

### 3.2 의존성 설치

```bash
# 현재 저장소에서
pip install -r requirements.txt

# 개발 모드 (테스트 포함)
pip install -r requirements.txt
pip install pytest pytest-cov mypy
```

### 3.3 IDE 설정

**권장 IDE**: PyCharm, VS Code
**Python 인터프리터**: 가상환경 내 python.exe

---

## 4. 빌드 및 배포

### 4.1 개발 모드 실행

```bash
python main.py
```

### 4.2 디버그 모드 실행

```bash
python debug_main.py
```

상세 로그 출력으로 문제 진단 가능.

### 4.3 실행 파일 빌드

```bash
# 기본 빌드
python build.py

# 디버그 빌드 (상세 출력)
python build.py --debug

# 빌드 + 임시 파일 유지 (디버깅용)
python build.py --keep-temp
```

**결과**: `dist/SimpleTodo.exe`

### 4.4 배포

1. 로컬 테스트: `dist/SimpleTodo.exe` 실행
2. GitHub Releases에 업로드
3. 사용자에게 다운로드 링크 제공

---

## 5. 테스트 환경

### 5.1 테스트 프레임워크

**예정 (SPEC-001)**: pytest + pytest-cov

```bash
# 테스트 실행
pytest tests/ -v

# 커버리지 리포트
pytest tests/ --cov=src --cov-report=html
```

**목표 커버리지**: 85%+

### 5.2 코드 품질 검사

```bash
# 타입 체크
mypy src/

# 코드 스타일
pylint src/

# 형식 검사
black src/
```

---

## 6. 성능 특성

### 6.1 응답 시간

| 작업 | 목표 | 현재 |
|------|------|------|
| Todo 생성 | < 50ms | ~30ms |
| Todo 수정 | < 100ms | ~50ms |
| Todo 삭제 | < 50ms | ~30ms |
| 정렬 | < 200ms | ~100ms (500개 항목) |
| UI 렌더링 | < 16ms | ~10ms (60fps 목표) |

### 6.2 메모리 사용

| 상태 | 사용량 |
|------|--------|
| 공백 상태 | ~50MB |
| 500개 항목 | ~100MB |
| 1000개 항목 | ~150MB |

**최적화 전략**:
- 지연 로딩 (Lazy Loading): 화면에 보이는 항목만 렌더링
- 캐싱: 정렬 결과 캐시 유지
- 메모리 풀: 위젯 재사용

### 6.3 저장소 사용

- 메인 데이터: 수십 KB (500개 항목 기준)
- 백업 저장소: ~1MB (최근 10개 백업)
- 임시 파일: 빌드 시 ~200MB

---

## 7. 개발 워크플로우

### 7.1 로컬 개발

```bash
# 1. 저장소 클론
git clone https://github.com/user/simple-todo.git
cd simple-todo

# 2. 가상환경 구성
python -m venv venv
venv\Scripts\activate  # Windows

# 3. 의존성 설치
pip install -r requirements.txt
pip install pytest pytest-cov mypy

# 4. 애플리케이션 실행
python main.py

# 5. 테스트 실행
pytest tests/ -v --cov=src
```

### 7.2 디버깅

```bash
# 디버그 모드 (상세 로그)
python debug_main.py

# 특정 모듈 테스트
pytest tests/test_todo_service.py -v

# 커버리지 리포트 생성
pytest tests/ --cov=src --cov-report=html
# 결과: htmlcov/index.html
```

### 7.3 배포 프로세스

```bash
# 1. 테스트 검증
pytest tests/ -v

# 2. 실행 파일 빌드
python build.py

# 3. 로컬 테스트
dist/SimpleTodo.exe

# 4. GitHub Release 생성
# (git-manager 에이전트가 처리)
gh release create v2.5.0 \
  -t "Simple ToDo v2.5.0" \
  -n "Release notes" \
  dist/SimpleTodo.exe
```

---

## 8. 라이선스 및 기여

### 8.1 라이선스

MIT License (개인 프로젝트)

### 8.2 기여 가이드

1. Fork 저장소
2. Feature branch 생성 (`git checkout -b feature/SPEC-XXX`)
3. 테스트 작성 및 검증 (coverage 85%+)
4. Pull Request 생성
5. Code Review 및 병합

### 8.3 커밋 규칙

```
feat: 새 기능 추가
fix: 버그 수정
docs: 문서 변경
test: 테스트 추가
refactor: 코드 리팩토링
perf: 성능 개선
ci: CI/CD 변경
```

---

**상태**: ACTIVE (공개 문서)
**최종 검토**: 완료
**버전 기록**:
- v1.0.0 (2025-11-09): 초기 기술 스택 문서 작성
