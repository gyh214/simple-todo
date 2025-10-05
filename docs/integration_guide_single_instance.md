# SingleInstanceManager 통합 가이드

## 개요
SingleInstanceManager는 애플리케이션의 중복 실행을 방지하고, 중복 실행 시도 시 기존 창을 활성화하는 기능을 제공합니다.

## 구현 완료 사항

### 1. 파일 위치
```
src/presentation/system/single_instance.py
```

### 2. 주요 메서드
- `is_already_running()`: 이미 실행 중인지 확인
- `start_listener()`: 활성화 요청 수신 리스너 시작
- `activate_existing_instance()`: 기존 인스턴스로 활성화 요청 전송
- `cleanup()`: 리소스 정리

### 3. PyQt6 시그널
- `activate_requested`: 활성화 요청이 들어왔을 때 발생

## main.py 통합 방법

### 기본 통합 패턴

```python
# -*- coding: utf-8 -*-
"""
Simple ToDo 애플리케이션 진입점
"""
import sys
from PyQt6.QtWidgets import QApplication

import config
from src.presentation.system import SingleInstanceManager
from src.presentation.ui.main_window import MainWindow


def main():
    """애플리케이션 진입점"""
    app = QApplication(sys.argv)

    # 애플리케이션 설정
    app.setApplicationName(config.APP_NAME)
    app.setApplicationVersion(config.APP_VERSION)

    # ========== SingleInstanceManager 초기화 ==========
    instance_manager = SingleInstanceManager()

    # 이미 실행 중인지 확인
    if instance_manager.is_already_running():
        print(f"{config.APP_NAME}이(가) 이미 실행 중입니다.")

        # 기존 창 활성화 시도
        success = instance_manager.activate_existing_instance()

        if success:
            print("기존 창을 활성화했습니다.")
        else:
            print("기존 창 활성화에 실패했습니다. 프로세스를 종료합니다.")

        # 정리 및 종료
        instance_manager.cleanup()
        sys.exit(0)

    print(f"{config.APP_NAME} 시작 중...")

    # ========== DI Container 초기화 ==========
    initialize_infrastructure_layer()
    initialize_application_layer()
    initialize_presentation_layer()

    # ========== 메인 윈도우 생성 ==========
    window = MainWindow()

    # ========== 활성화 요청 시그널 연결 ==========
    def on_activate_requested():
        """다른 인스턴스에서 활성화 요청이 들어왔을 때"""
        print("활성화 요청을 받았습니다.")
        window.show()
        window.raise_()
        window.activateWindow()

    instance_manager.activate_requested.connect(on_activate_requested)

    # ========== 리스너 시작 ==========
    instance_manager.start_listener()

    # ========== 메인 윈도우 표시 ==========
    window.show()

    # ========== 종료 시 정리 ==========
    def cleanup_on_exit():
        """애플리케이션 종료 시 리소스 정리"""
        print("리소스 정리 중...")
        instance_manager.cleanup()

    app.aboutToQuit.connect(cleanup_on_exit)

    # ========== 이벤트 루프 실행 ==========
    print(f"{config.APP_NAME} 시작 완료")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

## 주요 통합 포인트

### 1. 애플리케이션 시작 시 (main 함수 초반)
```python
# SingleInstanceManager 생성
instance_manager = SingleInstanceManager()

# 이미 실행 중이면 활성화하고 종료
if instance_manager.is_already_running():
    instance_manager.activate_existing_instance()
    instance_manager.cleanup()
    sys.exit(0)
```

### 2. 메인 윈도우 생성 후
```python
# 활성화 요청 시그널 연결
instance_manager.activate_requested.connect(window.activate)

# 리스너 시작
instance_manager.start_listener()
```

### 3. 애플리케이션 종료 시
```python
# aboutToQuit 시그널에 정리 함수 연결
app.aboutToQuit.connect(instance_manager.cleanup)
```

## MainWindow 메서드 추가 (권장)

MainWindow에 활성화 메서드를 추가하면 더 깔끔하게 통합할 수 있습니다:

```python
class MainWindow(QMainWindow):
    def activate(self):
        """창 활성화 (다른 인스턴스에서 요청 시)"""
        self.show()
        self.raise_()
        self.activateWindow()

        # 최소화 상태였다면 복원
        if self.isMinimized():
            self.showNormal()
```

통합 예시:
```python
instance_manager.activate_requested.connect(window.activate)
```

## 테스트 방법

### 1. 비 GUI 테스트
```bash
python test_single_instance.py --test-only
```

### 2. GUI 테스트 (수동)
1. 첫 번째 터미널에서 애플리케이션 실행
2. 두 번째 터미널에서 동일한 애플리케이션 실행
3. 첫 번째 창이 활성화되고 두 번째 프로세스는 종료되는지 확인

## 동작 원리

### 포트 기반 락
- 포트 65432를 소켓으로 바인딩
- 첫 실행: 바인딩 성공 → 서버 모드
- 중복 실행: 바인딩 실패 → 클라이언트 모드

### 활성화 요청 프로토콜
1. 클라이언트가 서버(기존 인스턴스)에 연결
2. "ACTIVATE" 메시지 전송
3. 서버가 PyQt6 시그널 발생
4. MainWindow가 시그널 수신하여 창 활성화

### Windows 환경 최적화
- `SO_EXCLUSIVEADDRUSE` 옵션 사용 (Windows)
- 배타적 포트 바인딩 보장
- Linux/Mac에서는 기본 동작 사용

## 주의사항

### 1. 포트 충돌
- 포트 65432가 다른 애플리케이션에서 사용 중이면 실패
- 필요 시 `SingleInstanceManager.PORT` 변경 가능

### 2. 방화벽
- localhost(127.0.0.1) 통신이므로 방화벽 문제 없음

### 3. 멀티 유저 환경
- 현재 구현은 같은 사용자만 감지
- 다른 사용자는 별도 인스턴스 실행 가능

### 4. 리소스 정리
- 반드시 `cleanup()` 호출 필요
- `aboutToQuit` 시그널에 연결하여 자동화

## 확장 가능성

### 1. 명령줄 인자 전달
활성화 요청 시 명령줄 인자를 기존 인스턴스로 전달:
```python
# ACTIVATION_MESSAGE에 인자 포함
message = f"ACTIVATE:{' '.join(sys.argv[1:])}".encode('utf-8')
```

### 2. 창 상태 복원
활성화 시 특정 상태로 복원:
```python
def activate(self, restore_state=True):
    self.show()
    self.raise_()
    self.activateWindow()

    if restore_state:
        # 저장된 윈도우 위치/크기 복원
        pass
```

### 3. 멀티 인스턴스 허용
프로필별로 다른 포트 사용:
```python
# config.py
INSTANCE_PORT = 65432 + hash(PROFILE_NAME) % 1000
```

## 관련 파일

- 구현: `src/presentation/system/single_instance.py`
- 테스트: `test_single_instance.py`
- 명세서: `docs/Simple_ToDo_기능_명세서.md` (섹션 8.2)

## 체크리스트

- [x] SingleInstanceManager 클래스 구현
- [x] is_already_running() 메서드 완성
- [x] activate_existing_instance() 메서드 완성
- [x] cleanup() 메서드 완성
- [x] 포트 바인딩 테스트 통과
- [x] 메시지 전송 테스트 통과
- [ ] main.py 통합 (Phase 6-3에서 진행)
- [ ] MainWindow.activate() 메서드 추가 (Phase 6-3에서 진행)
- [ ] E2E 테스트 (Phase 6-3에서 진행)
