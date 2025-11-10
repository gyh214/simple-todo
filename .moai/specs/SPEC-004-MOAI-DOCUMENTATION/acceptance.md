# SPEC-004 수용 기준서

**@TAG**: @ACCEPTANCE:004-MOAI-DOCUMENTATION
**SPEC 참조**: @SPEC:004-MOAI-DOCUMENTATION
**최종 업데이트**: 2025-11-09

---

## 1. 수용 기준 개요

### 정의
SPEC-004(MOAI 문서화)가 완료되었을 때 확인해야 할 구체적 기준과 테스트 절차

### 수용 범위
- product.md, structure.md, tech.md 3개 파일 작성 완료
- MOAI 표준 형식 준수
- 내용 정확성 및 완성도
- 팀 리뷰 통과

---

## 2. 상세 수용 기준

### 2.1 파일 생성 기준

#### Acceptance Criteria: AC-2.1.1 (파일 존재)
**Given** (주어진 상황): SPEC-004 작업 완료 후
**When** (조건): `.moai/project/` 디렉토리 확인
**Then** (결과):
- [ ] `.moai/project/product.md` 파일 존재
- [ ] `.moai/project/structure.md` 파일 존재
- [ ] `.moai/project/tech.md` 파일 존재

**확인 방법**:
```bash
ls -la .moai/project/
# 출력: product.md structure.md tech.md 세 파일 모두 보임
```

---

#### Acceptance Criteria: AC-2.1.2 (파일 크기)
**Given**: 각 파일이 작성됨
**When**: 파일 크기 확인
**Then**:
- [ ] product.md: 400~600 단어 (약 2KB~3KB)
- [ ] structure.md: 600~800 단어 (약 3KB~5KB)
- [ ] tech.md: 500~700 단어 (약 2.5KB~4KB)

**확인 방법**:
```bash
wc -w .moai/project/*.md
# 각 파일의 단어 수 확인
```

---

### 2.2 포맷팅 및 구조 기준

#### Acceptance Criteria: AC-2.2.1 (마크다운 포맷)
**Given**: 모든 문서 작성 완료
**When**: 마크다운 형식 검증
**Then**:
- [ ] 모든 파일이 `.md` 확장자
- [ ] YAML frontmatter 포함 (선택)
  ```yaml
  ---
  title: "Simple ToDo - 프로덕트 명세서"
  date: "2025-11-09"
  version: "1.0.0"
  ---
  ```
- [ ] UTF-8 인코딩 (한글 깨짐 없음)
- [ ] 줄 끝 CRLF (Windows) → LF (Unix) 변환 검토

**확인 방법**:
```bash
file .moai/project/*.md
# 각 파일이 "text/plain; charset=utf-8" 또는 동급 표시

# 인코딩 확인
file -i .moai/project/*.md
```

---

#### Acceptance Criteria: AC-2.2.2 (헤더 계층화)
**Given**: 마크다운 문서 작성됨
**When**: 헤더 구조 검증
**Then**:
- [ ] **product.md**:
  - 최상위: `# Simple ToDo - 프로덕트 명세서` (1단계)
  - 섹션: `## 1. 프로젝트 비전` (2단계)
  - 소항목: `### 1.1 목표` (3단계)
  - 3단계까지만 사용 (4단계 이상 금지)

- [ ] **structure.md**:
  - 최상위: `# Simple ToDo - 아키텍처 명세서` (1단계)
  - 섹션: `## 1. 아키텍처 개요` (2단계)
  - 소항목: `### 1.1 CLEAN Architecture 원칙` (3단계)

- [ ] **tech.md**:
  - 최상위: `# Simple ToDo - 기술 스택 명세서` (1단계)
  - 섹션: `## 1. 시스템 요구사항` (2단계)
  - 소항목: `### 1.1 Python 버전` (3단계)

**확인 방법**:
```bash
# grep으로 헤더 체계 확인
grep "^#" .moai/project/product.md | head -20
```

---

### 2.3 내용 정확성 기준

#### Acceptance Criteria: AC-2.3.1 (product.md - 비즈니스 정보)
**Given**: product.md 작성됨
**When**: 내용 검증
**Then**:

1. **프로젝트 비전** 섹션:
   - [ ] 프로젝트 목표 명확 (1문장, 20자 이상)
   - [ ] 타겟 사용자 정의 (최소 2가지 페르소나)
   - [ ] 핵심 가치 제안 (차별화 요소 최소 3가지)

2. **현재 기능** 섹션 (v2.4 기준):
   - [ ] Todo 관리: 생성, 수정, 삭제, 완료 처리
   - [ ] SubTask 관리: 생성, 수정, 삭제, 완료, 펼침 상태 유지
   - [ ] 시간 관리: 납기일 설정, 반복 할일, 시각적 구분
   - [ ] UI/UX: 다크 모드, 드래그 앤 드롭, 키보드 단축키, 링크/경로 감지
   - [ ] 시스템: 시스템 트레이, 자동 저장, 백업, 단일 인스턴스

