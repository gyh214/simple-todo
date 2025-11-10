# Phase 4: Application Layer 구현 완료

## 개요

Simple ToDo 앱의 자동 업데이트 기능을 위한 **Application Layer (Use Cases 및 Services)**를 성공적으로 구현했습니다.

**구현 날짜**: 2025-11-08
**구현 파일**: 4개
**코드 라인**: 약 1,200 라인
**테스트 상태**: Python 구문 검증 통과

---

## 구현 파일

### 1. Use Cases (3개)

#### 1.1. `src/application/use_cases/check_for_updates.py` (13KB)

**목적**: 업데이트 확인 비즈니스 로직

**주요 기능**:
- `execute()`: 자동 업데이트 체크 (24시간 간격 존중)
- `force_check()`: 강제 업데이트 체크 (수동 체크)
- `_should_check_now()`: 체크 시간 확인

**비즈니스 규칙**:
- check_interval_hours 경과 시에만 체크
- 건너뛴 버전은 알림 표시 안 함
- 체크 시간 자동 기록
- 현재 버전보다 높은 릴리스만 반환

**의존성**:
- `GitHubReleaseRepository` (Infrastructure)
- `UpdateSettingsRepository` (Infrastructure)
- `VersionComparisonService` (Domain)
- `AppVersion` (Domain)

**예제**:
```python
check_use_case = CheckForUpdatesUseCase(
    github_repo=github_repo,
    settings_repo=settings_repo,
    version_service=version_service,
    current_version=AppVersion.from_string("2.4"),
    check_interval_hours=24
)

# 자동 체크
release = check_use_case.execute()

# 강제 체크
release = check_use_case.force_check()
```

---

#### 1.2. `src/application/use_cases/download_update.py` (7.6KB)

**목적**: 업데이트 파일 다운로드 관리

**주요 기능**:
- `execute()`: 파일 다운로드 및 검증
- `verify_download()`: 파일 크기 검증
- `cancel()`: 다운로드 취소 (예약)
- `cleanup_temp_files()`: 임시 파일 정리

**비즈니스 규칙**:
- 다운로드 후 파일 크기 검증 필수
- 진행률 콜백으로 UI 업데이트
- 실패 시 임시 파일 자동 정리
- 검증 실패 시 파일 삭제

**의존성**:
- `UpdateDownloaderService` (Infrastructure)
- `Release` (Domain)

**예제**:
```python
download_use_case = DownloadUpdateUseCase(
    downloader=downloader,
    filename="SimpleTodo_new.exe"
)

def on_progress(downloaded, total):
    print(f"{downloaded}/{total} bytes")

file_path = download_use_case.execute(
    release=release,
    progress_callback=on_progress
)
```

---

#### 1.3. `src/application/use_cases/install_update.py` (8.4KB)

**목적**: 업데이트 설치 및 애플리케이션 재시작

**주요 기능**:
- `execute()`: Batch script 생성 및 실행
- `prepare_for_shutdown()`: 종료 전 준비
- `verify_new_exe()`: 새 exe 파일 검증

**비즈니스 규칙**:
- Batch script로 파일 교체 수행
- 프로세스 종료 후 교체 (안전성)
- 새 버전 자동 재시작
- Script 자체 삭제로 흔적 제거

**의존성**:
- `UpdateInstallerService` (Infrastructure)

**예제**:
```python
install_use_case = InstallUpdateUseCase(
    installer=installer,
    current_exe_path=Path("D:/app/SimpleTodo.exe")
)

# 검증
if install_use_case.verify_new_exe(new_exe_path):
    # 준비
    install_use_case.prepare_for_shutdown()

    # 설치 (앱 종료됨!)
    success = install_use_case.execute(new_exe_path)
```

**Warning**: `execute()` 성공 시 앱이 즉시 종료됩니다!

---

### 2. Services (1개)

#### 2.1. `src/application/services/update_scheduler_service.py` (11KB)

**목적**: 업데이트 체크 스케줄링 및 조율

**주요 기능**:
- `should_check_on_startup()`: 앱 시작 시 체크 여부 결정
- `check_and_notify()`: 업데이트 확인 및 알림
- `skip_version()`: 특정 버전 건너뛰기
- `reset_skipped_version()`: 건너뛴 버전 초기화
- `enable_auto_check()`: 자동 체크 활성화/비활성화
- `get_auto_check_status()`: 자동 체크 상태 조회
- `get_skipped_version()`: 건너뛴 버전 조회

**비즈니스 규칙**:
- 자동 체크 비활성화 시 체크 안 함
- 건너뛴 버전 관리
- Use Case와 Repository 간 조율

**의존성**:
- `CheckForUpdatesUseCase` (Application)
- `UpdateSettingsRepository` (Infrastructure)

**예제**:
```python
scheduler = UpdateSchedulerService(
    check_use_case=check_use_case,
    settings_repo=settings_repo
)

# 앱 시작 시
if scheduler.should_check_on_startup():
    release = scheduler.check_and_notify()
    if release:
        # UI 업데이트 다이얼로그 표시
        show_update_dialog(release)

# 버전 건너뛰기
scheduler.skip_version(release.version)

# 자동 체크 비활성화
scheduler.enable_auto_check(False)
```

