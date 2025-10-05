"""링크/경로를 인식하고 클릭 가능하게 만드는 위젯.

명세서 6장 링크 및 경로 인식 구현:
- 웹 링크 자동 감지 및 브라우저 열기
- 파일 경로 자동 감지 및 탐색기/프로그램 열기
- 실행 파일 보안 검증
"""

from PyQt6.QtWidgets import QLabel, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor
import webbrowser
import os
import subprocess
from typing import List, Tuple
from ..utils.link_parser import LinkParser


class RichTextWidget(QLabel):
    """링크/경로를 인식하고 클릭 가능하게 만드는 위젯."""

    # 시그널
    link_clicked = pyqtSignal(str, str)  # (타입, 텍스트)

    # 실행 파일 확장자
    EXECUTABLE_EXTENSIONS = ['.exe', '.bat', '.cmd', '.com', '.scr', '.msi', '.ps1', '.vbs']

    def __init__(self, text: str = "", parent=None):
        """초기화.

        Args:
            text: 표시할 텍스트
            parent: 부모 위젯
        """
        super().__init__(parent)
        self.raw_text = text
        self.links = []

        # Rich Text 포맷 설정
        self.setTextFormat(Qt.TextFormat.RichText)
        self.setOpenExternalLinks(False)  # 수동 처리

        # 링크 클릭 시그널 연결
        self.linkActivated.connect(self._on_link_activated)

        # 커서 변경 (링크 위에서 포인터로 변경)
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

        # 텍스트 업데이트
        self.update_text(text)

    def update_text(self, text: str):
        """텍스트 업데이트 및 링크/경로 HTML 변환.

        Args:
            text: 새로운 텍스트
        """
        self.raw_text = text
        self.links = LinkParser.parse_text(text)

        # HTML 생성
        html = self._convert_to_html(text, self.links)
        self.setText(html)

    def _convert_to_html(self, text: str, links: List[Tuple[str, str, int, int]]) -> str:
        """텍스트를 HTML로 변환 (링크/경로 하이라이트).

        Args:
            text: 원본 텍스트
            links: [(타입, 텍스트, 시작, 끝), ...] 형식의 링크 리스트

        Returns:
            HTML 문자열
        """
        if not links:
            # 링크가 없으면 텍스트만 반환
            return self._escape_html(text)

        # 링크를 <a> 태그로 변환
        result = []
        last_end = 0

        for link_type, link_text, start, end in links:
            # 링크 이전 텍스트 추가
            if start > last_end:
                result.append(self._escape_html(text[last_end:start]))

            # 링크를 <a> 태그로 변환
            # href는 "type:text" 형식으로 인코딩
            href = f"{link_type}:{link_text}"

            # URL과 Path에 따라 다른 스타일 적용
            if link_type == 'url':
                # URL: #CC785C, 밑줄
                result.append(
                    f'<a href="{self._escape_html(href)}" '
                    f'style="color: #CC785C; text-decoration: underline;" '
                    f'data-type="url">'
                    f'{self._escape_html(link_text)}</a>'
                )
            else:  # path
                # Path: #CC785C, 밑줄, opacity 0.8
                result.append(
                    f'<a href="{self._escape_html(href)}" '
                    f'style="color: #CC785C; text-decoration: underline; opacity: 0.8;" '
                    f'data-type="path">'
                    f'{self._escape_html(link_text)}</a>'
                )

            last_end = end

        # 마지막 링크 이후 텍스트 추가
        if last_end < len(text):
            result.append(self._escape_html(text[last_end:]))

        # 스타일 추가
        html = f"""
        <style>
        a[data-type="url"]:hover {{
            color: #E08B6F;
        }}
        a[data-type="path"]:hover {{
            opacity: 1.0;
        }}
        </style>
        {''.join(result)}
        """

        return html

    def _escape_html(self, text: str) -> str:
        """HTML 특수문자 이스케이프.

        Args:
            text: 원본 텍스트

        Returns:
            이스케이프된 텍스트
        """
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))

    def _on_link_activated(self, link_data: str):
        """링크 클릭 처리.

        Args:
            link_data: "type:text" 형식의 링크 데이터
        """
        # link_data 파싱
        if ':' not in link_data:
            return

        link_type, link_text = link_data.split(':', 1)

        # 시그널 발생
        self.link_clicked.emit(link_type, link_text)

        # 타입에 따라 처리
        if link_type == 'url':
            self._open_url(link_text)
        elif link_type == 'path':
            self._open_path(link_text)

    def _open_url(self, url: str):
        """URL을 기본 브라우저에서 열기.

        Args:
            url: 열 URL
        """
        # www.로 시작하면 http:// 추가
        if url.startswith('www.'):
            url = 'http://' + url

        try:
            webbrowser.open(url)
        except Exception as e:
            QMessageBox.warning(
                self,
                "URL 열기 실패",
                f"URL을 열 수 없습니다:\n{url}\n\n오류: {str(e)}"
            )

    def _open_path(self, path: str):
        """파일/폴더 열기.

        Args:
            path: 파일 또는 폴더 경로
        """
        # 경로 존재 확인
        if not os.path.exists(path):
            QMessageBox.warning(
                self,
                "경로 없음",
                f"다음 경로를 찾을 수 없습니다:\n{path}"
            )
            return

        # 실행 파일 검증
        if os.path.isfile(path) and self._is_executable(path):
            if not self._confirm_executable(path):
                return

        # Windows에서 파일/폴더 열기
        try:
            os.startfile(path)
        except Exception as e:
            QMessageBox.warning(
                self,
                "파일 열기 실패",
                f"파일을 열 수 없습니다:\n{path}\n\n오류: {str(e)}"
            )

    def _is_executable(self, file_path: str) -> bool:
        """실행 파일 여부 확인.

        Args:
            file_path: 파일 경로

        Returns:
            실행 파일이면 True
        """
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.EXECUTABLE_EXTENSIONS

    def _confirm_executable(self, file_path: str) -> bool:
        """실행 파일 실행 확인 다이얼로그.

        Args:
            file_path: 실행 파일 경로

        Returns:
            사용자가 확인하면 True
        """
        reply = QMessageBox.warning(
            self,
            "실행 파일 경고",
            f"실행 파일을 열려고 합니다:\n{file_path}\n\n계속하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes

    def get_raw_text(self) -> str:
        """원본 텍스트 반환.

        Returns:
            링크/경로 처리 전 원본 텍스트
        """
        return self.raw_text

    def get_links(self) -> List[Tuple[str, str, int, int]]:
        """추출된 링크 목록 반환.

        Returns:
            [(타입, 텍스트, 시작, 끝), ...] 형식의 링크 리스트
        """
        return self.links
