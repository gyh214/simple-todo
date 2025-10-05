"""
Windows TODO 패널 메인 애플리케이션 - CLEAN 아키텍처 통합

🏛️ CLEAN Architecture Application Entry Point:
==============================================
완전한 의존성 역전과 시스템 트레이 통합을 가진 TODO 패널 애플리케이션입니다.
모든 의존성은 DI Container에서 해결되며 Interface를 통해서만 상호작용합니다.

🎯 핵심 기능:
============
- CLEAN 아키텍처 완전 구현
- 의존성 주입 컨테이너 (DI Container)
- 시스템 트레이 통합 (pystray)
- 단일 인스턴스 보장
- 창 닫기 시 트레이로 최소화
- 동적 트레이 아이콘 생성
- 완전한 에러 처리 및 로깅
- Magic UI 스타일링

🔄 아키텍처 플로우:
==================
Main → Bootstrap → DI Container → Service Injection → UI Creation

🚀 실행 방법:
============
python main.py [--debug] [--reset]
"""

import sys
import os
import threading
import time
import socket
import logging
import traceback
import argparse
from pathlib import Path
from typing import Optional, Callable
import tkinter as tk

# 필수 패키지 확인
try:
    import pystray
    from PIL import Image, ImageDraw, ImageFont
    import psutil
except ImportError as e:
    print(f"필수 패키지가 설치되지 않았습니다: {e}")
    print("다음 명령어로 설치하세요: pip install pystray Pillow psutil")
    sys.exit(1)

# CLEAN 아키텍처 모듈들
try:
    from app_bootstrap import create_application, reset_application
    from ui.main_app import TodoPanelApp
    from interfaces import ITodoService, INotificationService
except ImportError as e:
    print(f"CLEAN 아키텍처 모듈을 찾을 수 없습니다: {e}")
    print("src 폴더에서 실행하거나 PYTHONPATH를 설정하세요.")
    print("현재 경로:", os.getcwd())
    print("Python 경로:", sys.path)
    sys.exit(1)

# 로깅 설정
def setup_logging(debug: bool = False):
    """로깅 시스템 설정"""
    log_level = logging.DEBUG if debug else logging.INFO

    # 로그 디렉토리 생성
    log_dir = Path(os.path.expanduser("~")) / "AppData" / "Local" / "TodoPanel" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # 로그 파일 경로
    log_file = log_dir / "todo_panel.log"

    # 로깅 포맷 설정
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # 루트 로거 설정
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info(f"로깅 시스템 초기화 완료 - 레벨: {log_level}")
    logger.info(f"로그 파일: {log_file}")

    return logger


class SingleInstanceChecker:
    """
    단일 인스턴스 확인자

    🔒 동시 실행 방지:
    =================
    포트 기반 락을 사용하여 동일한 애플리케이션이
    여러 번 실행되는 것을 방지합니다.
    """

    def __init__(self, port: int = 65432):
        self.port = port
        self.socket = None

    def is_running(self) -> bool:
        """다른 인스턴스가 실행 중인지 확인"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind(('127.0.0.1', self.port))
            return False  # 바인딩 성공 = 다른 인스턴스 없음
        except OSError:
            return True  # 바인딩 실패 = 다른 인스턴스 실행 중

    def cleanup(self):
        """리소스 정리"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass


