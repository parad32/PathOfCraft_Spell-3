import sys
import threading
import time

import pyautogui
import keyboard
import mss
import numpy as np
import easyocr

from PyQt5 import QtWidgets, QtCore, QtGui


TARGET_TEXT = "모든 주문 스킬레벨 +3"


def is_target_detected(raw_text: str) -> bool:
    """
    OCR가 인식한 문자열(raw_text)을 받아
    "모든 주문 스킬 레벨 +3" 옵션인지 정확하게 판단한다.

    필수 키워드 (변형 포함):
    1. 모든 (모듬, 모둔)
    2. 주문 (주뭄, 주믄)
    3. 스킬 (스길)
    4. 레벨 (레벌, 레펠)
    5. +3 (반드시 3)

    제외 키워드:
    - 소환수, 투사체, 근접 (이것들이 있으면 False)
    """
    if not raw_text:
        return False

    compact = "".join(raw_text.split())
    print("[MATCH] compact:", compact)

    # === 제외 키워드 필터링 ===
    exclude_keywords = ["소환수", "투사체", "근접"]
    for exclude in exclude_keywords:
        if exclude in compact:
            print(f"[MATCH] 제외 키워드 '{exclude}' 감지, False 반환")
            return False

    # === 필수 키워드 1: 모든 (OCR 오인식 변형 포함) ===
    # ㅁ/ㅂ/ㅍ, ㄷ/ㄹ/ㄴ/ㅌ/ㅅ, ㅡ/ㅓ/ㅗ/ㅜ 혼동
    keyword_modeun = [
        "모든", "모듬", "모둔", "모돈", "모등", "모튼", "모돈", "모든",
        "보든", "모론", "모른", "모슨", "모순", "묘든", "묘둔",
        "모드", "모듣", "모듯", "모돌", "모돌", "모뜬", "모뜨",
        "몯든", "묘든", "보둔", "보든", "뫼든", "뫼둔"
    ]
    if not any(keyword in compact for keyword in keyword_modeun):
        print("[MATCH] '모든' 키워드 없음")
        return False

    # === 필수 키워드 2: 주문 (OCR 오인식 변형 포함) ===
    # ㅈ/ㅊ/ㅉ, ㅜ/ㅠ/ㅡ/ㅓ, ㅁ/ㄴ/ㅂ/ㅍ 혼동
    keyword_jumun = [
        "주문", "주뭄", "주믄", "주몬", "주뮨", "주뭔", "쥬문", "쥬뭄",
        "쥬믄", "쥬몬", "쥬뮨", "추문", "추뭄", "추믄", "추몬",
        "쭈문", "쭈뭄", "쭈믄", "죠문", "죠뭄", "주분", "주본",
        "쥬분", "쥬본", "주폰", "쥬폰", "주론", "쥬론"
    ]
    if not any(keyword in compact for keyword in keyword_jumun):
        print("[MATCH] '주문' 키워드 없음")
        return False

    # === 필수 키워드 3: 스킬 (OCR 오인식 변형 포함) ===
    # ㅅ/ㅆ/ㅈ, ㅋ/ㄱ/ㄲ/ㅌ, ㅣ/ㅡ/ㅏ, ㄹ/ㄴ/ㄷ 혼동
    keyword_skill = [
        "스킬", "스길", "스킨", "스칼", "스킥", "스킵", "스킹", "스킬",
        "스틸", "스딜", "스낄", "스끼", "스끼ㄹ", "쓰킬", "쓰길",
        "쓰킨", "쓰칼", "즈킬", "즈길", "즈킨", "슥킬", "슥길",
        "스큘", "스클", "스킫", "스키", "스키ㄹ", "스컬"
    ]
    if not any(keyword in compact for keyword in keyword_skill):
        print("[MATCH] '스킬' 키워드 없음")
        return False

    # === 필수 키워드 4: 레벨 (OCR 오인식 변형 포함) ===
    # ㄹ/ㄴ/ㄷ, ㅔ/ㅐ/ㅓ/ㅕ, ㅂ/ㅃ/ㅍ/ㅁ 혼동
    keyword_level = [
        "레벨", "레벌", "레펠", "레밸", "래벨", "레별", "레뻘", "레뻔", 
        "래밸", "레벤", "레벨+3", "레빛", "레비", "레빋", "레블",
        "레볼", "레멜", "레멜", "네벨", "네벌", "네밸", "데벨",
        "레혈", "레혈", "려벨", "려벌", "려밸", "뢰벨", "뢰밸",
        "레뱔", "레뼐", "레백", "레밥", "레벨", "레벨","레텔","레테","레톌"
    ]
    if not any(keyword in compact for keyword in keyword_level):
        print("[MATCH] '레벨' 키워드 없음")
        return False

    # === 필수 키워드 5: +3 (반드시 3) ===
    # +3이 있는지 확인
    has_plus_3 = ("+3" in compact) or ("+ 3" in raw_text) or ("+3" in raw_text)
    
    # +1, +2가 있으면 제외
    has_plus_1_or_2 = ("+1" in compact) or ("+2" in compact) or \
                      ("+ 1" in raw_text) or ("+ 2" in raw_text)
    
    if has_plus_1_or_2:
        print("[MATCH] +1 또는 +2 감지됨, +3만 필요 (False)")
        return False
    
    if not has_plus_3:
        print("[MATCH] '+3' 없음")
        return False

    # === 모든 조건 만족 ===
    print("[MATCH] ✓ 모든 조건 만족! True 반환")
    return True