3. **로드맵** 섹션:
   - [ ] Phase 2: 테스트 및 안정화 (SPEC-001~003 명시)
   - [ ] Phase 3: 클라우드 동기화 (SPEC-007 명시)
   - [ ] Phase 4: 기능 확장 (SPEC-005~008 명시)
   - [ ] 각 Phase별 우선순위 명확 (High/Medium/Low)

4. **성공 지표** 섹션:
   - [ ] 최소 3가지 KPI 정의 (정량적)
   - [ ] 측정 방법 명시

5. **제약사항** 섹션:
   - [ ] 최소 3가지 제약사항 명시
   - [ ] 각 제약사항의 이유 설명

**확인 방법**:
```bash
# 특정 섹션 추출하여 내용 검증
sed -n '/## 1. 프로젝트 비전/,/## 2. 현재 기능/p' .moai/project/product.md
```

---

#### Acceptance Criteria: AC-2.3.2 (structure.md - 기술 구조)
**Given**: structure.md 작성됨
**When**: 내용 검증
**Then**:

1. **아키텍처 개요** 섹션:
   - [ ] CLEAN Architecture 원칙 설명 (3줄 이상)
   - [ ] 계층 다이어그램 또는 텍스트 설명

2. **계층별 설명** 섹션:
   - [ ] Presentation Layer: MainWindow, Dialogs, Widgets 언급
   - [ ] Application Layer: TodoService, UseCases 언급
   - [ ] Domain Layer: Entity, Value Objects, Services 언급
   - [ ] Infrastructure Layer: Repository, Migration, Backup 언급
   - [ ] 각 계층별 책임 명확 (3줄 이상)

3. **핵심 엔티티** 섹션:
   - [ ] Todo Entity: 속성(properties) 최소 5개 언급
   - [ ] SubTask Entity: Todo와의 관계 명시
   - [ ] Value Objects: TodoId, Content, DueDate, RecurrenceRule 각각 설명 (2줄 이상)

4. **데이터 흐름** 섹션:
   - [ ] Todo 생성 흐름: UI → Service → Repository → Disk 단계 설명
   - [ ] Todo 수정 흐름: 상세 설명
   - [ ] SubTask 관리 흐름: 중첩 구조 설명

5. **의존성 관리** 섹션:
   - [ ] DI Container 설명
   - [ ] 순환 의존성 회피 방법 언급

6. **확장 포인트** 섹션:
   - [ ] Repository 확장 방법 명시
   - [ ] Service 확장 방법 명시
   - [ ] Widget 확장 방법 명시

**확인 방법**:
```bash
# 전체 섹션 개수 확인
grep "^##" .moai/project/structure.md | wc -l
# 최소 6개 이상의 메인 섹션 필요
```

---

#### Acceptance Criteria: AC-2.3.3 (tech.md - 기술 스택)
**Given**: tech.md 작성됨
**When**: 내용 검증
**Then**:

1. **시스템 요구사항** 섹션:
   - [ ] Python 버전: "3.7+" 명시
   - [ ] OS: "Windows 10+" 명시
   - [ ] RAM, HDD 최소 요구사항 명시

2. **핵심 기술** 섹션:
   - [ ] Python: 버전, 사용 이유 명시
   - [ ] PyQt6: "6.6.0" 이상 버전 명시, 선택 이유 설명
   - [ ] python-dateutil: "2.8.2" 이상, 용도 설명
   - [ ] psutil: "5.9.0" 이상, 용도 설명
   - [ ] requests: "2.31.0" 이상, 용도 설명
   - [ ] PyInstaller: "6.0.0" 이상, 빌드 도구임 명시

3. **개발 환경 설정** 섹션:
   - [ ] 가상환경 생성 명령어 제시
   - [ ] 의존성 설치 명령어 제시
   - [ ] IDE 추천 (선택)

4. **빌드 및 배포** 섹션:
   - [ ] build.py 사용법 설명
   - [ ] 결과물: SimpleTodo.exe 명시
   - [ ] GitHub Releases 배포 프로세스 설명

5. **테스트 환경** 섹션:
   - [ ] pytest 프레임워크 언급 (SPEC-001 완료 후)
   - [ ] 테스트 실행 명령어 (선택)

6. **성능 특성** 섹션:
   - [ ] 메모리 사용량: 평상시/최대 명시
   - [ ] CPU 요구사항: 최소 사양 명시
   - [ ] UI 응답시간: "200ms 이하" 등 명시
   - [ ] 저장소 용량 예상: 할일 수 대비 선형 명시

