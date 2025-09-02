# -*- coding: utf-8 -*-
"""
Windows TODO Panel 실행 스크립트

사용법:
python run_todo_panel.py           # 일반 모드
python run_todo_panel.py --debug   # 디버그 모드
"""

import sys
import os
from pathlib import Path

def main():
    """TODO Panel 실행"""
    print("Windows TODO Panel Starting...")
    
    # main.py가 있는지 확인
    main_file = Path(__file__).parent / "main.py"
    if not main_file.exists():
        print(f"Error: main.py not found at {main_file}")
        return 1
    
    # main.py를 임포트하고 실행
    try:
        from main import main as main_app
        main_app()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        return 0
    except Exception as e:
        print(f"Error running application: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())