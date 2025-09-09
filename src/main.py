"""
Windows TODO 패널 메인 애플리케이션

시스템 트레이 통합, 단일 인스턴스 보장, 완전한 에러 처리를 포함한
완전한 TODO 패널 애플리케이션입니다.

Features:
- 시스템 트레이 통합 (pystray)
- 창 닫기 시 트레이로 최소화
- 트레이 아이콘 클릭으로 창 표시/숨기기
- 우클릭 컨텍스트 메뉴
- 단일 인스턴스 보장
- 동적 트레이 아이콘 생성
- 완전한 에러 처리 및 로깅
"""

import sys
import os
import threading
import time
import socket
import logging
import traceback
from pathlib import Path
from typing import Optional, Callable
import tkinter as tk
from tkinter import messagebox
import webbrowser

try:
    import pystray
    from PIL import Image, ImageDraw, ImageFont
except ImportError as e:
    print(f"필수 패키지가 설치되지 않았습니다: {e}")
    print("다음 명령어로 설치하세요: pip install pystray Pillow")
    sys.exit(1)

try:
    import psutil
except ImportError:
    print("psutil 패키지가 필요합니다: pip install psutil")
    sys.exit(1)

# 로컬 모듈 임포트
try:
    from ui_components import TodoPanelApp
    from todo_manager import TodoManager, TodoManagerError
except ImportError as e:
    print(f"로컬 모듈을 찾을 수 없습니다: {e}")
    print("src 폴더에서 실행하거나 PYTHONPATH를 설정하세요.")
    sys.exit(1)


