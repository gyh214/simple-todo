# SPEC-004: MOAI 프로젝트 문서화

**@TAG**: @SPEC:004-MOAI-DOCUMENTATION
**버전**: 1.0.0
**상태**: PENDING (검토 대기)
**작성일**: 2025-11-09
**담당자**: spec-builder

---

## 환경(Environment)

### 프로젝트 컨텍스트
- **프로젝트명**: new-todo-panel (Simple ToDo)
- **프로젝트 모드**: personal
- **대화 언어**: Korean (ko)
- **기술 스택**: Python 3.7+, PyQt6, CLEAN Architecture
- **현재 버전**: 0.21.2 (MoAI-ADK), 2.4 (Simple ToDo)

### MOAI 프레임워크
- **MoAI-ADK 목표**: SPEC-first, TDD-driven development
- **프로젝트 단계**: Phase 1 구현 완료, Phase 2+ 준비 필요
- **문서화 현황**: README.md, CLAUDE.md는 완성, MOAI 문서 미완성

### 현재 상황
- 프로젝트 구조는 명확하지만, MOAI 표준 문서(product.md, structure.md, tech.md)가 없음
- `.moai/project/` 디렉토리에 문서 템플릿이 부재
- 향후 SPEC 생성 시 참조할 수 있는 기본 정보 구조 부족
- 팀 온보딩 및 새로운 개발자 유입 시 학습 곡선 가파름

---

## 가정(Assumptions)

1. **문서화 범위**
   - 현재 README.md와 CLAUDE.md의 내용을 MOAI 표준 형식으로 재정리
   - 새로운 정보 추가보다는 기존 자료 체계화에 중점
   - 향후 SPEC 생성 및 관리를 위한 기반 마련

2. **대상 독자**
   - 새로운 개발자 (온보딩)
   - 프로젝트 기여자 (설계 이해)
   - 유지보수 담당자 (운영 정책)

3. **문서 버전 관리**
   - MOAI 문서는 project 단위로 관리 (spec.md와 별도)
   - 각 SPEC 생성 시 tech.md 업데이트 (라이브러리 버전 변경 시)
   - product.md 업데이트 (기능 추가/변경 시)

4. **다국어 정책**
   - 문서 언어: Korean (프로젝트 conversation_language 기준)
   - 코드 주석: English (전역 일관성)
   - @TAG: English (MOAI 표준)

---

## 요구사항(Requirements)

### Functional Requirements

#### FR-1: product.md 작성
프로젝트의 비즈니스 관점을 정의하는 문서

**요구사항 상세:**
- 프로젝트 비전 및 목표
- 타겟 사용자 정의
- 핵심 기능 목록 (현재 구현된 기능)
- 향후 로드맵 (계획 중인 기능, 우선순위)
- 성공 지표 (KPI)
- 제약사항 (Windows 데스크톱 전용, 로컬 저장 기반 등)

#### FR-2: structure.md 작성
프로젝트의 기술적 구조를 정의하는 문서

**요구사항 상세:**
- CLEAN Architecture 계층 설명 (Presentation/Application/Domain/Infrastructure)
- 각 계층의 책임 및 구성 요소
- 주요 엔티티 및 Value Objects 설명
- 데이터 흐름도 (텍스트 기반 ASCII art)
- 의존성 관계 다이어그램
- 확장 포인트 (Plugin/Extension 가능한 부분)

#### FR-3: tech.md 작성
프로젝트의 기술 스택을 정의하는 문서

**요구사항 상세:**
- 사용 기술 스택 (언어, 프레임워크, 라이브러리)
- 각 라이브러리의 버전 및 사용 이유
- 개발 환경 요구사항 (Python 버전, OS, 기타 도구)
- 빌드 및 배포 프로세스
- 테스트 환경 설정
- 성능 특성 및 제약사항

#### FR-4: MOAI 메타데이터 표준화
모든 MOAI 문서의 일관된 구조 보장

**요구사항 상세:**
- YAML frontmatter 사용 (@TAG, 버전, 상태, 작성일, 담당자)
- 문서 목차(TOC) 자동 생성 용이한 구조
- 각 섹션의 명확한 헤더 계층화
- 참조 링크 체계 (SPEC → product/structure/tech)

### Non-Functional Requirements