---

## 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────┐
│                   Presentation Layer                        │
│                   (Phase 5 - 다음 단계)                      │
│  - UpdateCheckDialog                                        │
│  - UpdateDownloadDialog                                     │
│  - UpdateSettingsDialog                                     │
└─────────────────────────────────────────────────────────────┘
                            ↓ 호출
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer (✓)                     │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Use Cases                                             │  │
│  │  - CheckForUpdatesUseCase                            │  │
│  │  - DownloadUpdateUseCase                             │  │
│  │  - InstallUpdateUseCase                              │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Services                                              │  │
│  │  - UpdateSchedulerService                            │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓ 의존
┌─────────────────────────────────────────────────────────────┐
│                Infrastructure Layer (✓ Phase 3)             │
│  - GitHubReleaseRepository                                  │
│  - UpdateSettingsRepository                                 │
│  - UpdateDownloaderService                                  │
│  - UpdateInstallerService                                   │
└─────────────────────────────────────────────────────────────┘
                            ↓ 의존
┌─────────────────────────────────────────────────────────────┐
│                   Domain Layer (✓ Phase 1,2)                │
│  - Release (Entity)                                         │
│  - AppVersion (Value Object)                                │
│  - VersionComparisonService                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 주요 비즈니스 흐름

### 1. 앱 시작 시 자동 업데이트 체크

```
1. MainWindow 시작
   ↓
2. UpdateSchedulerService.should_check_on_startup()
   - 자동 체크 활성화 확인
   ↓
3. UpdateSchedulerService.check_and_notify()
   ↓
4. CheckForUpdatesUseCase.execute()
   - 24시간 경과 확인
   - GitHub 최신 릴리스 조회
   - 버전 비교
   - 건너뛴 버전 확인
   ↓
5. Release 반환 (업데이트 가능 시)
   ↓
6. UI에서 UpdateCheckDialog 표시
```

### 2. 수동 업데이트 확인

```
1. 사용자가 "업데이트 확인" 버튼 클릭
   ↓
2. UpdateSchedulerService.reset_skipped_version()
   - 건너뛴 버전 초기화
   ↓
3. CheckForUpdatesUseCase.force_check()
   - 24시간 무시하고 즉시 체크
   ↓
4. Release 반환
   ↓
5. UI에서 결과 표시
```

### 3. 업데이트 다운로드 및 설치

```
1. 사용자가 "업데이트" 버튼 클릭
   ↓
2. DownloadUpdateUseCase.execute(release, progress_callback)
   - HTTP 다운로드
   - 진행률 콜백 호출 (UI 업데이트)
   - 파일 검증
   ↓
3. 다운로드 성공 → Path 반환
   ↓
4. InstallUpdateUseCase.verify_new_exe(path)
   - 파일 검증
   ↓
5. InstallUpdateUseCase.prepare_for_shutdown()
   - 데이터 저장, 로그 플러시
   ↓
6. InstallUpdateUseCase.execute(path)
   - Batch script 생성
   - Script 실행
   ↓
7. QApplication.quit()
   - 앱 종료
   ↓
8. Batch script 실행
   - 2초 대기
   - 프로세스 강제 종료
   - 파일 교체
   - 새 앱 실행
   - Script 자체 삭제
```

### 4. 버전 건너뛰기

```
1. 사용자가 "건너뛰기" 버튼 클릭
   ↓
2. UpdateSchedulerService.skip_version(release.version)
   ↓
3. UpdateSettingsRepository.set_skipped_version(version)
   ↓
4. data.json에 저장
   ↓
5. 다음 체크 시 이 버전은 알림 표시 안 함
```

---

## 에러 처리 전략

### 1. 업데이트 확인 실패

```python
try:
    release = check_use_case.execute()
except Exception as e:
    logger.error(f"업데이트 확인 실패: {e}")
    # 체크 시간은 저장 (무한 재시도 방지)
    # UI에서 에러 메시지 표시 안 함 (조용히 실패)
```

### 2. 다운로드 실패

```python
file_path = download_use_case.execute(release, progress_callback)

if not file_path:
    # 임시 파일 자동 정리됨
    show_error("다운로드에 실패했습니다. 네트워크를 확인하세요.")
```

### 3. 설치 실패

```python
success = install_use_case.execute(new_exe_path)

if not success:
    show_error("설치에 실패했습니다. 수동으로 파일을 교체하세요.")
    # 다운로드한 파일 경로 표시
```

---

## 테스트 가이드

### 1. Unit Tests (권장)