class LogManager:
    """로깅 관리자"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self._setup_logging()
    
    def _setup_logging(self):
        """로깅 설정"""
        try:
            # 로그 디렉토리 생성
            appdata_local = os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local'))
            log_dir = Path(appdata_local) / 'TodoPanel' / 'logs'
            log_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = log_dir / 'todo_panel.log'
            
            # 로거 설정
            log_level = logging.DEBUG if self.debug else logging.INFO
            logging.basicConfig(
                level=log_level,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_file, encoding='utf-8'),
                    logging.StreamHandler(sys.stdout) if self.debug else logging.NullHandler()
                ]
            )
            
            self.logger = logging.getLogger('TodoPanel')
            self.logger.info("로깅 시스템 초기화 완료")
            
        except Exception as e:
            print(f"로깅 설정 실패: {e}")
            # 기본 로거 사용
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger('TodoPanel')
    
    def info(self, message: str):
        """정보 로그"""
        self.logger.info(message)
    
    def error(self, message: str, exc_info=None):
        """에러 로그"""
        self.logger.error(message, exc_info=exc_info)
    
    def debug(self, message: str):
        """디버그 로그"""
        self.logger.debug(message)


class SingleInstanceManager:
    """단일 인스턴스 보장 관리자"""
    
    def __init__(self, port: int = 65432):
        self.port = port
        self.socket = None
        self.logger = logging.getLogger('TodoPanel.SingleInstance')
    
    def is_already_running(self) -> bool:
        """다른 인스턴스가 실행 중인지 확인"""
        try:
            # 소켓을 사용한 락 메커니즘
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind(('localhost', self.port))
            self.logger.info(f"단일 인스턴스 락 획득 (포트: {self.port})")
            return False
        except OSError:
            self.logger.info(f"다른 인스턴스가 이미 실행 중 (포트: {self.port})")
            return True
    
    def cleanup(self):
        """리소스 정리"""
        if self.socket:
            try:
                self.socket.close()
                self.logger.info("단일 인스턴스 락 해제")
            except:
                pass


class TrayIconGenerator:
    """트레이 아이콘 생성기"""
    
    @staticmethod
    def create_icon(size: int = 64, color: str = "#007acc") -> Image.Image:
        """동적으로 트레이 아이콘 생성"""
        try:
            # 이미지 생성
            image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # 배경 원 그리기
            margin = 4
            circle_bbox = [margin, margin, size - margin, size - margin]
            draw.ellipse(circle_bbox, fill=color, outline="white", width=2)
            
            # 체크 마크 그리기
            check_color = "white"
            check_width = max(2, size // 16)
            
            # 체크 마크 좌표 계산
            center_x, center_y = size // 2, size // 2
            check_size = size // 3
            
            # 체크 마크 그리기 (간단한 V 자 형태)
            check_points = [
                (center_x - check_size // 2, center_y),
                (center_x - check_size // 4, center_y + check_size // 3),
                (center_x + check_size // 2, center_y - check_size // 3)
            ]
            
            for i in range(len(check_points) - 1):
                draw.line([check_points[i], check_points[i + 1]], 
                         fill=check_color, width=check_width)
            
            return image
            
        except Exception as e:
            logging.getLogger('TodoPanel.TrayIcon').error(f"트레이 아이콘 생성 실패: {e}")
            # 기본 아이콘 반환
            return TrayIconGenerator._create_fallback_icon(size)
    
    @staticmethod
    def _create_fallback_icon(size: int = 64) -> Image.Image:
        """기본 아이콘 생성"""
        image = Image.new('RGBA', (size, size), (0, 100, 200, 255))
        draw = ImageDraw.Draw(image)
        
        # 간단한 사각형
        margin = size // 4
        draw.rectangle([margin, margin, size - margin, size - margin], 
                      fill="white", outline="black", width=2)
        
        return image


class SystemTrayManager:
    """시스템 트레이 관리자"""
    
    def __init__(self, on_show: Callable, on_exit: Callable):
        self.on_show = on_show
        self.on_exit = on_exit
        self.logger = logging.getLogger('TodoPanel.SystemTray')
        self.tray_icon = None
        self.icon_image = None
        
        self._create_tray_icon()
    
    def _create_tray_icon(self):
        """트레이 아이콘 생성"""
        try:
            # 아이콘 이미지 생성
            self.icon_image = TrayIconGenerator.create_icon()
            
            # 메뉴 생성
            menu = pystray.Menu(
                pystray.MenuItem("TODO Panel 열기", self._on_show_clicked, default=True),
                pystray.MenuItem("---", None),  # 구분선
                pystray.MenuItem("더 많은 유용한 도구들", self._on_visit_kochim),
                pystray.MenuItem("---", None),  # 구분선
                pystray.MenuItem("종료", self._on_exit_clicked)
            )
            
            # 트레이 아이콘 생성
            self.tray_icon = pystray.Icon(
                "TodoPanel",
                self.icon_image,
                "TODO Panel",
                menu
            )
            
            self.logger.info("시스템 트레이 아이콘 생성 완료")
            
        except Exception as e:
            self.logger.error(f"트레이 아이콘 생성 실패: {e}", exc_info=True)
            raise
    
    def _on_show_clicked(self, icon, item):
        """트레이 메뉴 '열기' 클릭"""
        self.logger.debug("트레이 메뉴 '열기' 클릭됨")
        if self.on_show:
            self.on_show()
    
    def _on_visit_kochim(self, icon, item):
        """트레이 메뉴 'kochim.com 방문' 클릭"""
        try:
            self.logger.info("kochim.com 방문 요청됨")
            webbrowser.open("https://kochim.com")
            self.logger.info("kochim.com이 브라우저에서 열림")
        except Exception as e:
            self.logger.error(f"웹사이트 열기 실패: {e}", exc_info=True)
    
    def _on_exit_clicked(self, icon, item):
        """트레이 메뉴 '종료' 클릭"""
        self.logger.info("애플리케이션 종료 요청됨")
        if self.on_exit:
            self.on_exit()
    
    def run_tray(self):
        """트레이 아이콘 실행 (블로킹)"""
        try:
            if self.tray_icon:
                self.logger.info("시스템 트레이 시작")
                self.tray_icon.run()
        except Exception as e:
            self.logger.error(f"트레이 실행 중 오류: {e}", exc_info=True)
    
    def stop_tray(self):
        """트레이 아이콘 중지"""
        try:
            if self.tray_icon:
                self.tray_icon.stop()
                self.logger.info("시스템 트레이 중지")
        except Exception as e:
            self.logger.error(f"트레이 중지 중 오류: {e}", exc_info=True)


class MainApplication:
    """메인 애플리케이션 관리자"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.log_manager = LogManager(debug)
        self.logger = logging.getLogger('TodoPanel.Main')
        
        # 컴포넌트들
        self.instance_manager = None
        self.tray_manager = None
        self.todo_app = None
        self.tray_thread = None
        
        # 상태 변수
        self.is_running = True
        self.is_window_hidden = False
        
        self.logger.info(f"메인 애플리케이션 초기화 시작 (디버그 모드: {debug})")
    
    def initialize(self) -> bool:
        """애플리케이션 초기화"""
        try:
            # 1. 단일 인스턴스 확인
            self.instance_manager = SingleInstanceManager()
            if self.instance_manager.is_already_running():
                self.logger.info("다른 인스턴스가 이미 실행 중입니다.")
                messagebox.showwarning(
                    "TODO Panel", 
                    "TODO Panel이 이미 실행 중입니다.\n시스템 트레이를 확인해주세요."
                )
                return False
            
            # 2. TODO 앱 생성
            self.todo_app = TodoPanelApp()
            self._setup_todo_app()
            
            # 3. 시스템 트레이 설정
            self.tray_manager = SystemTrayManager(
                on_show=self._show_window,
                on_exit=self._exit_application
            )
            
            self.logger.info("애플리케이션 초기화 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"애플리케이션 초기화 실패: {e}", exc_info=True)
            messagebox.showerror("초기화 오류", f"애플리케이션 초기화에 실패했습니다:\n{e}")
            return False
    
    def _setup_todo_app(self):
        """TODO 앱 설정"""
        if not self.todo_app:
            return
        
        # 창 닫기 이벤트를 트레이로 최소화로 변경
        self.todo_app.root.protocol("WM_DELETE_WINDOW", self._hide_to_tray)
        
        # 윈도우 아이콘 설정 (가능한 경우)
        self._set_window_icon()
        
        # 창 상태 이벤트 바인딩
        self.todo_app.root.bind('<Unmap>', self._on_window_unmap)
        self.todo_app.root.bind('<Map>', self._on_window_map)
        
        self.logger.info("TODO 앱 설정 완료")
    
    def _set_window_icon(self):
        """윈도우 아이콘 설정"""
        try:
            # PIL 이미지를 tkinter에서 사용할 수 있는 형태로 변환
            icon_image = TrayIconGenerator.create_icon(32)
            
            # 임시 파일로 저장 후 아이콘 설정 (Windows에서 동작하는 방법)
            temp_icon_path = Path.cwd() / "temp_icon.ico"
            icon_image.save(temp_icon_path, format='ICO')
            
            self.todo_app.root.iconbitmap(str(temp_icon_path))
            
            # 임시 파일 삭제
            try:
                temp_icon_path.unlink()
            except:
                pass
                
        except Exception as e:
            self.logger.debug(f"윈도우 아이콘 설정 실패 (무시됨): {e}")
    
    def _hide_to_tray(self):
        """창을 트레이로 숨기기"""
        try:
            self.todo_app.root.withdraw()
            self.is_window_hidden = True
            self.logger.debug("창이 트레이로 숨겨짐")
            
            # 처음 숨길 때 알림 표시
            if hasattr(self, '_first_hide') and not self._first_hide:
                self._show_tray_notification()
                self._first_hide = True
                
        except Exception as e:
            self.logger.error(f"창 숨기기 실패: {e}", exc_info=True)
    
    def _show_window(self):
        """창 표시"""
        try:
            if self.is_window_hidden:
                self.todo_app.root.deiconify()
                self.todo_app.root.lift()
                self.todo_app.root.focus_force()
                self.is_window_hidden = False
                self.logger.debug("창이 표시됨")
            else:
                # 이미 보이는 경우 포커스만
                self.todo_app.root.lift()
                self.todo_app.root.focus_force()
                
        except Exception as e:
            self.logger.error(f"창 표시 실패: {e}", exc_info=True)
    
    def _show_tray_notification(self):
        """트레이 알림 표시"""
        try:
            if hasattr(self.tray_manager, 'tray_icon') and self.tray_manager.tray_icon:
                # 간단한 방법으로 알림 (시스템 지원 여부에 따라 동작)
                pass
        except Exception as e:
            self.logger.debug(f"트레이 알림 표시 실패: {e}")
    
    def _on_window_unmap(self, event):
        """윈도우가 숨겨질 때"""
        if event.widget == self.todo_app.root:
            self.is_window_hidden = True
    
    def _on_window_map(self, event):
        """윈도우가 표시될 때"""
        if event.widget == self.todo_app.root:
            self.is_window_hidden = False
    
    def _exit_application(self):
        """애플리케이션 종료"""
        try:
            self.logger.info("애플리케이션 종료 시작")
            self.is_running = False
            
            # 트레이 중지
            if self.tray_manager:
                self.tray_manager.stop_tray()
            
            # TODO 앱 종료
            if self.todo_app and self.todo_app.root:
                self.todo_app.root.quit()
                self.todo_app.root.destroy()
            
            # 단일 인스턴스 매니저 정리
            if self.instance_manager:
                self.instance_manager.cleanup()
            
            self.logger.info("애플리케이션 종료 완료")
            
        except Exception as e:
            self.logger.error(f"애플리케이션 종료 중 오류: {e}", exc_info=True)
        finally:
            # 강제 종료
            sys.exit(0)
    
    def run(self):
        """애플리케이션 실행"""
        try:
            # 초기화
            if not self.initialize():
                return
            
            # 트레이 아이콘을 별도 스레드에서 실행
            self.tray_thread = threading.Thread(
                target=self.tray_manager.run_tray,
                daemon=True
            )
            self.tray_thread.start()
            
            # 처음 숨기기 플래그 초기화
            self._first_hide = False
            
            # 메인 GUI 루프 실행
            self.logger.info("메인 애플리케이션 루프 시작")
            self.todo_app.run()
            
        except KeyboardInterrupt:
            self.logger.info("키보드 인터럽트로 종료")
        except Exception as e:
            self.logger.error(f"애플리케이션 실행 중 오류: {e}", exc_info=True)
            messagebox.showerror("실행 오류", f"애플리케이션 실행 중 오류가 발생했습니다:\n{e}")
        finally:
            self._exit_application()


def main():
    """메인 함수"""
    # 디버그 모드 확인
    debug_mode = '--debug' in sys.argv or '-d' in sys.argv
    
    try:
        print("=== Windows TODO Panel 시작 ===")
        if debug_mode:
            print("디버그 모드로 실행됩니다.")
        
        # 메인 애플리케이션 생성 및 실행
        app = MainApplication(debug=debug_mode)
        app.run()
        
    except Exception as e:
        print(f"치명적 오류: {e}")
        traceback.print_exc()
        
        # GUI 오류 표시 (가능한 경우)
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("치명적 오류", f"애플리케이션을 시작할 수 없습니다:\n{e}")
            root.destroy()
        except:
            pass
        
        sys.exit(1)


if __name__ == "__main__":
    main()