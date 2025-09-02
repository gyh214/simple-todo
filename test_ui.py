#!/usr/bin/env python3
"""
UI 컴포넌트 테스트 스크립트
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ui_components import TodoPanelApp

def main():
    """테스트 실행"""
    try:
        print("TODO Panel UI 컴포넌트 테스트 시작")
        app = TodoPanelApp()
        print("UI 초기화 완료")
        print("웹링크 기능 테스트: 할일에 https://github.com 등의 URL을 입력해보세요")
        print("Magic UI 스타일 적용됨")
        print("컴팩트한 디자인으로 더 많은 할일 표시 가능")
        app.run()
    except Exception as e:
        print(f"테스트 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()