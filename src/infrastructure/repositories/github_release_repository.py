# -*- coding: utf-8 -*-
"""GitHub Release Repository - GitHub API로부터 릴리스 정보 가져오기"""

import logging
from typing import Optional
from datetime import datetime

try:
    import requests
except ImportError:
    requests = None

from ...domain.entities.release import Release
from ...domain.value_objects.app_version import AppVersion


logger = logging.getLogger(__name__)


class GitHubReleaseRepository:
    """GitHub Releases API를 통해 최신 릴리스 정보를 가져오는 Repository

    GitHub REST API v3를 사용하여 최신 릴리스 정보를 조회하고,
    SimpleTodo.exe 에셋이 포함된 Release 엔티티로 변환합니다.

    Attributes:
        repo_owner: GitHub 저장소 소유자
        repo_name: GitHub 저장소 이름
        timeout: API 요청 타임아웃 (초)

    Examples:
        >>> repo = GitHubReleaseRepository("gyh214", "simple-todo")
        >>> release = repo.get_latest_release()
        >>> if release:
        ...     print(f"최신 버전: {release.version}")
    """

    def __init__(self, repo_owner: str, repo_name: str, timeout: int = 10):
        """GitHubReleaseRepository 초기화

        Args:
            repo_owner: GitHub 저장소 소유자 (예: "gyh214")
            repo_name: GitHub 저장소 이름 (예: "simple-todo")
            timeout: API 요청 타임아웃 (초, 기본값: 10)

        Raises:
            ValueError: repo_owner 또는 repo_name이 비어있는 경우
            ImportError: requests 라이브러리가 설치되지 않은 경우
        """
        if not repo_owner or not repo_owner.strip():
            raise ValueError("repo_owner는 비어있을 수 없습니다")
        if not repo_name or not repo_name.strip():
            raise ValueError("repo_name은 비어있을 수 없습니다")
        if requests is None:
            raise ImportError(
                "requests 라이브러리가 설치되지 않았습니다. "
                "'pip install requests'를 실행하세요."
            )

        self.repo_owner = repo_owner.strip()
        self.repo_name = repo_name.strip()
        self.timeout = max(1, timeout)  # 최소 1초

        self.api_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases/latest"

        logger.info(
            f"GitHubReleaseRepository 초기화: {self.repo_owner}/{self.repo_name}"
        )

    def get_latest_release(self) -> Optional[Release]:
        """GitHub에서 최신 릴리스 정보를 가져옵니다.

        SimpleTodo.exe 에셋이 포함된 최신 릴리스를 조회하고,
        Release 엔티티로 변환하여 반환합니다.

        Returns:
            Optional[Release]: 최신 릴리스 정보 또는 None (실패 시)

        Note:
            다음 경우에 None을 반환합니다:
            - 네트워크 오류
            - API rate limit 초과
            - 404 Not Found (릴리스가 없는 경우)
            - SimpleTodo.exe 에셋이 없는 경우
            - JSON 파싱 오류
        """
        try:
            logger.info(f"GitHub API 요청: {self.api_url}")

            # GitHub API 요청
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'SimpleTodo-AutoUpdater/1.0'
            }

            response = requests.get(
                self.api_url,
                headers=headers,
                timeout=self.timeout
            )

            # HTTP 상태 코드 확인
            if response.status_code == 404:
                logger.warning(f"릴리스를 찾을 수 없습니다: {self.repo_owner}/{self.repo_name}")
                return None

            if response.status_code == 403:
                logger.error("GitHub API rate limit 초과. 나중에 다시 시도하세요.")
                return None

            if response.status_code != 200:
                logger.error(
                    f"GitHub API 요청 실패: HTTP {response.status_code} - {response.text[:200]}"
                )
                return None

            # JSON 파싱
            data = response.json()

            # Release 엔티티로 변환
            release = self._parse_release_response(data)

            if release:
                logger.info(
                    f"최신 릴리스 조회 성공: {release.version} "
                    f"({release.format_file_size()})"
                )
            else:
                logger.warning("SimpleTodo.exe 에셋을 찾을 수 없습니다")

            return release

        except requests.exceptions.Timeout:
            logger.error(f"GitHub API 요청 타임아웃 ({self.timeout}초)")
            return None

        except requests.exceptions.ConnectionError as e:
            logger.error(f"네트워크 연결 오류: {e}")
            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"GitHub API 요청 중 오류 발생: {e}")
            return None

        except ValueError as e:
            logger.error(f"릴리스 데이터 파싱 오류: {e}")
            return None

        except Exception as e:
            logger.error(f"예상치 못한 오류 발생: {e}", exc_info=True)
            return None

    def _parse_release_response(self, data: dict) -> Optional[Release]:
        """GitHub API 응답을 Release 엔티티로 변환합니다.

        Args:
            data: GitHub API JSON 응답 데이터

        Returns:
            Optional[Release]: 변환된 Release 엔티티 또는 None

        Raises:
            ValueError: 필수 필드가 없거나 유효하지 않은 경우
        """
        # tag_name에서 버전 추출
        tag_name = data.get('tag_name')
        if not tag_name:
            raise ValueError("tag_name 필드가 없습니다")

        # AppVersion 생성 (v 접두사 자동 처리)
        try:
            version = AppVersion.from_string(tag_name)
        except ValueError as e:
            raise ValueError(f"유효하지 않은 버전 형식: {tag_name} - {e}")

        # 릴리스 노트
        release_notes = data.get('body', '').strip()

        # 공개 날짜
        published_at_str = data.get('published_at')
        if not published_at_str:
            raise ValueError("published_at 필드가 없습니다")

        try:
            # ISO 8601 형식 파싱 (예: "2025-01-15T10:00:00Z")
            published_at = datetime.fromisoformat(
                published_at_str.replace('Z', '+00:00')
            )
        except ValueError as e:
            raise ValueError(f"유효하지 않은 날짜 형식: {published_at_str} - {e}")

        # assets에서 SimpleTodo.exe 찾기
        assets = data.get('assets', [])
        exe_asset = self._find_exe_asset(assets)

        if not exe_asset:
            # SimpleTodo.exe 에셋이 없으면 None 반환
            return None

        # Release 엔티티 생성
        release = Release(
            version=version,
            download_url=exe_asset['browser_download_url'],
            release_notes=release_notes,
            published_at=published_at,
            asset_name=exe_asset['name'],
            asset_size=exe_asset['size']
        )

        return release

    def _find_exe_asset(self, assets: list) -> Optional[dict]:
        """assets 목록에서 SimpleTodo.exe 파일을 찾습니다.

        Args:
            assets: GitHub API의 assets 배열

        Returns:
            Optional[dict]: SimpleTodo.exe 에셋 정보 또는 None

        Note:
            대소문자 구분 없이 "SimpleTodo.exe" 또는 "simpletodo.exe"를 찾습니다.
        """
        if not assets or not isinstance(assets, list):
            return None

        for asset in assets:
            name = asset.get('name', '').lower()

            # SimpleTodo.exe 파일 찾기 (대소문자 무시)
            if name == 'simpletodo.exe':
                # 필수 필드 검증
                if not asset.get('browser_download_url'):
                    logger.warning(f"에셋 '{asset.get('name')}'에 다운로드 URL이 없습니다")
                    continue

                if not isinstance(asset.get('size'), int):
                    logger.warning(f"에셋 '{asset.get('name')}'에 유효한 크기 정보가 없습니다")
                    continue

                return asset

        return None

    def __repr__(self) -> str:
        """개발자용 문자열 표현을 반환합니다."""
        return (
            f"GitHubReleaseRepository("
            f"repo='{self.repo_owner}/{self.repo_name}', "
            f"timeout={self.timeout}s)"
        )
