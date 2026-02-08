"""
매크로 시작 전 간단한 테스트 스크립트
"""
import sys
import io

# 한글 출력을 위한 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 60)
print("Macro Startup Test")
print("=" * 60)

# 1. 필요한 모듈 import 테스트
print("\n[1/5] Module import test...")
try:
    import pyautogui
    import keyboard
    import mss
    import numpy as np
    import easyocr
    from PyQt5 import QtWidgets, QtCore, QtGui
    print("OK - All modules imported successfully")
except ImportError as e:
    print(f"ERROR - Module import failed: {e}")
    sys.exit(1)

# 2. PyQt5 애플리케이션 생성 테스트
print("\n[2/5] PyQt5 application test...")
try:
    app = QtWidgets.QApplication(sys.argv)
    print("OK - PyQt5 application created successfully")
except Exception as e:
    print(f"ERROR - PyQt5 application creation failed: {e}")
    sys.exit(1)

# 3. 주요 클래스 import 테스트
print("\n[3/5] main.py class import test...")
try:
    sys.path.insert(0, r'c:\WorkSpace\PathOfCraft\macro')
    from main import MainWindow, MacroThread
    print("OK - Classes imported successfully")
except Exception as e:
    print(f"ERROR - Class import failed: {e}")
    import traceback
    print(traceback.format_exc())
    sys.exit(1)

# 4. MainWindow 인스턴스 생성 테스트
print("\n[4/5] MainWindow instance creation test...")
try:
    win = MainWindow()
    print("OK - MainWindow created successfully")
except Exception as e:
    print(f"ERROR - MainWindow creation failed: {e}")
    import traceback
    print(traceback.format_exc())
    sys.exit(1)

# 5. UI 컴포넌트 확인
print("\n[5/5] UI component check...")
try:
    assert hasattr(win, 'spinbox_item_count'), "spinbox_item_count missing"
    assert hasattr(win, 'spinbox_move_distance'), "spinbox_move_distance missing"
    assert hasattr(win, 'spinbox_wait_time'), "spinbox_wait_time missing"
    assert hasattr(win, 'label_batch_progress'), "label_batch_progress missing"
    assert hasattr(win, 'label_mouse_pos'), "label_mouse_pos missing"
    assert hasattr(win, 'excluded_stats'), "excluded_stats missing"
    assert hasattr(win, 'batch_mode'), "batch_mode missing"
    assert hasattr(win, 'current_item_index'), "current_item_index missing"
    print("OK - All UI components exist")
except AssertionError as e:
    print(f"ERROR - UI component check failed: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("SUCCESS - All tests passed!")
print("=" * 60)
print("\nClosing test program...")

