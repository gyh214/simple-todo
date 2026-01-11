# new-todo-panel

PyQt6 기반 TodoPanel 프로젝트의 개발 가이드입니다.

## 기본 원칙

- **SPEC-First Development**: 요구사항 중심의 개발
- **TDD (Test-Driven Development)**: 테스트 먼저 작성
- **KISS (Keep It Simple, Stupid)**: 단순하고 명확한 코드
- **DRY (Don't Repeat Yourself)**: 중복 제거

## 개발 워크플로우

### 1단계: 의도 파악
- 요구사항 명확화
- 구현 범위 결정
- 테스트 전략 수립

### 2단계: 계획 수립
- 작업을 구조화된 단계로 분해
- 의존성 파악
- 생성/수정/삭제할 파일 목록화

### 3단계: TDD 실행 (RED → GREEN → REFACTOR)
- **RED**: 실패하는 테스트 작성
- **GREEN**: 최소한의 코드로 테스트 통과
- **REFACTOR**: 코드 품질 개선

### 4단계: 검증 및 커밋
- 모든 테스트 통과 확인
- 코드 리뷰
- git 커밋 (명확한 메시지)

## 파일 구조

```
new-todo-panel/
├── src/                      # 소스 코드
│   └── todo_panel/
│       ├── __init__.py
│       ├── main.py          # 애플리케이션 진입점
│       ├── ui/              # UI 관련 모듈
│       └── models/          # 데이터 모델
├── tests/                    # 테스트 코드
│   └── test_*.py
├── CLAUDE.md                 # 이 파일
├── README.md                 # 프로젝트 설명
└── requirements.txt          # 의존성
```

## 핵심 개발 원칙

### 코드 품질 (TRUST 5)
- **Test First**: 테스트부터 작성
- **Readable**: 읽기 쉬운 코드
- **Unified**: 일관된 스타일과 구조
- **Secured**: 보안을 고려한 구현
- **Trackable**: 변경 이력 추적 가능

### 커밋 메시지 가이드
- 명확한 제목 (50자 이내)
- 상세 설명 (필요시)
- 형식: `feat:`, `fix:`, `refactor:`, `test:`, `docs:` 등

### 테스트 작성
- 각 기능마다 테스트 케이스 작성
- 정상 케이스와 예외 케이스 모두 포함
- 테스트 이름은 명확하게 (무엇을 테스트하는지 알 수 있도록)

## 프로젝트 정보

- **이름**: new-todo-panel
- **타입**: PyQt6 데스크톱 애플리케이션
- **언어**: Python 3.8+

## 금지 사항

- ❌ 계획 없이 코드 작성 시작
- ❌ 테스트 없이 구현
- ❌ TODO/임시방편 코드
- ❌ 중복된 코드 작성 (기존 코드 재사용 우선)
- ❌ 명확하지 않은 커밋 메시지

