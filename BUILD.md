# 실행파일 생성 가이드

Windows TODO Panel 애플리케이션의 실행파일을 생성하는 방법입니다.

## 요구사항

- Python 3.9 이상
- 필수 패키지: `pip install -r requirements.txt`

## 빌드 방법

### 1. 기본 빌드
```bash
python build.py
```

### 2. 디버그 빌드 (콘솔 출력 포함)
```bash
python build.py --debug
```

### 3. PyInstaller 직접 사용
```bash
pyinstaller --clean --noconfirm todo_panel.spec
```

## 빌드 결과

- **출력 위치**: `dist/TodoPanel.exe`
- **파일 크기**: 약 25MB
- **배포**: 단일 실행파일로 배포 가능

## 참고사항

- UPX 압축 도구가 없으면 자동으로 비활성화됩니다
- 빌드된 실행파일은 git에 추가하지 않습니다 (.gitignore에 설정됨)
- 빌드 전 기존 dist 폴더는 자동으로 정리됩니다