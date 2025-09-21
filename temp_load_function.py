    def _load_pane_ratio(self):
        """저장된 분할 비율을 불러오기 (기본값: 0.8) - 디버그 강화"""
        try:
            import json

            config_file = self._get_config_file_path()
            print(f"[DEBUG] 설정 파일 경로: {config_file}")

            if not config_file.exists():
                print(f"[DEBUG] 설정 파일 없음, 기본값 0.8 사용")
                return 0.8  # 기본값

            with open(config_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)

            print(f"[DEBUG] 로드된 설정: {settings}")
            ratio = settings.get('paned_window_ratio', 0.8)
            print(f"[DEBUG] 원본 비율값: {ratio}")

            # 유효한 범위인지 검증 (0.1 ~ 0.9)
            ratio = max(0.1, min(0.9, ratio))
            print(f"[DEBUG] 검증된 비율값: {ratio}")

            return ratio

        except Exception as e:
            print(f"[DEBUG] 분할 비율 로드 실패, 기본값 사용: {e}")
            return 0.8  # 기본값