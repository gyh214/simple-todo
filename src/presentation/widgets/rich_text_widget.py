"""링크/경로를 인식하고 클릭 가능하게 만드는 위젯.

명세서 6장 링크 및 경로 인식 구현:
- 웹 링크 자동 감지 및 브라우저 열기
- 파일 경로 자동 감지 및 탐색기/프로그램 열기
- 실행 파일 보안 검증
"""

from PyQt6.QtWidgets import QLabel, QMessageBox, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor
import webbrowser
import os
import subprocess
import re
from typing import List, Tuple
from ..utils.link_parser import LinkParser
import config


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
        self._expanded = False  # 펼침 상태
        self.links = []

        # Rich Text 포맷 설정
        self.setTextFormat(Qt.TextFormat.RichText)
        self.setOpenExternalLinks(False)  # 수동 처리

        # 1줄 고정 높이 및 줄바꿈 비활성화
        self.setFixedHeight(config.WIDGET_SIZES['todo_text_line_height'])
        self.setWordWrap(False)

        # Size Policy 설정: 너비는 자동 확장(Expanding), 높이는 고정(Fixed)
        # Expanding: 레이아웃이 제공하는 공간을 최대한 활용하며 자동 확장
        # setMinimumWidth()로 최소 너비만 제한하고, 나머지는 레이아웃이 자동 할당
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

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
        self._update_elided_text()

    def _convert_to_html(self, display_text: str, original_links: List[Tuple[str, str, int, int]]) -> str:
        """텍스트를 HTML로 변환 (링크/경로 하이라이트).

        Args:
            display_text: 화면에 표시될 텍스트 (elided 가능)
            original_links: 원본 텍스트에서 추출한 링크 리스트 [(타입, 텍스트, 시작, 끝), ...]

        Returns:
            HTML 문자열
        """
        if not original_links:
            # 링크가 없으면 텍스트만 반환
            return self._escape_html(display_text)

        # 링크를 <a> 태그로 변환
        result = []
        last_end = 0

        for link_type, original_link_text, original_start, original_end in original_links:
            # display_text에서 링크 시작 위치 찾기
            # 원본 텍스트의 시작 위치를 기준으로 display_text에서 매칭
            if original_start >= len(display_text):
                # 링크가 display_text 범위를 넘어서면 중단
                break

            # display_text에서 실제 표시될 링크 텍스트 찾기
            # 링크 시작 위치부터 원본 링크의 시작 패턴 매칭
            display_start = original_start

            # 링크 끝 위치 계산 (elided된 경우 "..." 포함)
            if original_end <= len(display_text):
                # 링크가 잘리지 않음
                display_end = original_end
                display_link_text = display_text[display_start:display_end]
            else:
                # 링크가 잘림 - "..."까지를 표시 텍스트로 사용
                # display_text에서 링크 시작부터 끝까지 (또는 "..."까지)
                display_end = len(display_text)
                display_link_text = display_text[display_start:display_end]

            # 링크 이전 텍스트 추가
            if display_start > last_end:
                result.append(self._escape_html(display_text[last_end:display_start]))

            # 링크를 <a> 태그로 변환
            # href는 "type:original_text" 형식으로 원본 링크 사용
            href = f"{link_type}:{original_link_text}"

            # URL과 Path에 따라 다른 스타일 적용
            if link_type == 'url':
                # URL: #CC785C, 밑줄
                result.append(
                    f'<a href="{self._escape_html(href)}" '
                    f'style="color: #CC785C; text-decoration: underline;" '
                    f'data-type="url">'
                    f'{self._escape_html(display_link_text)}</a>'
                )
            else:  # path
                # Path: #CC785C, 밑줄, opacity 0.8
                result.append(
                    f'<a href="{self._escape_html(href)}" '
                    f'style="color: #CC785C; text-decoration: underline; opacity: 0.8;" '
                    f'data-type="path">'
                    f'{self._escape_html(display_link_text)}</a>'
                )

            last_end = display_end

        # 마지막 링크 이후 텍스트 추가
        if last_end < len(display_text):
            result.append(self._escape_html(display_text[last_end:]))

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

    def set_expanded(self, expanded: bool) -> None:
        """텍스트 펼침/접힘 상태 설정.

        Args:
            expanded: True면 펼침, False면 접힘
        """
        if self._expanded == expanded:
            return

        self._expanded = expanded

        if expanded:
            # 펼침: 높이 자동, 줄바꿈 활성화
            self.setMinimumHeight(config.WIDGET_SIZES['todo_text_line_height'])
            self.setMaximumHeight(16777215)  # QWIDGETSIZE_MAX
            self.setWordWrap(True)
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        else:
            # 접힘: 1줄 고정
            self.setMinimumHeight(config.WIDGET_SIZES['todo_text_line_height'])
            self.setMaximumHeight(config.WIDGET_SIZES['todo_text_line_height'])
            self.setWordWrap(False)
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self._update_elided_text()
        self.adjustSize()
        self.updateGeometry()

    def _normalize_newlines(self, text: str) -> str:
        """모든 개행문자를 \\n으로 정규화.

        처리하는 패턴:
        - <br>, <br/>, <br /> (HTML)
        - \\r\\n (Windows)
        - \\r (Mac Classic)
        - \\n (Unix)

        Args:
            text: 원본 텍스트

        Returns:
            정규화된 텍스트 (\\n만 포함)
        """
        # <br>, <br/>, <br /> 처리
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        # \r\n -> \n, \r -> \n
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        return text

    def _convert_to_html_expanded(self, text: str, links: List[Tuple[str, str, int, int]]) -> str:
        """펼침 모드용 HTML 변환 (개행 유지).

        Args:
            text: 정규화된 텍스트 (\\n만 포함)
            links: 링크 리스트

        Returns:
            HTML 문자열 (개행이 <br>로 변환됨)
        """
        if not links:
            # 링크 없음: 텍스트만 처리
            escaped = self._escape_html(text)
            return escaped.replace('\n', '<br>')

        # 링크가 있는 경우: 기존 _convert_to_html 로직 재사용 후 개행 처리
        # 먼저 개행 없이 변환 후, 개행 문자를 <br>로 치환
        result = []
        last_end = 0

        for link_type, link_text, start, end in links:
            # 링크 이전 텍스트
            if start > last_end:
                result.append(self._escape_html(text[last_end:start]).replace('\n', '<br>'))

            # 링크 (개행이 링크 내에 있을 수 있음)
            display_link = self._escape_html(link_text).replace('\n', '<br>')
            href = f"{link_type}:{link_text}"

            if link_type == 'url':
                result.append(
                    f'<a href="{self._escape_html(href)}" '
                    f'style="color: #CC785C; text-decoration: underline;" '
                    f'data-type="url">{display_link}</a>'
                )
            else:
                result.append(
                    f'<a href="{self._escape_html(href)}" '
                    f'style="color: #CC785C; text-decoration: underline; opacity: 0.8;" '
                    f'data-type="path">{display_link}</a>'
                )

            last_end = end

        # 마지막 링크 이후 텍스트
        if last_end < len(text):
            result.append(self._escape_html(text[last_end:]).replace('\n', '<br>'))

        return ''.join(result)

    def _update_elided_text(self):
        """너비에 맞게 텍스트를 elide 처리하고 HTML 변환.

        펼침 모드: 개행문자를 실제 줄바꿈으로 표시
        접힘 모드: 개행문자를 공백으로 치환하여 1줄 표시
        """
        if not self.raw_text:
            self.setText("")
            self.setToolTip("")
            return

        if self._expanded:
            # 펼침 모드: 개행 유지
            normalized_text = self._normalize_newlines(self.raw_text)

            # 링크 파싱 (정규화된 텍스트에서)
            self.links = LinkParser.parse_text(normalized_text)

            # HTML 변환 (개행을 <br>로)
            html = self._convert_to_html_expanded(normalized_text, self.links)
            self.setText(html)
            self.setToolTip("")  # 펼침 모드에서는 툴팁 불필요
        else:
            # 접힘 모드: 기존 로직 (개행→공백, 1줄)
            single_line_text = self.raw_text.replace('\n', ' ').replace('\r', ' ')

            available_width = self.width() - 10
            fm = self.fontMetrics()

            # 텍스트가 넘치면 elide, 아니면 원본
            if fm.horizontalAdvance(single_line_text) > available_width:
                display_text = fm.elidedText(single_line_text, Qt.TextElideMode.ElideRight, available_width)
                self.setToolTip(self.raw_text)  # 툴팁에는 원본 텍스트 (개행 포함)
            else:
                display_text = single_line_text
                # 원본에 개행이 있으면 툴팁에 표시
                if '\n' in self.raw_text or '\r' in self.raw_text:
                    self.setToolTip(self.raw_text)
                else:
                    self.setToolTip("")

            # 원본 텍스트(single_line_text)에서 링크 파싱 - 원본 링크 정보 보존
            self.links = LinkParser.parse_text(single_line_text)

            # HTML 변환 시 display_text 사용하되, 링크는 원본 사용
            html = self._convert_to_html(display_text, self.links)
            self.setText(html)

    def resizeEvent(self, event):
        """위젯 크기 변경 시 텍스트 다시 elide 처리.

        Args:
            event: resize 이벤트
        """
        super().resizeEvent(event)
        if hasattr(self, 'raw_text'):
            self._update_elided_text()

    def showEvent(self, event):
        """위젯 표시 시 텍스트 elide 처리.

        Args:
            event: show 이벤트
        """
        super().showEvent(event)
        if hasattr(self, 'raw_text'):
            self._update_elided_text()