**확인 방법**:
```bash
# 라이브러리 버전 정보 확인
grep -E "^- \*\*|>=" .moai/project/tech.md | head -10
```

---

### 2.4 일관성 기준

#### Acceptance Criteria: AC-2.4.1 (문서 간 일관성)
**Given**: product.md, structure.md, tech.md 작성됨
**When**: 문서 간 교차 검증
**Then**:
- [ ] product.md의 기능 목록 ↔ structure.md의 계층 설명 일치
- [ ] product.md의 기술 스택 언급 ↔ tech.md 버전 일치
- [ ] structure.md의 라이브러리 언급 ↔ tech.md 설명 일치
- [ ] 모든 문서의 프로젝트 버전 표기 일관 (v2.4 기준)

**확인 방법**:
```bash
# 세 파일에서 "PyQt6" 언급 빈도 확인
grep -i "PyQt6" .moai/project/*.md

# 세 파일에서 "todo" 언급 빈도 확인
grep -i "todo" .moai/project/*.md | wc -l
```

---

#### Acceptance Criteria: AC-2.4.2 (README.md와 중복 확인)
**Given**: product.md, structure.md, tech.md 작성됨
**When**: README.md와 교차 검증
**Then**:
- [ ] product.md의 기능 설명이 README.md 기능 섹션과 **명확히 다름** (더 상세함)
- [ ] structure.md가 CLAUDE.md보다 **더 구체적** (계층별 설명)
- [ ] tech.md가 README.md 기술 스택과 **정확히 일치**

**확인 방법**:
```bash
# README.md의 기능 섹션과 product.md 비교
diff <(sed -n '/## ✨ 주요 기능/,/## 🚀 설치 방법/p' README.md) \
     <(sed -n '/## 2. 현재 기능/,/## 3. 로드맵/p' .moai/project/product.md)
```

---

### 2.5 링크 및 참조 기준

#### Acceptance Criteria: AC-2.5.1 (파일 경로 유효성)
**Given**: 문서에 파일 경로 언급됨
**When**: 경로 검증
**Then**:
- [ ] 모든 언급된 파일 경로가 실제로 존재
  - `src/domain/entities/` (Domain Layer)
  - `src/application/services/` (Application Layer)
  - `src/presentation/ui/` (Presentation Layer)
  - `src/infrastructure/repositories/` (Infrastructure Layer)
- [ ] 상대 경로 사용 (절대 경로 금지)
- [ ] Forward slash `/` 사용 (백슬래시 금지)

**확인 방법**:
```bash
# structure.md에서 언급된 파일 경로 추출하여 확인
grep -o "src/[^)]*" .moai/project/structure.md | sort -u | while read path; do
  [ -e "$path" ] && echo "OK: $path" || echo "ERROR: $path"
done
```

---

#### Acceptance Criteria: AC-2.5.2 (@TAG 일관성)
**Given**: 문서에 @TAG 포함됨
**When**: TAG 검증
**Then**:
- [ ] product.md 내: @DOC:PRODUCT 사용 (일관)
- [ ] structure.md 내: @DOC:STRUCTURE 사용 (일관)
- [ ] tech.md 내: @DOC:TECH 사용 (일관)
- [ ] 모든 문서: 참조 SPEC은 @SPEC:XXX 형식 (예: @SPEC:004-MOAI-DOCUMENTATION)

**확인 방법**:
```bash
# @TAG 사용 현황 확인
grep "@" .moai/project/*.md
```

---

### 2.6 한글 맞춤법 및 표기 기준

#### Acceptance Criteria: AC-2.6.1 (한글 맞춤법)
**Given**: 한글 문서 작성 완료
**When**: 맞춤법 검증
**Then**:
- [ ] 띄어쓰기 오류 없음
- [ ] 문법 오류 없음
- [ ] 한글/영문 혼용 시 적절한 띄어쓰기
  - 예: "PyQt6은" (O), "PyQt6은" (O)
  - 예: "TODO (할일)" (O), "TODO(할일)" (X)
- [ ] 숫자 표기 일관성
  - 버전: "v2.4", "PyQt6 >= 6.6.0"
  - 개수: "3개", "5가지"

**확인 방법**:
```bash
# 한글 맞춤법 도구 사용 (선택)
# - Hunspell 또는 기타 한글 검사기
```

---

#### Acceptance Criteria: AC-2.6.2 (용어 일관성)
**Given**: 용어 사용됨
**When**: 용어 일관성 검증
**Then**:
- [ ] "할일" vs "TODO": 일관적으로 사용
- [ ] "하위 할일" vs "SubTask": 문맥에 맞게 사용
- [ ] "납기일" vs "Due Date": 일관적으로 사용
- [ ] "저장소" vs "Repository": 일관적으로 사용
- [ ] "버전" vs "Version": 일관적으로 사용