class TrayIconManager:
    """
    시스템 트레이 아이콘 관리자

    🎨 동적 아이콘 생성:
    ===================
    PIL을 사용하여 런타임에 아이콘을 생성하고
    TODO 상태에 따라 동적으로 업데이트할 수 있습니다.
    """

    def __init__(self, app_controller: 'MainApplication'):
        self.app_controller = app_controller
        self.tray = None
        self.logger = logging.getLogger(self.__class__.__name__)

    def create_icon_image(self) -> Image.Image:
        """트레이 아이콘 이미지 생성"""
        try:
            # 32x32 아이콘 생성
            img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            # 배경 원 그리기
            draw.ellipse([4, 4, 28, 28], fill=(33, 150, 243, 255), outline=(21, 101, 192, 255))

            # 체크마크 그리기
            draw.line([(10, 16), (14, 20), (22, 12)], fill=(255, 255, 255, 255), width=2)

            return img
        except Exception as e:
            self.logger.error(f"아이콘 생성 실패: {e}")
            # 폴백: 간단한 아이콘
            img = Image.new('RGBA', (32, 32), (33, 150, 243, 255))
            return img

    def create_context_menu(self) -> pystray.Menu:
        """컨텍스트 메뉴 생성"""
        return pystray.Menu(
            pystray.MenuItem(
                "TODO Panel 표시",
                self.app_controller.show_window,
                default=True
            ),
            pystray.MenuItem(
                "TODO Panel 숨기기",
                self.app_controller.hide_window
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "더 많은 유용한 도구들",
                self._open_website
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "종료",
                self.app_controller.quit_application
            )
        )

    def _open_website(self, icon, item):
        """웹사이트 열기"""
        import webbrowser
        webbrowser.open("https://kochim.com")
        self.logger.info("kochim.com 웹사이트 열기")

    def setup_tray(self):
        """시스템 트레이 설정"""
        try:
            icon_image = self.create_icon_image()
            menu = self.create_context_menu()

            self.tray = pystray.Icon(
                name="TodoPanel",
                icon=icon_image,
                title="TODO Panel - CLEAN Architecture",
                menu=menu
            )

            # 트레이 아이콘 클릭 이벤트
            self.tray.left_click = self.app_controller.toggle_window

            self.logger.info("시스템 트레이 아이콘 설정 완료")

        except Exception as e:
            self.logger.error(f"트레이 아이콘 설정 실패: {e}")
            raise

    def run_tray(self):
        """트레이 아이콘 실행 (별도 스레드)"""
        try:
            if self.tray:
                self.logger.info("시스템 트레이 실행 시작")
                self.tray.run()
            else:
                self.logger.error("트레이 아이콘이 설정되지 않았습니다")
        except Exception as e:
            self.logger.error(f"트레이 실행 중 오류: {e}")

    def stop_tray(self):
        """트레이 아이콘 중지"""
        try:
            if self.tray:
                self.tray.stop()
                self.logger.info("시스템 트레이 중지")
        except Exception as e:
            self.logger.error(f"트레이 중지 중 오류: {e}")


class MainApplication:
    """
    CLEAN 아키텍처 메인 애플리케이션 컨트롤러

    🏛️ 애플리케이션 조율자:
    =======================
    UI, 비즈니스 로직, Infrastructure의 생명주기를 관리하고
    시스템 트레이와의 통합을 담당합니다.

    🎯 책임 분리:
    ============
    - UI 생명주기 관리
    - 시스템 트레이 통합
    - 애플리케이션 설정 관리
    - 에러 처리 및 로깅
    """

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.logger = logging.getLogger(self.__class__.__name__)

        # 핵심 컴포넌트들
        self.todo_app: Optional[TodoPanelApp] = None
        self.root: Optional[tk.Tk] = None
        self.tray_manager: Optional[TrayIconManager] = None
        self.instance_checker: Optional[SingleInstanceChecker] = None

        # 상태 관리
        self.is_visible = True
        self.is_shutting_down = False

        self.logger.info("MainApplication 초기화")

    def initialize(self) -> bool:
        """
        애플리케이션 초기화

        🚀 초기화 순서:
        ==============
        1. 단일 인스턴스 확인
        2. CLEAN 아키텍처 애플리케이션 생성
        3. 시스템 트레이 설정
        4. 이벤트 바인딩

        Returns:
            초기화 성공 여부
        """
        try:
            # 1. 단일 인스턴스 확인
            self.instance_checker = SingleInstanceChecker()
            if self.instance_checker.is_running():
                self.logger.warning("이미 실행 중인 TODO Panel이 있습니다")
                return False

            # 2. CLEAN 아키텍처 애플리케이션 생성
            self.logger.info("CLEAN 아키텍처 애플리케이션 생성 중...")
            self.todo_app = create_application(debug=self.debug)
            self.root = self.todo_app.root

            # 3. 윈도우 이벤트 바인딩
            self._setup_window_events()

            # 4. 시스템 트레이 설정
            self.tray_manager = TrayIconManager(self)
            self.tray_manager.setup_tray()

            self.logger.info("메인 애플리케이션 초기화 완료")
            return True

        except Exception as e:
            self.logger.error(f"애플리케이션 초기화 실패: {e}")
            self.logger.error(traceback.format_exc())
            return False

    def _setup_window_events(self):
        """윈도우 이벤트 설정"""
        if self.root:
            # 창 닫기 이벤트 (트레이로 최소화)
            self.root.protocol("WM_DELETE_WINDOW", self.on_window_closing)

            # 창 상태 변경 이벤트
            self.root.bind("<Unmap>", self.on_window_unmap)
            self.root.bind("<Map>", self.on_window_map)

    def run(self):
        """
        애플리케이션 실행

        🔄 실행 플로우:
        ==============
        1. 트레이 아이콘 스레드 시작
        2. Tkinter 메인 루프 실행
        3. 종료 시 리소스 정리
        """
        try:
            # 트레이 아이콘을 별도 스레드에서 실행
            if self.tray_manager:
                tray_thread = threading.Thread(
                    target=self.tray_manager.run_tray,
                    daemon=True
                )
                tray_thread.start()
                self.logger.info("트레이 아이콘 스레드 시작")

            # 메인 UI 실행
            if self.todo_app:
                self.logger.info("TODO Panel 메인 루프 시작")
                self.todo_app.run()
            else:
                self.logger.error("TODO 애플리케이션이 초기화되지 않았습니다")

        except Exception as e:
            self.logger.error(f"애플리케이션 실행 중 오류: {e}")
            self.logger.error(traceback.format_exc())
        finally:
            self.cleanup()

    def on_window_closing(self):
        """창 닫기 이벤트 처리 (트레이로 최소화)"""
        self.logger.debug("창 닫기 요청 - 트레이로 최소화")
        self.hide_window()

    def on_window_unmap(self, event):
        """창 숨김 이벤트"""
        if event.widget == self.root:
            self.is_visible = False
            self.logger.debug("창이 숨겨짐")

    def on_window_map(self, event):
        """창 표시 이벤트"""
        if event.widget == self.root:
            self.is_visible = True
            self.logger.debug("창이 표시됨")

    def show_window(self, icon=None, item=None):
        """창 표시"""
        if self.root and not self.is_shutting_down:
            try:
                self.root.deiconify()
                self.root.lift()
                self.root.focus_force()
                self.is_visible = True
                self.logger.debug("창 표시")
            except Exception as e:
                self.logger.error(f"창 표시 실패: {e}")

    def hide_window(self, icon=None, item=None):
        """창 숨기기"""
        if self.root and not self.is_shutting_down:
            try:
                self.root.withdraw()
                self.is_visible = False
                self.logger.debug("창 숨김")
            except Exception as e:
                self.logger.error(f"창 숨김 실패: {e}")

    def toggle_window(self, icon=None, item=None):
        """창 표시/숨김 토글"""
        if self.is_visible:
            self.hide_window()
        else:
            self.show_window()

    def quit_application(self, icon=None, item=None):
        """애플리케이션 완전 종료"""
        self.logger.info("애플리케이션 종료 요청")
        self.is_shutting_down = True

        try:
            # 트레이 아이콘 중지
            if self.tray_manager:
                self.tray_manager.stop_tray()

            # Tkinter 종료
            if self.root:
                self.root.quit()
                self.root.destroy()

        except Exception as e:
            self.logger.error(f"종료 중 오류: {e}")

    def cleanup(self):
        """리소스 정리"""
        self.logger.info("리소스 정리 시작")

        try:
            # 단일 인스턴스 체커 정리
            if self.instance_checker:
                self.instance_checker.cleanup()

            # CLEAN 아키텍처 정리
            reset_application()

            self.logger.info("리소스 정리 완료")

        except Exception as e:
            self.logger.error(f"리소스 정리 중 오류: {e}")


