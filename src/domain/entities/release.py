# -*- coding: utf-8 -*-
"""Release Entity - GitHub Release 정보"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ..value_objects.app_version import AppVersion


@dataclass
class Release:
    """GitHub Release 정보를 나타내는 엔티티

    GitHub API에서 가져온 릴리스 정보를 도메인 객체로 표현합니다.
    버전 비교, 다운로드 URL, 릴리스 노트 등의 정보를 포함합니다.

    Attributes:
        version: 릴리스 버전 (AppVersion)
        download_url: exe 파일 다운로드 URL
        release_notes: 릴리스 노트 (마크다운 형식)
        published_at: 릴리스 공개 날짜
        asset_name: 에셋 파일명 (예: "SimpleTodo.exe")
        asset_size: 파일 크기 (bytes)
    """

    version: AppVersion
    download_url: str
    release_notes: str
    published_at: datetime
    asset_name: str
    asset_size: int

    def __post_init__(self):
        """생성 후 검증을 수행합니다."""
        # download_url 검증
        if not self.download_url or not isinstance(self.download_url, str):
            raise ValueError("다운로드 URL이 필요합니다")

        if not self.download_url.startswith(('http://', 'https://')):
            raise ValueError(f"유효하지 않은 다운로드 URL입니다: {self.download_url}")

        # asset_name 검증
        if not self.asset_name or not isinstance(self.asset_name, str):
            raise ValueError("에셋 파일명이 필요합니다")

        # asset_size 검증
        if self.asset_size < 0:
            raise ValueError(f"파일 크기는 0 이상이어야 합니다: {self.asset_size}")

        # published_at 검증
        if not isinstance(self.published_at, datetime):
            raise ValueError("공개 날짜는 datetime 객체여야 합니다")

        # version 검증
        if not isinstance(self.version, AppVersion):
            raise ValueError("버전은 AppVersion 객체여야 합니다")

    def is_newer_than(self, current_version: AppVersion) -> bool:
        """현재 버전보다 새로운 릴리스인지 확인합니다.

        Args:
            current_version: 현재 설치된 버전

        Returns:
            bool: 릴리스 버전이 현재 버전보다 높으면 True

        Raises:
            TypeError: current_version이 AppVersion이 아닌 경우
        """
        if not isinstance(current_version, AppVersion):
            raise TypeError(
                f"current_version은 AppVersion이어야 합니다. "
                f"받은 타입: {type(current_version)}"
            )
        return self.version > current_version

    def format_file_size(self) -> str:
        """파일 크기를 사람이 읽기 쉬운 형식으로 변환합니다.

        Returns:
            str: 형식화된 파일 크기 (예: "5.2 MB", "1.3 GB")
        """
        size = self.asset_size
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0

        while size >= 1024.0 and unit_index < len(units) - 1:
            size /= 1024.0
            unit_index += 1

        if unit_index == 0:
            # Bytes는 소수점 없이 표시
            return f"{size} {units[unit_index]}"
        else:
            # 나머지는 소수점 1자리까지 표시
            return f"{size:.1f} {units[unit_index]}"

    def format_published_date(self) -> str:
        """공개 날짜를 사람이 읽기 쉬운 형식으로 변환합니다.

        Returns:
            str: 형식화된 날짜 (예: "2025-01-15")
        """
        return self.published_at.strftime("%Y-%m-%d")

    def get_short_release_notes(self, max_length: int = 200) -> str:
        """릴리스 노트의 요약본을 반환합니다.

        Args:
            max_length: 최대 길이 (기본값: 200자)

        Returns:
            str: 요약된 릴리스 노트 (긴 경우 "..." 추가)
        """
        if not self.release_notes:
            return "릴리스 노트 없음"

        # 개행 문자를 공백으로 변환
        clean_notes = ' '.join(self.release_notes.split())

        if len(clean_notes) <= max_length:
            return clean_notes
        else:
            return clean_notes[:max_length].rstrip() + "..."

    def __str__(self) -> str:
        """Release를 사람이 읽기 쉬운 문자열로 변환합니다.

        Returns:
            str: Release 정보 문자열
        """
        return (
            f"Release v{self.version} "
            f"({self.format_published_date()}, {self.format_file_size()})"
        )

    def __repr__(self) -> str:
        """개발자용 문자열 표현을 반환합니다.

        Returns:
            str: Release 표현 문자열
        """
        return (
            f"Release(version={self.version}, "
            f"asset_name='{self.asset_name}', "
            f"published_at='{self.format_published_date()}')"
        )

    def to_dict(self) -> dict:
        """Release를 딕셔너리로 변환합니다.

        직렬화 및 로깅에 유용합니다.

        Returns:
            dict: Release 정보를 담은 딕셔너리
        """
        return {
            'version': str(self.version),
            'download_url': self.download_url,
            'release_notes': self.release_notes,
            'published_at': self.published_at.isoformat(),
            'asset_name': self.asset_name,
            'asset_size': self.asset_size,
            'asset_size_formatted': self.format_file_size(),
        }