class SelectionOverlay(QtWidgets.QWidget):
    """
    전체 화면을 덮는 선택 오버레이.
    마우스로 드래그해서 인식 영역(사각형)을 지정한다.
    """

    region_selected = QtCore.pyqtSignal(int, int, int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.WindowStaysOnTopHint
            | QtCore.Qt.Tool
        )
        self.setWindowState(QtCore.Qt.WindowFullScreen)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        self.start_pos = None
        self.end_pos = None

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.LeftButton:
            self.start_pos = event.pos()
            self.end_pos = event.pos()
            self.update()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if self.start_pos is not None:
            self.end_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.LeftButton and self.start_pos and self.end_pos:
            x1 = min(self.start_pos.x(), self.end_pos.x())
            y1 = min(self.start_pos.y(), self.end_pos.y())
            x2 = max(self.start_pos.x(), self.end_pos.x())
            y2 = max(self.start_pos.y(), self.end_pos.y())
            w = x2 - x1
            h = y2 - y1
            self.region_selected.emit(x1, y1, w, h)
            self.close()

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # 항상 전체 화면을 살짝 어둡게 표시해서
        # 오버레이가 떠 있다는 것을 눈에 보이게 한다.
        painter.fillRect(self.rect(), QtGui.QColor(0, 0, 0, 80))

        # 드래그 중일 때만 선택 사각형을 그린다.
        if self.start_pos and self.end_pos:
            x1 = min(self.start_pos.x(), self.end_pos.x())
            y1 = min(self.start_pos.y(), self.end_pos.y())
            x2 = max(self.start_pos.x(), self.end_pos.x())
            y2 = max(self.start_pos.y(), self.end_pos.y())
            rect = QtCore.QRect(x1, y1, x2 - x1, y2 - y1)

            painter.setPen(QtGui.QPen(QtGui.QColor(255, 0, 0), 3))
            painter.drawRect(rect)