```python
# tests/application/test_check_for_updates.py
def test_execute_returns_none_when_interval_not_passed():
    # Given
    check_use_case = CheckForUpdatesUseCase(...)
    settings_repo.save_last_check_time(datetime.now())

    # When
    release = check_use_case.execute()

    # Then
    assert release is None

def test_execute_returns_release_when_update_available():
    # Given
    check_use_case = CheckForUpdatesUseCase(...)
    mock_github_repo.get_latest_release.return_value = Release(...)

    # When
    release = check_use_case.execute()

    # Then
    assert release is not None
    assert release.version > current_version
```

### 2. Integration Tests (수동)

Phase 4 사용 예제 파일을 실행하여 테스트:

```bash
cd D:\dev_proj\new-todo-panel
python docs\update_feature\phase4_usage_example.py
```

**주의**: 예제 3 (다운로드 및 설치)는 실제 파일을 다운로드하므로 주석 처리됨

---

## Phase 5 준비사항

다음 단계(Presentation Layer)를 위한 준비:

### 1. UI 다이얼로그 (3개)

#### 1.1. UpdateCheckDialog
- 업데이트 가능 알림
- 릴리스 노트 표시
- 버튼: "업데이트", "건너뛰기", "나중에"

#### 1.2. UpdateDownloadDialog
- 다운로드 진행률 표시
- 취소 버튼 (선택사항)

#### 1.3. UpdateSettingsDialog (또는 기존 설정에 추가)
- "자동 업데이트 체크" 체크박스
- 체크 간격 설정 (선택사항)

### 2. MainWindow 통합

```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # DI Container에서 주입
        self.scheduler = container.get(UpdateSchedulerService)

        # 앱 시작 시 체크
        QTimer.singleShot(3000, self._check_for_updates_on_startup)

    def _check_for_updates_on_startup(self):
        if self.scheduler.should_check_on_startup():
            release = self.scheduler.check_and_notify()
            if release:
                self._show_update_dialog(release)
```

### 3. DI Container 설정

`src/core/container.py`에 추가:

```python
# Application Layer
from src.application.use_cases.check_for_updates import CheckForUpdatesUseCase
from src.application.use_cases.download_update import DownloadUpdateUseCase
from src.application.use_cases.install_update import InstallUpdateUseCase
from src.application.services.update_scheduler_service import UpdateSchedulerService

def setup_update_dependencies(container):
    # Infrastructure
    container.register_singleton(
        GitHubReleaseRepository,
        lambda: GitHubReleaseRepository(GITHUB_REPO_OWNER, GITHUB_REPO_NAME)
    )

    container.register_singleton(
        UpdateSettingsRepository,
        lambda: UpdateSettingsRepository(DATA_FILE)
    )

    # Application
    container.register_singleton(
        CheckForUpdatesUseCase,
        lambda: CheckForUpdatesUseCase(
            github_repo=container.get(GitHubReleaseRepository),
            settings_repo=container.get(UpdateSettingsRepository),
            version_service=VersionComparisonService(),
            current_version=AppVersion.from_string(APP_VERSION),
            check_interval_hours=UPDATE_CHECK_INTERVAL_HOURS
        )
    )

    container.register_singleton(
        UpdateSchedulerService,
        lambda: UpdateSchedulerService(
            check_use_case=container.get(CheckForUpdatesUseCase),
            settings_repo=container.get(UpdateSettingsRepository)
        )
    )
```

---

## 검증 결과

### 1. 파일 생성 확인

```bash
✓ src/application/use_cases/check_for_updates.py (13KB)
✓ src/application/use_cases/download_update.py (7.6KB)
✓ src/application/use_cases/install_update.py (8.4KB)
✓ src/application/services/update_scheduler_service.py (11KB)
```

### 2. Python 구문 검증

```bash
✓ All files compiled successfully
```

### 3. 의존성 확인

- Domain Layer: ✓ (Phase 1,2)
- Infrastructure Layer: ✓ (Phase 3)
- Application Layer: ✓ (Phase 4)
- Presentation Layer: ⏳ (Phase 5 - 다음 단계)

---

## 사용 예제

상세한 사용 예제는 다음 파일 참고:
- `docs/update_feature/phase4_usage_example.py`

5가지 예제 포함:
1. 앱 시작 시 자동 체크
2. 수동 업데이트 확인
3. 다운로드 및 설치
4. 버전 건너뛰기
5. 설정 관리

---

## 다음 단계: Phase 5

**목표**: Presentation Layer (PyQt6 UI) 구현

**구현 내용**:
1. UpdateCheckDialog - 업데이트 알림 다이얼로그
2. UpdateDownloadDialog - 다운로드 진행률 다이얼로그
3. MainWindow 통합 - 앱 시작 시 자동 체크
4. DI Container 설정 - 의존성 주입
5. 메뉴 항목 추가 - "업데이트 확인"

**예상 작업 시간**: 2-3시간

---

## 참고 문서

- [Phase 1-3 Summary](./PHASE1-3_SUMMARY.md)
- [Usage Example](./phase4_usage_example.py)
- [GitHub API Documentation](https://docs.github.com/en/rest/releases/releases)

---

## 작성자

- **날짜**: 2025-11-08
- **Phase**: 4 (Application Layer)
- **상태**: ✓ 완료
