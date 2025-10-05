"""링크 및 파일 경로 파싱 유틸리티.

명세서 6.1, 6.2에 정의된 정규식 패턴을 사용하여
TODO 텍스트에서 URL과 파일 경로를 추출합니다.
"""

import re
from typing import List, Tuple


class LinkParser:
    """링크 및 파일 경로 파싱 유틸리티."""

    # 정규식 패턴 (명세서 6.1, 6.2)
    # URL: 구두점(쉼표, 세미콜론, 마침표 등)을 제외
    URL_PATTERN = r'(https?://[^\s,;!?]+)|(www\.[^\s,;!?]+)'
    # 파일 경로: Windows 절대 경로 및 네트워크 경로
    PATH_PATTERN = r'([A-Za-z]:\\[\\\w\s\-\.]+)|(\\\\[\w\-\.]+\\[\\\w\s\-\.]+)'

    @staticmethod
    def parse_text(text: str) -> List[Tuple[str, str, int, int]]:
        """텍스트에서 링크/경로 추출.

        Args:
            text: TODO 텍스트

        Returns:
            List[Tuple[str, str, int, int]]: [(타입, 텍스트, 시작 위치, 끝 위치), ...]
            타입: 'url' 또는 'path'

        예시:
            text = "방문: https://claude.ai, 파일: C:\\docs\\file.txt"
            결과: [
                ('url', 'https://claude.ai', 4, 21),
                ('path', 'C:\\docs\\file.txt', 29, 47)
            ]
        """
        results = []

        # URL 매칭
        for match in re.finditer(LinkParser.URL_PATTERN, text):
            url = match.group(0)
            results.append(('url', url, match.start(), match.end()))

        # 파일 경로 매칭
        for match in re.finditer(LinkParser.PATH_PATTERN, text):
            path = match.group(0)
            results.append(('path', path, match.start(), match.end()))

        # 위치 순서로 정렬
        results.sort(key=lambda x: x[2])

        return results