**확인 방법**:
```bash
# 특정 용어의 일관성 확인
grep -n "할일\|TODO" .moai/project/*.md | head -20
```

---

### 2.7 최종 검증 기준

#### Acceptance Criteria: AC-2.7.1 (타이핑 오류)
**Given**: 문서 작성 완료
**When**: 최종 검토
**Then**:
- [ ] 오타 없음 (반복 읽음으로 확인)
- [ ] 마크다운 문법 오류 없음 (링크, 이미지, 코드 블록)
- [ ] 빈 줄 적절 (과도한 빈 줄 없음)

**확인 방법**:
```bash
# 마크다운 검증 도구 (선택)
# npm install -g markdownlint-cli
markdownlint .moai/project/*.md
```

---

#### Acceptance Criteria: AC-2.7.2 (Git 커밋 준비)
**Given**: 문서 최종 검증 완료
**When**: 커밋 전 확인
**Then**:
- [ ] 3개 파일 모두 추가됨: `git add .moai/project/*.md`
- [ ] 커밋 메시지 준비:
  ```
  feat: MOAI 프로젝트 문서 작성 (product, structure, tech)

  - product.md: 프로젝트 비전, 기능, 로드맵
  - structure.md: CLEAN Architecture 설명
  - tech.md: 기술 스택 및 개발 환경

  @SPEC:004-MOAI-DOCUMENTATION
  ```
- [ ] 커밋 실행 가능 (충돌 없음)

**확인 방법**:
```bash
git status
git diff .moai/project/*.md
```

---

## 3. 테스트 시나리오

### 테스트 케이스 1: 새로운 개발자 온보딩
**목표**: 새로운 개발자가 product.md만으로 프로젝트 이해 가능한가?

**시나리오**:
1. 새로운 개발자가 product.md 읽음
2. 프로젝트의 목표, 기능, 로드맵 이해
3. 기존 기능과 계획된 기능 구분 가능

**성공 기준**:
- [ ] 개발자가 "Simple ToDo가 무엇인가?" 질문에 1분 내 답변 가능
- [ ] 개발자가 "향후 계획이 무엇인가?" 질문에 명확히 답변 가능

---

### 테스트 케이스 2: 아키텍처 이해도 검증
**목표**: 개발자가 structure.md만으로 코드 네비게이션 가능한가?

**시나리오**:
1. 개발자가 structure.md 읽음
2. "새 기능을 추가하려면 어디를 수정해야 하나?" 질문에 답변
3. 계층별 책임 이해

**성공 기준**:
- [ ] 개발자가 5가지 구체적인 파일/폴더 언급 가능
- [ ] Domain, Application, Presentation 계층 구분 가능

---

### 테스트 케이스 3: 개발 환경 구축
**목표**: tech.md의 지시사항만으로 개발 환경 구축 가능한가?

**시나리오**:
1. 새로운 개발자가 Windows 10 컴퓨터에서 시작
2. tech.md의 "개발 환경 설정" 섹션 따라감
3. `python main.py` 실행 성공

**성공 기준**:
- [ ] 모든 명령어 실행 성공 (오류 없음)
- [ ] 가상환경 활성화 및 의존성 설치 완료
- [ ] 애플리케이션 실행 가능 (UI 표시)

---

### 테스트 케이스 4: 로드맵 명확성
**목표**: product.md의 로드맵만으로 우선순위 결정 가능한가?

**시나리오**:
1. 개발 리더가 product.md의 로드맵 섹션 읽음
2. "다음에 어떤 기능을 추가해야 하나?" 질문에 답변
3. Phase 단계별 우선순위 명확

**성공 기준**:
- [ ] Phase 2, 3, 4가 명확히 구분됨
- [ ] 각 Phase 내 SPEC 우선순위 명시
- [ ] 비즈니스 효과(기대 효과) 명확

---

## 4. 정의된 완료(Definition of Done)

### DoD 체크리스트
- [ ] 3개 파일 모두 `.moai/project/` 디렉토리에 저장됨
- [ ] 모든 AC (Acceptance Criteria) 통과
- [ ] 3개 테스트 시나리오 중 최소 2개 통과
- [ ] 마크다운 문법 오류 없음 (markdownlint 통과)
- [ ] 한글 맞춤법 확인 완료
- [ ] Git 커밋 메시지 준비 완료
- [ ] 팀 리뷰 통과 (최소 1명)

---

## 5. 검증자 체크리스트

### Primary Reviewer
- [ ] 문서 구조 및 내용 검토
- [ ] 기술 정확성 확인
- [ ] 링크 유효성 검증

### Secondary Reviewer (선택)
- [ ] 한글 맞춤법 검토
- [ ] 가독성 평가
- [ ] 사용자 관점 피드백

---

**작성자**: spec-builder
**최종 검증**: (검증 대기)
**승인자**: (승인 대기)
