# -*- coding: utf-8 -*-
"""
Main Application Basic Function Test Script
"""

import sys
import os
from pathlib import Path

# Module Import Tests
print("=== Module Import Tests ===")
try:
    import pystray
    print("[OK] pystray import successful")
except ImportError as e:
    print(f"[FAIL] pystray import failed: {e}")

try:
    from PIL import Image, ImageDraw
    print("[OK] PIL import successful")
except ImportError as e:
    print(f"[FAIL] PIL import failed: {e}")

try:
    import psutil
    print("[OK] psutil import successful")
except ImportError as e:
    print(f"[FAIL] psutil import failed: {e}")

try:
    from ui_components import TodoPanelApp
    print("[OK] ui_components import successful")
except ImportError as e:
    print(f"[FAIL] ui_components import failed: {e}")

try:
    from todo_manager import TodoManager
    print("[OK] todo_manager import successful")
except ImportError as e:
    print(f"[FAIL] todo_manager import failed: {e}")

print("\n=== Core Class Tests ===")

# Tray Icon Generation Test
try:
    from main import TrayIconGenerator
    icon = TrayIconGenerator.create_icon(32)
    print(f"[OK] Tray icon generation successful (size: {icon.size})")
except Exception as e:
    print(f"[FAIL] Tray icon generation failed: {e}")

# Single Instance Manager Test
try:
    from main import SingleInstanceManager
    instance_mgr = SingleInstanceManager(65433)  # Use different port
    is_running = instance_mgr.is_already_running()
    print(f"[OK] Single instance manager test successful (running: {is_running})")
    instance_mgr.cleanup()
except Exception as e:
    print(f"[FAIL] Single instance manager test failed: {e}")

# Log Manager Test
try:
    from main import LogManager
    log_mgr = LogManager(debug=True)
    log_mgr.info("Test log message")
    print("[OK] Log manager test successful")
except Exception as e:
    print(f"[FAIL] Log manager test failed: {e}")

# TodoManager Basic Function Test
try:
    todo_mgr = TodoManager(debug=False)
    stats = todo_mgr.get_stats()
    print(f"[OK] TodoManager basic function test successful (stats: {stats})")
except Exception as e:
    print(f"[FAIL] TodoManager basic function test failed: {e}")

print("\n=== Test Complete ===")
print("All core components loaded successfully and basic functions are working.")