def parse_arguments():
    """명령행 인수 파싱"""
    parser = argparse.ArgumentParser(
        description="TODO Panel - CLEAN Architecture",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python main.py               # 일반 실행
  python main.py --debug       # 디버그 모드
  python main.py --reset       # 설정 리셋 후 실행
        """
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='디버그 모드로 실행 (상세한 로깅)'
    )

    parser.add_argument(
        '--reset',
        action='store_true',
        help='애플리케이션 설정 리셋'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='TODO Panel v2.0 - CLEAN Architecture'
    )

    return parser.parse_args()


def check_system_requirements():
    """시스템 요구사항 확인"""
    # Python 버전 확인
    if sys.version_info < (3, 8):
        print("Python 3.8 이상이 필요합니다")
        return False

    # Windows 확인
    if os.name != 'nt':
        print("이 애플리케이션은 Windows 환경에서만 실행됩니다")
        return False

    return True


def main():
    """메인 진입점"""
    print("TODO Panel - CLEAN Architecture")
    print("=" * 50)

    # 시스템 요구사항 확인
    if not check_system_requirements():
        sys.exit(1)

    # 명령행 인수 파싱
    args = parse_arguments()

    # 로깅 설정
    logger = setup_logging(debug=args.debug)

    try:
        # 설정 리셋 처리
        if args.reset:
            logger.info("애플리케이션 설정 리셋")
            reset_application()

        # 메인 애플리케이션 생성 및 초기화
        app = MainApplication(debug=args.debug)

        if not app.initialize():
            logger.error("애플리케이션 초기화 실패")
            sys.exit(1)

        # 애플리케이션 실행
        logger.info("🚀 TODO Panel 실행 시작")
        app.run()

    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단됨")
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        logger.info("TODO Panel 종료")


if __name__ == "__main__":
    main()