class RegionBorderOverlay(QtWidgets.QWidget):
    """
    항상 인식 영역에 빨간 테두리를 표시하는 오버레이.
    마우스 입력은 통과시킨다.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.WindowStaysOnTopHint
            | QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.region = None

    def set_region(self, x: int, y: int, w: int, h: int) -> None:
        self.region = (x, y, w, h)
        self.setGeometry(x, y, w, h)
        self.show()
        self.update()

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        if not self.region:
            return
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 0, 0), 3))
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)


class BlockPopup(QtWidgets.QDialog):
    """
    옵션 감지 시 뜨는 전체 화면 팝업.
    클릭을 막고, 클릭 횟수를 보여준다.
    """

    def __init__(self, click_count: int, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.WindowStaysOnTopHint
            | QtCore.Qt.Tool
        )
        self.setModal(True)
        self.setWindowState(QtCore.Qt.WindowFullScreen)
        self.setWindowModality(QtCore.Qt.ApplicationModal)

        # 메인 레이아웃 (여백 없이)
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 전체 화면을 덮는 컨테이너
        container = QtWidgets.QWidget()
        container.setStyleSheet("background-color: rgba(0, 0, 0, 230);")
        
        # 컨테이너 내부 레이아웃
        layout = QtWidgets.QVBoxLayout(container)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        layout.setContentsMargins(100, 100, 100, 100)

        # 축하 제목 (매우 크게)
        label_title = QtWidgets.QLabel("🎉 축하합니다! 🎉")
        label_title.setStyleSheet(
            "font-size: 80px; font-weight: bold; color: #FFD700; "
            "padding: 40px;"
        )
        label_title.setAlignment(QtCore.Qt.AlignCenter)

        # 감지된 옵션 표시 (크게)
        msg = (
            f'"{TARGET_TEXT}"\n\n'
            f"옵션이 감지되었습니다!"
        )
        label_msg = QtWidgets.QLabel(msg)
        label_msg.setStyleSheet(
            "font-size: 40px; color: white; "
            "padding: 30px; line-height: 1.5;"
        )
        label_msg.setAlignment(QtCore.Qt.AlignCenter)

        # 클릭 횟수 표시 (강조)
        label_count = QtWidgets.QLabel(f"총 {click_count}회 클릭")
        label_count.setStyleSheet(
            "font-size: 50px; color: #00FF00; font-weight: bold; "
            "padding: 20px;"
        )
        label_count.setAlignment(QtCore.Qt.AlignCenter)

        # 닫기 버튼 (크게)
        btn_close = QtWidgets.QPushButton("✓ 확인 (ESC / F9 / F10)")
        btn_close.setStyleSheet(
            "font-size: 30px; padding: 20px 60px; "
            "background-color: #4CAF50; color: white; "
            "border-radius: 10px; font-weight: bold;"
        )
        btn_close.clicked.connect(self.accept)

        layout.addStretch()
        layout.addWidget(label_title)
        layout.addSpacing(50)
        layout.addWidget(label_msg)
        layout.addSpacing(40)
        layout.addWidget(label_count)
        layout.addSpacing(60)
        layout.addWidget(btn_close)
        layout.addStretch()

        main_layout.addWidget(container)
        self.setLayout(main_layout)

        # 팝업을 확실히 최상단으로 올리고 포커스를 준다.
        self.raise_()
        self.activateWindow()

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() in (QtCore.Qt.Key_Escape, QtCore.Qt.Key_F9, QtCore.Qt.Key_F10):
            self.accept()
        else:
            super().keyPressEvent(event)


class MacroThread(QtCore.QThread):
    """
    OCR 체크 후 클릭을 수행하는 통합 매크로 쓰레드.
    
    동작 순서:
    1. OCR로 화면 텍스트 확인
    2. 목표 텍스트 감지 시 클릭하지 않고 즉시 중단 (detected 시그널 발생)
    3. 목표 텍스트 없으면 클릭 실행
    4. 100ms 대기 후 반복
    
    이렇게 하면 원하는 옵션이 나타났을 때 추가 클릭으로 넘어가는 것을 방지합니다.
    """

    detected = QtCore.pyqtSignal()
    text_updated = QtCore.pyqtSignal(str)
    click_count_changed = QtCore.pyqtSignal(int)

    def __init__(self, region, reader, interval_ms: int = 100, parent=None):
        super().__init__(parent)
        self.region = region  # (x, y, w, h)
        self.reader = reader
        self.interval_ms = interval_ms
        self._running = True
        self.click_count = 0

    def stop(self) -> None:
        self._running = False

    def run(self) -> None:
        """
        매 반복마다 OCR 체크 → 클릭 순서로 실행
        목표 감지 시 클릭하지 않고 즉시 중단
        """
        print("[MACRO] 통합 매크로 스레드 시작")
        sct = mss.mss()
        x, y, w, h = self.region
        monitor = {"top": y, "left": x, "width": w, "height": h}
        
        pyautogui.keyDown("shift")
        try:
            while self._running:
                # === 1단계: OCR로 화면 체크 (클릭 전에!) ===
                img = np.array(sct.grab(monitor))
                img = img[:, :, :3]  # BGRA -> BGR

                try:
                    results = self.reader.readtext(img, detail=0)
                except Exception:
                    results = []

                joined = " ".join(results)

                # 실시간 OCR 텍스트 UI 전송
                self.text_updated.emit(joined)
                print("[OCR]", joined)

                # === 2단계: 목표 감지 확인 ===
                if is_target_detected(joined):
                    print("[DETECT] ✓✓✓ 목표 감지! 클릭하지 않고 즉시 중단 ✓✓✓")
                    self.detected.emit()
                    break  # 클릭하지 않고 즉시 종료

                # === 3단계: 목표 없으면 클릭 실행 ===
                pyautogui.click()
                self.click_count += 1
                self.click_count_changed.emit(self.click_count)
                print(f"[CLICK] 클릭 실행 (총 {self.click_count}회)")

                # === 4단계: 대기 후 반복 ===
                time.sleep(self.interval_ms / 1000.0)
        
        finally:
            pyautogui.keyUp("shift")
            print("[MACRO] 매크로 스레드 종료, Shift 해제")


class MainWindow(QtWidgets.QMainWindow):
    """
    메인 윈도우.
    - 인식 영역 설정
    - 상태/클릭 수 표시
    - 전역 핫키(F8, F9) 관리
    """

    def __init__(self):
        super().__init__()

        self.setWindowTitle("옵션 감지 매크로 (프로토타입)")
        self.setFixedSize(450, 350)

        central = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central)

        self.label_status = QtWidgets.QLabel("상태: 대기 중")
        self.label_status.setStyleSheet("font-size: 14px;")

        self.label_region = QtWidgets.QLabel("인식 영역: 미설정")
        self.label_region.setStyleSheet("font-size: 12px;")

        btn_set_region = QtWidgets.QPushButton("인식 영역 설정")
        btn_set_region.clicked.connect(self.on_set_region)

        btn_emergency_stop = QtWidgets.QPushButton("긴급 정지 (F9/F10)")
        btn_emergency_stop.setStyleSheet("background-color: #ff4444; color: white; font-weight: bold;")
        btn_emergency_stop.clicked.connect(self.stop_macro)

        # === 클릭 속도 조절 UI ===
        speed_group = QtWidgets.QGroupBox("클릭 속도 설정")
        speed_layout = QtWidgets.QVBoxLayout()
        
        # 슬라이더와 현재 값 표시
        slider_layout = QtWidgets.QHBoxLayout()
        slider_label = QtWidgets.QLabel("클릭 간격:")
        self.speed_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.speed_slider.setMinimum(50)   # 최소 50ms
        self.speed_slider.setMaximum(500)  # 최대 500ms
        self.speed_slider.setValue(100)    # 기본 100ms
        self.speed_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.speed_slider.setTickInterval(50)
        self.speed_slider.valueChanged.connect(self.on_speed_changed)
        
        self.label_speed = QtWidgets.QLabel("100 ms (초당 10회)")
        self.label_speed.setStyleSheet("font-weight: bold; color: #0066cc;")
        
        slider_layout.addWidget(slider_label)
        slider_layout.addWidget(self.speed_slider)
        slider_layout.addWidget(self.label_speed)
        
        # 프리셋 버튼
        preset_layout = QtWidgets.QHBoxLayout()
        btn_fast = QtWidgets.QPushButton("빠름 (50ms)")
        btn_fast.clicked.connect(lambda: self.speed_slider.setValue(50))
        btn_normal = QtWidgets.QPushButton("보통 (100ms)")
        btn_normal.clicked.connect(lambda: self.speed_slider.setValue(100))
        btn_slow = QtWidgets.QPushButton("느림 (200ms)")
        btn_slow.clicked.connect(lambda: self.speed_slider.setValue(200))
        
        preset_layout.addWidget(btn_fast)
        preset_layout.addWidget(btn_normal)
        preset_layout.addWidget(btn_slow)
        
        speed_layout.addLayout(slider_layout)
        speed_layout.addLayout(preset_layout)
        speed_group.setLayout(speed_layout)

        self.label_clicks = QtWidgets.QLabel("현재 클릭 수: 0")
        self.label_clicks.setStyleSheet("font-size: 12px;")

        # 실시간 OCR 텍스트 모니터링 라벨
        self.label_ocr = QtWidgets.QLabel("현재 인식 텍스트: (대기 중)")
        self.label_ocr.setStyleSheet("font-size: 11px; color: gray;")

        self.label_hotkeys = QtWidgets.QLabel(
            "핫키:\nF7 - 인식 영역 설정\nF8 - 매크로 시작/정지\nF9 / F10 - 긴급 정지 (Shift 조합도 가능)"
        )
        self.label_hotkeys.setStyleSheet("font-size: 12px;")

        layout.addWidget(self.label_status)
        layout.addWidget(self.label_region)
        layout.addWidget(btn_set_region)
        layout.addWidget(btn_emergency_stop)
        layout.addSpacing(10)
        layout.addWidget(speed_group)
        layout.addSpacing(10)
        layout.addWidget(self.label_clicks)
        layout.addSpacing(10)
        layout.addWidget(self.label_ocr)
        layout.addSpacing(5)
        layout.addWidget(self.label_hotkeys)

        self.setCentralWidget(central)

        # 상태 변수
        self.region = None
        self.region_overlay = RegionBorderOverlay()
        self.macro_thread = None
        self.macro_running = False
        self.click_count = 0
        self.click_interval_ms = 100  # 기본 클릭 간격
        self.emergency_stop_requested = False
        self.last_f7_state = False
        self.last_f8_state = False
        self.last_f9_state = False
        self.last_f10_state = False

        # OCR 리더 초기화 (한 번만)
        self.reader = easyocr.Reader(["ko", "en"], gpu=False)

        # Qt 단축키 등록 (UI 포커스 시)
        # F7: 인식 영역 설정
        self.shortcut_f7 = QtWidgets.QShortcut(QtGui.QKeySequence("F7"), self)
        self.shortcut_f7.activated.connect(self.on_set_region)
        
        # F8: 매크로 시작/정지
        self.shortcut_f8 = QtWidgets.QShortcut(QtGui.QKeySequence("F8"), self)
        self.shortcut_f8.activated.connect(self.toggle_macro)
        
        # F9/F10: 긴급 정지 (일반 + Shift 조합)
        self.shortcut_f9 = QtWidgets.QShortcut(QtGui.QKeySequence("F9"), self)
        self.shortcut_f9.activated.connect(self.stop_macro)
        self.shortcut_f10 = QtWidgets.QShortcut(QtGui.QKeySequence("F10"), self)
        self.shortcut_f10.activated.connect(self.stop_macro)
        self.shortcut_shift_f9 = QtWidgets.QShortcut(QtGui.QKeySequence("Shift+F9"), self)
        self.shortcut_shift_f9.activated.connect(self.stop_macro)
        self.shortcut_shift_f10 = QtWidgets.QShortcut(QtGui.QKeySequence("Shift+F10"), self)
        self.shortcut_shift_f10.activated.connect(self.stop_macro)

        # 전역 핫키 등록은 별도 스레드에서
        threading.Thread(target=self._register_hotkeys, daemon=True).start()

        # 백그라운드 키 체크 타이머 (50ms마다)
        self.hotkey_timer = QtCore.QTimer(self)
        self.hotkey_timer.timeout.connect(self._check_hotkeys)
        self.hotkey_timer.start(50)  # 50ms마다 체크

    def _register_hotkeys(self) -> None:
        print("[HOTKEY] F7/F8/F9/F10 모두 폴링 방식으로 작동 (백그라운드 지원)")
        print("[HOTKEY] F7 - 인식 영역 설정")
        print("[HOTKEY] F8 - 매크로 시작/정지")
        print("[HOTKEY] F9/F10 - 긴급 정지")

    def _check_hotkeys(self) -> None:
        """
        백그라운드에서도 작동하는 키 체크 (50ms마다 호출됨)
        keyboard.is_pressed()를 사용한 폴링 방식
        """
        try:
            # F7 키 체크 (인식 영역 설정)
            f7_pressed = keyboard.is_pressed('f7')
            if f7_pressed and not self.last_f7_state:
                print("[HOTKEY] F7 눌림 감지 (인식 영역 설정)")
                self.on_set_region()
            self.last_f7_state = f7_pressed

            # F8 키 체크 (매크로 시작/정지)
            f8_pressed = keyboard.is_pressed('f8')
            if f8_pressed and not self.last_f8_state:
                print("[HOTKEY] F8 눌림 감지 (매크로 시작/정지)")
                self.toggle_macro()
            self.last_f8_state = f8_pressed

            # F9 키 체크 (긴급 정지)
            f9_pressed = keyboard.is_pressed('f9')
            if f9_pressed and not self.last_f9_state:
                print("[HOTKEY] F9 눌림 감지 (긴급 정지)")
                self.emergency_stop()
            self.last_f9_state = f9_pressed

            # F10 키 체크 (긴급 정지)
            f10_pressed = keyboard.is_pressed('f10')
            if f10_pressed and not self.last_f10_state:
                print("[HOTKEY] F10 눌림 감지 (긴급 정지)")
                self.emergency_stop()
            self.last_f10_state = f10_pressed

        except Exception as e:
            # 에러 발생 시 조용히 넘어감 (너무 많은 로그 방지)
            pass

    def on_set_region(self) -> None:
        # 오버레이 객체를 인스턴스 속성으로 보관해서 수명 유지
        self.selection_overlay = SelectionOverlay()
        self.selection_overlay.region_selected.connect(self.set_region)
        self.selection_overlay.show()
        # 확실히 맨 위로 올리고 포커스를 준다.
        self.selection_overlay.raise_()
        self.selection_overlay.activateWindow()

    @QtCore.pyqtSlot(int)
    def on_speed_changed(self, value: int) -> None:
        """
        슬라이더 값이 변경되면 클릭 간격을 업데이트한다.
        """
        self.click_interval_ms = value
        clicks_per_sec = 1000.0 / value
        self.label_speed.setText(f"{value} ms (초당 {clicks_per_sec:.1f}회)")
        print(f"[SPEED] 클릭 간격 변경: {value}ms (초당 {clicks_per_sec:.1f}회)")
        
        # 매크로 실행 중이면 스레드에도 적용
        if self.macro_thread and self.macro_thread.isRunning():
            self.macro_thread.interval_ms = value
            print(f"[SPEED] 실행 중인 매크로에 새 속도 적용: {value}ms")

    @QtCore.pyqtSlot(int, int, int, int)
    def set_region(self, x: int, y: int, w: int, h: int) -> None:
        self.region = (x, y, w, h)
        self.label_region.setText(f"인식 영역: x={x}, y={y}, w={w}, h={h}")
        self.region_overlay.set_region(x, y, w, h)

    def toggle_macro(self) -> None:
        # Qt 메인 스레드에서 실행되도록 보장
        QtCore.QMetaObject.invokeMethod(
            self, "_toggle_macro_impl", QtCore.Qt.QueuedConnection
        )

    @QtCore.pyqtSlot()
    def _toggle_macro_impl(self) -> None:
        if self.macro_running:
            self.stop_macro()
        else:
            self.start_macro()

    def start_macro(self) -> None:
        if not self.region:
            QtWidgets.QMessageBox.warning(self, "경고", "먼저 인식 영역을 설정해주세요.")
            return
        if self.macro_running:
            return

        self.macro_running = True
        self.emergency_stop_requested = False
        self.click_count = 0
        self.label_clicks.setText("현재 클릭 수: 0")
        self.label_status.setText(f"상태: 매크로 동작 중 ({self.click_interval_ms}ms 간격)")

        # 통합 매크로 쓰레드 (OCR 체크 후 클릭) - 현재 설정된 속도 사용
        self.macro_thread = MacroThread(self.region, self.reader, interval_ms=self.click_interval_ms)
        self.macro_thread.detected.connect(self.on_detected)
        self.macro_thread.text_updated.connect(self.on_ocr_text_updated)
        self.macro_thread.click_count_changed.connect(self.on_click_count_changed)
        self.macro_thread.start()
        
        print(f"[MACRO] 매크로 시작 - 클릭 간격: {self.click_interval_ms}ms")

    @QtCore.pyqtSlot()
    def stop_macro(self) -> None:
        """
        매크로를 강제로 중지한다.
        macro_running 플래그와 상관없이 매크로 쓰레드를 정리한다.
        """
        print("[MACRO] stop_macro 호출")
        self.macro_running = False
        self.emergency_stop_requested = False
        self.label_status.setText("상태: 대기 중")

        if self.macro_thread:
            print("[MACRO] macro_thread 정지 요청")
            self.macro_thread.stop()
            self.macro_thread.wait(2000)  # 최대 2초 대기
            self.macro_thread = None
            print("[MACRO] macro_thread 정지 완료")

    @QtCore.pyqtSlot()
    def _update_ui_after_stop(self) -> None:
        """
        긴급 정지 후 UI 업데이트 (Qt 메인 스레드에서 실행)
        """
        self.macro_running = False
        self.label_status.setText("상태: 대기 중 (긴급 정지됨)")
        
        # 스레드 정리
        if self.macro_thread:
            self.macro_thread.wait(1000)
            self.macro_thread = None

    @QtCore.pyqtSlot(int)
    def on_click_count_changed(self, count: int) -> None:
        self.click_count = count
        self.label_clicks.setText(f"현재 클릭 수: {count}")

    @QtCore.pyqtSlot()
    def on_detected(self) -> None:
        # 감지 시: 매크로 정지 후 팝업 표시
        self.stop_macro()
        popup = BlockPopup(self.click_count, self)
        popup.exec_()

    @QtCore.pyqtSlot(str)
    def on_ocr_text_updated(self, text: str) -> None:
        """
        DetectorThread에서 보내는 실시간 OCR 텍스트를 UI 라벨에 표시한다.
        """
        shown = text if text else "(없음)"
        self.label_ocr.setText(f"현재 인식 텍스트: {shown}")

    def emergency_stop(self) -> None:
        """
        긴급 정지 - keyboard 라이브러리 콜백에서 호출됨.
        별도 스레드에서 실행되므로 직접 쓰레드를 정지시킨다.
        """
        print("[HOTKEY] emergency_stop 호출됨")
        
        # 플래그 설정
        self.emergency_stop_requested = True
        
        # 직접 쓰레드 정지 (스레드 안전하게)
        if self.macro_thread and self.macro_thread.isRunning():
            print("[HOTKEY] macro_thread 정지 요청")
            self.macro_thread.stop()
        
        # UI 업데이트는 Qt 메인 스레드에서
        QtCore.QMetaObject.invokeMethod(
            self, "_update_ui_after_stop", QtCore.Qt.QueuedConnection
        )

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.stop_macro()
        self.region_overlay.close()
        
        # 타이머 정지
        if hasattr(self, 'hotkey_timer'):
            self.hotkey_timer.stop()
        
        event.accept()


def main() -> None:
    """
    애플리케이션 진입점.
    """
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

