"""
Settings Manager - 설정 관리 전담 모듈 (DRY+CLEAN+Simple 원칙 적용)
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Phase 4A: 새로운 인터페이스 import
from ..interfaces.manager_interfaces import IManagerContainer, ISettingsManager

# Phase 4B: 에러 처리 및 로깅 유틸리티 import
from ..utils.error_handling import SettingsError, ensure_file_path, safe_execute, safe_ui_operation
from ..utils.logging_config import get_logger


class SettingsManager(ISettingsManager):
    """애플리케이션 설정 저장/로드 관리자 (Phase 4A: ISettingsManager 구현)"""

    def __init__(self, app_instance: IManagerContainer) -> None:
        """
        Args:
            app_instance: TodoPanelApp 인스턴스 (의존성 주입)
        """
        self.app: IManagerContainer = app_instance
        self._config_file_path: Optional[Path] = None  # 캐시된 경로
        self.logger = get_logger(__name__)

    @safe_execute("설정 파일 경로 계산 중 오류 발생")
    def get_config_file_path(self) -> Path:
        """설정 파일 경로를 TodoManager와 동일한 로직으로 계산 (DRY+통일성 원칙 적용)"""
        if self._config_file_path is not None:
            return self._config_file_path

        try:
            # TodoManager와 동일한 경로 계산 로직 (data.json과 ui_settings.json 같은 폴더)
            if getattr(sys, "frozen", False):
                # PyInstaller로 빌드된 exe 실행 중
                app_dir = Path(sys.executable).parent
            else:
                # 개발 환경에서 실행 중 - TodoManager와 동일하게 프로젝트 루트 사용
                app_dir = Path(__file__).parent.parent.parent.parent  # src의 상위 디렉토리

            config_dir = app_dir / "TodoPanel_Data"
            config_dir.mkdir(parents=True, exist_ok=True)

            self._config_file_path = config_dir / "ui_settings.json"
            return self._config_file_path

        except Exception as path_error:
            # 폴백: 기존 방식 사용
            print(f"[WARNING] 설정 경로 설정 실패, 기존 방식 사용: {path_error}")
            config_dir = Path(os.path.expanduser("~")) / "AppData" / "Local" / "TodoPanel"
            config_dir.mkdir(parents=True, exist_ok=True)
            self._config_file_path = config_dir / "ui_settings.json"
            return self._config_file_path

    @safe_execute("설정 파일 로드 중 오류 발생")
    def _load_config_file(self) -> Dict[str, Any]:
        """공통 설정 파일 로드 로직 (DRY 원칙)"""
        config_file = self.get_config_file_path()
        settings = {}

        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)
            except Exception as e:
                print(f"[WARNING] 설정 파일 로드 실패: {e}")
                settings = {}

        return settings

    @safe_execute("설정 파일 저장 중 오류 발생")
    def _save_config_file(self, settings: Dict[str, Any]) -> bool:
        """공통 설정 파일 저장 로직 (DRY 원칙)"""
        try:
            config_file = self.get_config_file_path()

            # 최종 저장 시간 업데이트
            settings["last_updated"] = datetime.now().isoformat()

            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"[ERROR] 설정 파일 저장 실패: {e}")
            return False

    @safe_execute("설정 저장 중 오류 발생")
    def save_setting(self, key: str, value: Any) -> bool:
        """제네릭 설정 저장 메서드 (DRY 원칙)"""
        settings = self._load_config_file()
        settings[key] = value
        return self._save_config_file(settings)

    def load_setting(self, key: str, default: Any = None) -> Any:
        """제네릭 설정 로드 메서드 (DRY 원칙)"""
        settings = self._load_config_file()
        return settings.get(key, default)

    @safe_execute("모든 UI 설정 저장 중 오류 발생")
    def save_all_ui_settings(self) -> None:
        """모든 UI 설정을 통합 저장 (분할 비율 + 정렬 설정)"""
        try:
            print(f"[DEBUG] UI 설정 파일 경로: {self.get_config_file_path()}")

            # 기존 설정 로드
            settings = self._load_config_file()

            # 1. 분할 비율 저장
            total_height = self.app.sections_paned_window.winfo_height()
            if total_height >= 50:  # 유효한 크기인 경우에만 저장
                sash_coord = self.app.sections_paned_window.sash_coord(0)
                pending_height = sash_coord[1] if sash_coord else total_height * 0.7
                ratio = max(0.1, min(0.9, pending_height / total_height))
                settings["paned_window_ratio"] = ratio
                print(f"[DEBUG] 분할 비율 저장: {ratio:.2f}")

            # 2. 정렬 설정 저장
            if hasattr(self.app, "sort_manager") and self.app.sort_manager:
                sort_info_before = self.app.sort_manager.get_current_sort_info()
                success = self.app.sort_manager.save_settings(settings)
                if success:
                    sort_settings = settings.get("sort_settings", {})
                    print(
                        f"[DEBUG] 정렬 설정 저장 성공: {sort_settings.get('sort_criteria', 'N/A')} {sort_settings.get('sort_direction', 'N/A')}"
                    )
                else:
                    print("[WARNING] 정렬 설정 저장 실패")
            else:
                print("[WARNING] SortManager를 찾을 수 없음")

            # 3. 설정 파일에 저장
            success = self._save_config_file(settings)

            if success:
                # 4. 저장 검증
                try:
                    config_file = self.get_config_file_path()
                    with open(config_file, "r", encoding="utf-8") as f:
                        saved_settings = json.load(f)
                    sort_verified = "sort_settings" in saved_settings
                    print(
                        f"[DEBUG] 설정 저장 검증: 파일크기={config_file.stat().st_size}B, 정렬설정={'포함' if sort_verified else '누락'}"
                    )
                except Exception as verify_error:
                    print(f"[WARNING] 저장 검증 실패: {verify_error}")

                print(f"[DEBUG] 모든 UI 설정 저장 완료: {config_file}")
            else:
                print("[ERROR] UI 설정 저장 실패")

        except Exception as e:
            print(f"[ERROR] UI 설정 저장 실패: {e}")
            # 재시도 로직
            import traceback

            print(f"[ERROR] 스택 트레이스: {traceback.format_exc()}")

    @safe_ui_operation()
    def save_pane_ratio(self) -> None:
        """현재 분할 비율을 사용자 설정에 저장 (DRY 적용 단순화)"""
        try:
            # 현재 분할 비율 계산
            total_height = self.app.sections_paned_window.winfo_height()
            if total_height < 50:
                return  # 너무 작으면 저장하지 않음

            # 첫 번째 패널(진행중 할일)의 높이 가져오기
            sash_coord = self.app.sections_paned_window.sash_coord(0)
            pending_height = sash_coord[1] if sash_coord else total_height * 0.7

            # 비율 계산 (0.1 ~ 0.9 범위로 제한)
            ratio = max(0.1, min(0.9, pending_height / total_height))

            # 공통 메서드 활용 (DRY 원칙)
            success = self.save_setting("paned_window_ratio", ratio)

            if success and hasattr(self.app, "_debug") and self.app._debug:
                print(f"[DEBUG] 분할 비율 저장됨: {ratio:.2f}")

        except Exception as e:
            if hasattr(self.app, "_debug") and self.app._debug:
                print(f"[DEBUG] 분할 비율 저장 실패: {e}")

    @safe_ui_operation()
    def load_sort_settings(self) -> None:
        """저장된 정렬 설정을 불러와서 SortManager에 적용 (DRY 적용 단순화)"""
        try:
            config_file = self.get_config_file_path()
            print(f"[DEBUG] UI 설정 파일 로드 경로: {config_file}")

            if not config_file.exists():
                print("[DEBUG] 설정 파일 없음, 기본 정렬 설정 사용")
                return

            settings = self._load_config_file()

            # SortManager에 설정 로드
            if hasattr(self.app, "sort_manager") and self.app.sort_manager:
                success = self.app.sort_manager.load_settings(settings)
                if success:
                    print("[DEBUG] 정렬 설정 로드 성공")

                    # 정렬 드롭다운 UI 업데이트
                    if hasattr(self.app, "sort_dropdown") and self.app.sort_dropdown:
                        self.app.sort_dropdown.update_display()
                        print("[DEBUG] 정렬 드롭다운 UI 업데이트 완료")
                else:
                    print("[WARNING] 정렬 설정 로드 실패, 기본값 사용")

        except Exception as e:
            print(f"[ERROR] 정렬 설정 로드 중 오류: {e}")
            # 오류 시 기본값 사용 (SortManager는 이미 기본값으로 초기화됨)

    def load_pane_ratio(self) -> float:
        """저장된 분할 비율을 불러오기 (기본값: 0.8) - DRY 적용 단순화"""
        try:
            config_file = self.get_config_file_path()
            print(f"[DEBUG] 설정 파일 경로: {config_file}")

            if not config_file.exists():
                print(f"[DEBUG] 설정 파일 없음, 기본값 0.8 사용")
                return 0.8  # 기본값

            # 공통 메서드 활용 (DRY 원칙)
            ratio = self.load_setting("paned_window_ratio", 0.8)
            print(f"[DEBUG] 원본 비율값: {ratio}")

            # 유효한 범위인지 검증 (0.1 ~ 0.9)
            ratio = max(0.1, min(0.9, ratio))
            print(f"[DEBUG] 검증된 비율값: {ratio}")

            return ratio

        except Exception as e:
            print(f"[DEBUG] 분할 비율 로드 실패, 기본값 사용: {e}")
            return 0.8  # 기본값
