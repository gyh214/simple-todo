# -*- coding: utf-8 -*-
"""
Simple ToDo 빌드 스크립트

PyInstaller를 사용해서 Simple ToDo 애플리케이션을
단일 exe 파일로 빌드합니다.

기능:
- PyInstaller를 사용한 단일 exe 파일 생성
- --onefile 옵션 (단일 파일)
- --windowed 옵션 (콘솔 창 숨김)
- 아이콘 파일 적용
- 버전 정보 추가
- 빌드 전 이전 파일 정리
- 빌드 후 exe 파일 정보 출력

사용법:
python build.py [--debug] [--keep-temp]

옵션:
--debug     : 디버그 모드로 빌드 (콘솔 표시)
--keep-temp : 임시 파일 유지 (디버깅용)
"""

import sys
import os
import subprocess
import shutil
import time
from pathlib import Path
from typing import Optional, List
import argparse


class BuildManager:
    """빌드 관리자"""

    def __init__(self, debug: bool = False, keep_temp: bool = False):
        self.debug = debug
        self.keep_temp = keep_temp

        # 경로 설정
        self.root_dir = Path(__file__).parent.resolve()
        self.src_dir = self.root_dir / 'src'
        self.dist_dir = self.root_dir / 'dist'
        self.build_dir = self.root_dir / 'build'
        self.main_script = self.root_dir / 'main.py'
        self.spec_file = self.root_dir / 'simple_todo.spec'
        self.icon_file = self.root_dir / 'simple-todo.ico'
        self.version_file = self.root_dir / 'version_info.txt'
        self.output_exe = self.dist_dir / 'SimpleTodo.exe'

        # 빌드 시작 시간
        self.start_time = time.time()

    def log(self, message: str, level: str = "INFO"):
        """로그 출력"""
        timestamp = time.strftime("%H:%M:%S")
        if level == "ERROR":
            print(f"[{timestamp}] [ERROR] {message}")
        elif level == "WARNING":
            print(f"[{timestamp}] [WARNING] {message}")
        elif level == "SUCCESS":
            print(f"[{timestamp}] [SUCCESS] {message}")
        else:
            print(f"[{timestamp}] [INFO] {message}")

    def check_requirements(self) -> bool:
        """빌드 요구사항 확인"""
        self.log("빌드 요구사항 확인 중...")

        # Python 버전 확인
        python_version = sys.version_info
        if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 7):
            self.log(f"Python 3.7 이상이 필요합니다. 현재: {python_version.major}.{python_version.minor}", "ERROR")
            return False

        self.log(f"Python {python_version.major}.{python_version.minor}.{python_version.micro} 확인됨")

        # PyInstaller 설치 확인
        try:
            import PyInstaller
            self.log(f"PyInstaller {PyInstaller.__version__} 확인됨")
        except ImportError:
            self.log("PyInstaller가 설치되지 않았습니다.", "ERROR")
            self.log("다음 명령어로 설치하세요: pip install pyinstaller", "ERROR")
            return False

        # 필수 파일 확인
        required_files = [
            (self.main_script, "메인 스크립트"),
            (self.src_dir, "소스 디렉토리"),
            (self.spec_file, "PyInstaller spec 파일")
        ]

        for file_path, description in required_files:
            if not file_path.exists():
                self.log(f"{description}를 찾을 수 없습니다: {file_path}", "ERROR")
                return False
            self.log(f"{description} 확인됨: {file_path}")

        # 선택적 파일 확인
        optional_files = [
            (self.icon_file, "아이콘 파일"),
            (self.version_file, "버전 정보 파일")
        ]

        for file_path, description in optional_files:
            if file_path.exists():
                self.log(f"{description} 확인됨: {file_path}")
            else:
                self.log(f"{description}를 찾을 수 없습니다 (선택사항): {file_path}", "WARNING")

        return True

    def clean_previous_builds(self) -> bool:
        """이전 빌드 파일 정리"""
        self.log("이전 빌드 파일 정리 중...")

        try:
            # dist 디렉토리 정리
            if self.dist_dir.exists():
                shutil.rmtree(self.dist_dir)
                self.log("dist 디렉토리 삭제됨")

            # build 디렉토리 정리
            if self.build_dir.exists():
                shutil.rmtree(self.build_dir)
                self.log("build 디렉토리 삭제됨")

            # 이전 spec 파일에서 생성된 임시 파일들 정리
            temp_files = [
                self.root_dir / 'temp_icon.ico'
            ]

            for temp_file in temp_files:
                if temp_file.exists():
                    try:
                        temp_file.unlink()
                        self.log(f"임시 파일 삭제됨: {temp_file}")
                    except:
                        pass

            self.log("이전 빌드 파일 정리 완료", "SUCCESS")
            return True

        except Exception as e:
            self.log(f"빌드 파일 정리 실패: {e}", "ERROR")
            return False

    def run_pyinstaller(self) -> bool:
        """PyInstaller 실행"""
        self.log("PyInstaller 빌드 시작...")

        try:
            # spec 파일을 사용하여 빌드
            self.log(f"spec 파일 사용: {self.spec_file}")
            cmd = ['pyinstaller', str(self.spec_file)]

            # 명령어 출력
            self.log(f"실행 명령어: {' '.join(cmd)}")

            # 작업 디렉토리를 프로젝트 루트로 설정
            os.chdir(self.root_dir)

            # PyInstaller 실행
            self.log("PyInstaller 실행 중... (시간이 걸릴 수 있습니다)")
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')

            # 결과 확인
            if result.returncode == 0:
                self.log("PyInstaller 빌드 성공", "SUCCESS")
                if self.debug and result.stdout:
                    self.log("빌드 출력:")
                    print(result.stdout)
                return True
            else:
                self.log("PyInstaller 빌드 실패", "ERROR")
                if result.stderr:
                    self.log("오류 출력:")
                    print(result.stderr)
                if result.stdout:
                    self.log("표준 출력:")
                    print(result.stdout)
                return False

        except Exception as e:
            self.log(f"PyInstaller 실행 중 오류: {e}", "ERROR")
            return False

    def verify_build_result(self) -> bool:
        """빌드 결과 확인"""
        self.log("빌드 결과 확인 중...")

        # exe 파일 존재 확인
        if not self.output_exe.exists():
            self.log(f"exe 파일을 찾을 수 없습니다: {self.output_exe}", "ERROR")
            return False

        # 파일 크기 확인
        file_size = self.output_exe.stat().st_size
        size_mb = file_size / 1024 / 1024

        if size_mb < 1:
            self.log(f"exe 파일이 너무 작습니다: {size_mb:.1f} MB", "WARNING")

        # 실행 파일 권한 확인 (Windows에서는 기본적으로 실행 가능)
        if not os.access(self.output_exe, os.X_OK):
            self.log("exe 파일에 실행 권한이 없습니다", "WARNING")

        self.log(f"exe 파일 생성 확인: {self.output_exe}", "SUCCESS")
        self.log(f"파일 크기: {size_mb:.1f} MB ({file_size:,} bytes)")

        return True

    def copy_icon_to_dist(self) -> bool:
        """아이콘 파일을 dist 폴더로 복사 (런타임 사용)"""
        self.log("아이콘 파일 복사 중...")

        try:
            # SimpleTodo.ico 파일 확인
            if not self.icon_file.exists():
                self.log(f"아이콘 파일을 찾을 수 없습니다: {self.icon_file}", "WARNING")
                return False

            # dist 폴더에 복사
            dist_icon = self.dist_dir / 'SimpleTodo.ico'
            shutil.copy2(self.icon_file, dist_icon)

            self.log(f"아이콘 파일 복사 완료: {dist_icon}", "SUCCESS")
            return True

        except Exception as e:
            self.log(f"아이콘 파일 복사 실패: {e}", "WARNING")
            return False

    def cleanup_temp_files(self) -> bool:
        """임시 파일 정리"""
        if self.keep_temp:
            self.log("임시 파일 유지 (--keep-temp 옵션)")
            return True

        self.log("임시 파일 정리 중...")

        try:
            # build 디렉토리 정리
            if self.build_dir.exists():
                shutil.rmtree(self.build_dir)
                self.log("build 디렉토리 정리됨")

            # 기타 임시 파일들
            temp_patterns = [
                '*.spec~',
                'logdict*.log',
                'warn*.txt'
            ]

            for pattern in temp_patterns:
                for file_path in self.root_dir.glob(pattern):
                    try:
                        file_path.unlink()
                        self.log(f"임시 파일 삭제: {file_path}")
                    except:
                        pass

            self.log("임시 파일 정리 완료", "SUCCESS")
            return True

        except Exception as e:
            self.log(f"임시 파일 정리 실패: {e}", "WARNING")
            return False

    def print_build_summary(self):
        """빌드 요약 정보 출력"""
        elapsed_time = time.time() - self.start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)

        print()
        print("=" * 60)
        print("빌드 완료!")
        print("=" * 60)

        if self.output_exe.exists():
            stat = self.output_exe.stat()
            size_mb = stat.st_size / 1024 / 1024

            print(f"출력 파일      : {self.output_exe}")
            print(f"파일 크기      : {size_mb:.1f} MB ({stat.st_size:,} bytes)")
            print(f"수정 시간      : {time.ctime(stat.st_mtime)}")
            print(f"빌드 시간      : {minutes:02d}:{seconds:02d}")

            # 빌드 옵션 정보
            print()
            print("빌드 옵션:")
            print(f"- 디버그 모드  : {'예' if self.debug else '아니오'}")
            print(f"- 임시 파일 유지: {'예' if self.keep_temp else '아니오'}")

            # 사용된 파일들
            print()
            print("사용된 파일:")
            print(f"- 메인 스크립트: {self.main_script}")
            if self.icon_file.exists():
                print(f"- 아이콘 파일  : {self.icon_file}")
            if self.version_file.exists():
                print(f"- 버전 정보    : {self.version_file}")
            if self.spec_file.exists():
                print(f"- Spec 파일    : {self.spec_file}")

        print()
        print("실행 방법:")
        print(f"  {self.output_exe}")
        print()

    def build(self) -> bool:
        """전체 빌드 프로세스 실행"""
        print("=" * 60)
        print("Simple ToDo 빌드 시작")
        print("=" * 60)
        print()

        try:
            # 1. 요구사항 확인
            if not self.check_requirements():
                return False

            # 2. 이전 빌드 정리
            if not self.clean_previous_builds():
                return False

            # 3. PyInstaller 실행
            if not self.run_pyinstaller():
                return False

            # 4. 빌드 결과 확인
            if not self.verify_build_result():
                return False

            # 5. 임시 파일 정리
            self.cleanup_temp_files()

            # 6. 빌드 요약 출력
            self.print_build_summary()

            return True

        except KeyboardInterrupt:
            self.log("사용자에 의해 빌드가 중단되었습니다", "WARNING")
            return False
        except Exception as e:
            self.log(f"빌드 중 예상치 못한 오류: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description='Simple ToDo 빌드 스크립트',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  python build.py                   # 기본 빌드
  python build.py --debug           # 디버그 모드로 빌드
  python build.py --keep-temp       # 임시 파일 유지
        """
    )

    parser.add_argument('--debug', action='store_true',
                       help='디버그 모드로 빌드 (상세 출력)')
    parser.add_argument('--keep-temp', action='store_true',
                       help='임시 파일 유지 (디버깅용)')

    args = parser.parse_args()

    # 빌드 매니저 생성
    builder = BuildManager(
        debug=args.debug,
        keep_temp=args.keep_temp
    )

    # 빌드 실행
    success = builder.build()

    # 결과에 따른 종료 코드 반환
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