#### NFR-1: 유지보수성
- 문서는 마크다운 형식 (버전 관리 용이)
- 코드와 문서의 동기화 메커니즘 정의
- 문서 갱신 주기 명시

#### NFR-2: 접근성
- 문서는 UTF-8 인코딩 (한글 지원)
- 상대 경로 사용 (크로스 플랫폼 호환성)
- 이미지 대체 텍스트 포함 (접근성)

#### NFR-3: 명확성
- 기술 용어는 처음 등장 시 정의
- 예시 코드 포함 (읽기 어려운 개념)
- 관련 파일/폴더 경로 명시

---

## 스펙(Specifications)

### 1. product.md 구조

```
# Simple ToDo - 프로덕트 명세서

## 1. 프로젝트 비전
### 1.1 목표
### 1.2 사용자 페르소나
### 1.3 핵심 가치 제안

## 2. 현재 기능 (v2.4)
### 2.1 Todo 관리
### 2.2 SubTask 관리
### 2.3 시간 관리 (납기일, 반복)
### 2.4 UI/UX 기능
### 2.5 시스템 통합

## 3. 로드맵 (우선순위 기반)
### Phase 2: 테스트 및 안정화 (SPEC-001~003)
### Phase 3: 클라우드 동기화 (SPEC-007)
### Phase 4: 기능 확장 (SPEC-005~008)

## 4. 성공 지표
## 5. 제약사항 및 제한사항
```

### 2. structure.md 구조

```
# Simple ToDo - 아키텍처 명세서

## 1. 아키텍처 개요
### 1.1 CLEAN Architecture 원칙
### 1.2 계층 다이어그램

## 2. 계층별 설명
### 2.1 Presentation Layer
### 2.2 Application Layer
### 2.3 Domain Layer
### 2.4 Infrastructure Layer

## 3. 핵심 엔티티
### 3.1 Todo Entity
### 3.2 SubTask Entity
### 3.3 Value Objects

## 4. 데이터 흐름
### 4.1 Todo 생성 흐름
### 4.2 Todo 수정 흐름
### 4.3 SubTask 관리 흐름

## 5. 의존성 관리
## 6. 확장 포인트
```

### 3. tech.md 구조

```
# Simple ToDo - 기술 스택 명세서

## 1. 시스템 요구사항
## 2. 핵심 기술
### 2.1 Python
### 2.2 PyQt6
### 2.3 기타 라이브러리

## 3. 개발 환경 설정
## 4. 빌드 및 배포
## 5. 테스트 환경
## 6. 성능 특성
```

### 4. 문서 링크 관계

```
product.md (비즈니스 관점)
    ↓ (참조)
SPEC-XXX (구체적 구현)
    ↓ (구현)
structure.md (기술 구조)
    ↓ (활용)
tech.md (기술 스택)
```

---

## 추적성(Traceability)

### @TAG 연결
- **@SPEC:004-MOAI-DOCUMENTATION**: 이 SPEC의 고유 식별자
- **@DOC:PRODUCT**: product.md 내 태그
- **@DOC:STRUCTURE**: structure.md 내 태그
- **@DOC:TECH**: tech.md 내 태그

### 참조 문서
- `README.md`: 사용자 가이드 (product.md 기반)
- `CLAUDE.md`: 개발 철학 (structure.md와 연계)
- `.moai/project/`: MOAI 표준 문서 저장소

### 후속 SPEC
- **SPEC-001**: product.md의 로드맵 기반 테스트 프레임워크 구축
- **SPEC-002**: tech.md의 자동 업데이트 기술 참조
- **SPEC-007**: product.md의 클라우드 동기화 로드맵 구현

---

## 비고

### 작성 시 고려사항
1. **기존 자료 활용**: README.md, CLAUDE.md, 초기 기획서의 내용 재정리
2. **코드 일관성**: 실제 구현 코드와 문서 내용 동기화 확인
3. **버전 관리**: 향후 기능 추가 시 관련 문서 업데이트 프로세스 정의

### 질문 및 결정 사항 (검토 중)
1. 문서 버전 관리 전략: 프로젝트 버전과 동기화?
2. 이미지/다이어그램 포함: 텍스트 기반 ASCII art vs 이미지 파일?
3. 국제화 계획: 향후 영어 버전 제공?

---

**작성자**: spec-builder
**최종 검토**: (검토 대기)
**승인자**: (승인 대기)
