# -*- coding: utf-8 -*-
"""
TODO Panel 아이콘 생성 스크립트

PyInstaller 빌드를 위한 ICO 파일을 생성합니다.
"""

import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError as e:
    print(f"PIL(Pillow) 패키지가 설치되지 않았습니다: {e}")
    print("다음 명령어로 설치하세요: pip install Pillow")
    sys.exit(1)


def create_todo_icon(sizes=[16, 32, 48, 64, 128, 256]):
    """
    TODO 패널용 아이콘을 다양한 크기로 생성
    
    Args:
        sizes: 생성할 아이콘 크기 리스트
    
    Returns:
        PIL Image 객체 리스트
    """
    icons = []
    
    for size in sizes:
        try:
            # 이미지 생성
            image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # 색상 설정
            bg_color = "#007acc"  # 파란색 배경
            check_color = "white"  # 흰색 체크마크
            border_color = "white"  # 흰색 테두리
            
            # 배경 원 그리기
            margin = max(2, size // 16)
            circle_bbox = [margin, margin, size - margin, size - margin]
            border_width = max(1, size // 32)
            
            draw.ellipse(circle_bbox, fill=bg_color, outline=border_color, width=border_width)
            
            # 체크 마크 그리기
            check_width = max(2, size // 16)
            center_x, center_y = size // 2, size // 2
            check_size = size // 3
            
            # 체크 마크 좌표 계산 (V자 형태)
            # 왼쪽 부분
            left_start = (center_x - check_size // 2, center_y)
            left_end = (center_x - check_size // 6, center_y + check_size // 3)
            
            # 오른쪽 부분
            right_start = left_end
            right_end = (center_x + check_size // 2, center_y - check_size // 3)
            
            # 체크 마크 그리기
            draw.line([left_start, left_end], fill=check_color, width=check_width)
            draw.line([right_start, right_end], fill=check_color, width=check_width)
            
            # 끝점을 둥글게 처리 (선택사항)
            if size >= 32:
                dot_size = check_width // 2
                for point in [left_start, left_end, right_end]:
                    dot_bbox = [
                        point[0] - dot_size, point[1] - dot_size,
                        point[0] + dot_size, point[1] + dot_size
                    ]
                    draw.ellipse(dot_bbox, fill=check_color)
            
            icons.append(image)
            print(f"[OK] {size}x{size} 아이콘 생성 완료")
            
        except Exception as e:
            print(f"[ERROR] {size}x{size} 아이콘 생성 실패: {e}")
            continue
    
    return icons


def save_icon_files(icons, base_name="TodoPanel"):
    """
    아이콘을 다양한 형태로 저장
    
    Args:
        icons: PIL Image 객체 리스트
        base_name: 기본 파일명
    """
    if not icons:
        print("저장할 아이콘이 없습니다.")
        return False
    
    try:
        # ICO 파일 저장 (모든 크기 포함)
        ico_path = Path(f"{base_name}.ico")
        icons[0].save(ico_path, format='ICO', sizes=[(img.width, img.height) for img in icons])
        print(f"[OK] ICO 파일 저장 완료: {ico_path}")
        
        # PNG 파일도 저장 (256x256 크기, 백업용)
        if len(icons) > 0:
            largest_icon = max(icons, key=lambda img: img.width)
            png_path = Path(f"{base_name}.png")
            largest_icon.save(png_path, format='PNG')
            print(f"[OK] PNG 파일 저장 완료: {png_path}")
        
        # 파일 크기 정보 출력
        if ico_path.exists():
            size_kb = ico_path.stat().st_size / 1024
            print(f"[OK] ICO 파일 크기: {size_kb:.1f} KB")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 아이콘 파일 저장 실패: {e}")
        return False


def main():
    """메인 함수"""
    print("=== TODO Panel 아이콘 생성 ===")
    print()
    
    try:
        # 아이콘 생성
        print("아이콘 생성 중...")
        icons = create_todo_icon()
        
        if not icons:
            print("[ERROR] 아이콘 생성에 실패했습니다.")
            return 1
        
        print(f"[OK] {len(icons)}개의 아이콘 크기 생성 완료")
        print()
        
        # 파일 저장
        print("아이콘 파일 저장 중...")
        if save_icon_files(icons, "TodoPanel"):
            print()
            print("=== 아이콘 생성 완료 ===")
            print("생성된 파일:")
            print("- TodoPanel.ico (PyInstaller용)")
            print("- TodoPanel.png (백업용)")
            return 0
        else:
            return 1
            
    except Exception as e:
        print(f"[ERROR] 치명적 오류: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())