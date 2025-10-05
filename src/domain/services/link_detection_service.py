# -*- coding: utf-8 -*-
"""LinkDetectionService - 링크 및 경로 감지 서비스"""

import re
from typing import List, Tuple, Literal


LinkType = Literal["url", "path"]


class LinkDetectionService:
    """텍스트에서 URL과 파일 경로를 감지하는 도메인 서비스

    정규식을 사용하여 링크와 경로를 추출합니다.
    """

    # URL 정규식: http://, https://, www. 로 시작하는 URL
    URL_PATTERN = re.compile(r'(https?://[^\s]+)|(www\.[^\s]+)')

    # 파일 경로 정규식: Windows 경로 (C:\..., \\server\...)
    PATH_PATTERN = re.compile(r'([A-Za-z]:\\[\\\w\s\-\.]+)|(\\\\[\w\-\.]+\\[\\\w\s\-\.]+)')

    @staticmethod
    def detect_links(text: str) -> List[Tuple[LinkType, str, int, int]]:
        """텍스트에서 링크와 경로를 감지합니다.

        Args:
            text: 검사할 텍스트

        Returns:
            List[Tuple[LinkType, str, int, int]]:
                [(type, text, start, end), ...] 형식의 리스트
                - type: "url" 또는 "path"
                - text: 감지된 링크/경로 문자열
                - start: 시작 위치 (인덱스)
                - end: 종료 위치 (인덱스)
        """
        results: List[Tuple[LinkType, str, int, int]] = []

        # URL 감지
        for match in LinkDetectionService.URL_PATTERN.finditer(text):
            # match.group(0)은 전체 매칭된 문자열
            matched_text = match.group(0)
            start = match.start()
            end = match.end()
            results.append(("url", matched_text, start, end))

        # 파일 경로 감지
        for match in LinkDetectionService.PATH_PATTERN.finditer(text):
            matched_text = match.group(0)
            start = match.start()
            end = match.end()
            results.append(("path", matched_text, start, end))

        # 위치 순서대로 정렬
        results.sort(key=lambda x: x[2])

        return results

    @staticmethod
    def has_links(text: str) -> bool:
        """텍스트에 링크나 경로가 있는지 확인합니다.

        Args:
            text: 검사할 텍스트

        Returns:
            bool: 링크나 경로가 있으면 True, 없으면 False
        """
        return (
            LinkDetectionService.URL_PATTERN.search(text) is not None or
            LinkDetectionService.PATH_PATTERN.search(text) is not None
        )

    @staticmethod
    def extract_urls(text: str) -> List[str]:
        """텍스트에서 URL만 추출합니다.

        Args:
            text: 검사할 텍스트

        Returns:
            List[str]: 감지된 URL 리스트
        """
        matches = LinkDetectionService.URL_PATTERN.findall(text)
        # findall은 그룹이 있을 경우 튜플 리스트를 반환
        # (group1, group2) 형태이므로 빈 문자열이 아닌 것만 추출
        urls = []
        for match in matches:
            url = match[0] if match[0] else match[1]
            if url:
                urls.append(url)
        return urls

    @staticmethod
    def extract_paths(text: str) -> List[str]:
        """텍스트에서 파일 경로만 추출합니다.

        Args:
            text: 검사할 텍스트

        Returns:
            List[str]: 감지된 파일 경로 리스트
        """
        matches = LinkDetectionService.PATH_PATTERN.findall(text)
        # findall은 그룹이 있을 경우 튜플 리스트를 반환
        paths = []
        for match in matches:
            path = match[0] if match[0] else match[1]
            if path:
                paths.append(path)
        return paths
