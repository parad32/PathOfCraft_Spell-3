import sys
import threading
import time
import ctypes

import pyautogui
import keyboard
import mss
import numpy as np
import easyocr

from PyQt5 import QtWidgets, QtCore, QtGui

# PyAutoGUI 안전 설정
pyautogui.FAILSAFE = False  # 마우스를 화면 모서리로 이동해도 중단되지 않음
pyautogui.PAUSE = 0.01  # 각 pyautogui 함수 호출 후 0.01초 대기


def safe_click():
    """
    안전한 클릭 함수 - Windows API 사용
    pyautogui가 불안정할 경우 대체
    """
    try:
        # 방법 1: pyautogui 사용
        pyautogui.click()
        return True
    except Exception as e1:
        print(f"[CLICK] pyautogui 클릭 실패, Windows API 사용: {e1}")
        try:
            # 방법 2: Windows API 직접 호출 (더 안정적)
            # WM_LBUTTONDOWN = 0x0201, WM_LBUTTONUP = 0x0202
            import win32api
            import win32con
            x, y = win32api.GetCursorPos()
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
            time.sleep(0.01)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
            return True
        except Exception as e2:
            print(f"[CLICK] Windows API 클릭도 실패: {e2}")
            try:
                # 방법 3: ctypes 사용 (마지막 대안)
                ctypes.windll.user32.mouse_event(2, 0, 0, 0, 0)  # Left down
                time.sleep(0.01)
                ctypes.windll.user32.mouse_event(4, 0, 0, 0, 0)  # Left up
                return True
            except Exception as e3:
                print(f"[CLICK] ctypes 클릭도 실패: {e3}")
                return False


TARGET_TEXT = "모든 주문 스킬레벨 +3"


def check_excluded_option(raw_text: str) -> str:
    """
    제외 옵션(투사체/소환수/근접)인지 확인한다.
    
    Returns:
        str: 제외 키워드 ("투사체", "소환수", "근접") 또는 빈 문자열
    """
    if not raw_text:
        return ""
    
    compact = "".join(raw_text.split())
    
    # 모든, 스킬, 레벨, +3 조건 확인 (간단 버전)
    has_modeun = any(k in compact for k in ["모든", "모듬", "모둔", "보든"])
    has_skill = any(k in compact for k in ["스킬", "스길", "스킨"])
    has_level = any(k in compact for k in ["레벨", "레벌", "레밸", "래벨"])
    has_plus_3 = ("+3" in compact) or ("+ 3" in raw_text)
    
    # 기본 조건이 맞지 않으면 제외 옵션이 아님
    if not (has_modeun and has_skill and has_level and has_plus_3):
        return ""
    
    # 제외 키워드 확인
    exclude_keywords = ["투사체", "소환수", "근접"]
    for exclude in exclude_keywords:
        if exclude in compact:
            print(f"[EXCLUDED] 제외 옵션 감지: {exclude}")
            return exclude
    
    return ""


def is_target_detected(raw_text: str, test_mode: bool = False) -> bool:
    """
    OCR가 인식한 문자열(raw_text)을 받아
    "모든 주문 스킬 레벨 +3" 옵션인지 정확하게 판단한다.

    필수 키워드 (변형 포함):
    1. 모든 (모듬, 모둔)
    2. 주문 (주뭄, 주믄)
    3. 스킬 (스길)
    4. 레벨 (레벌, 레펠)
    5. +3 (반드시 3) - 테스트 모드에서는 +1, +2도 허용

    제외 키워드:
    - 소환수, 투사체, 근접 (이것들이 있으면 False)
    
    Args:
        raw_text: OCR로 인식한 텍스트
        test_mode: True면 +1, +2, +3 모두 성공으로 판정
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

    # === 필수 키워드 5: +1, +2, +3 체크 ===
    if test_mode:
        # 테스트 모드: +1, +2, +3 모두 허용
        has_plus = ("+1" in compact) or ("+2" in compact) or ("+3" in compact) or \
                   ("+ 1" in raw_text) or ("+ 2" in raw_text) or ("+ 3" in raw_text)
        
        if not has_plus:
            print("[MATCH] '+1/+2/+3' 없음 (테스트 모드)")
            return False
        
        print("[MATCH] ✓ 테스트 모드: +1/+2/+3 모두 허용, 조건 만족! True 반환")
        return True
    else:
        # 일반 모드: +3만 허용
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
    클릭 횟수와 제외 옵션 통계를 보여준다.
    """

    def __init__(self, click_count: int, excluded_stats: dict = None, parent=None, auto_close_ms: int = 0):
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
        
        # 제외 옵션 통계 표시 (있으면)
        if excluded_stats:
            total_excluded = sum(excluded_stats.values())
            if total_excluded > 0:
                excluded_text = f"넘긴 옵션: "
                details = []
                if excluded_stats.get("투사체", 0) > 0:
                    details.append(f"투사체 {excluded_stats['투사체']}회")
                if excluded_stats.get("소환수", 0) > 0:
                    details.append(f"소환수 {excluded_stats['소환수']}회")
                if excluded_stats.get("근접", 0) > 0:
                    details.append(f"근접 {excluded_stats['근접']}회")
                
                excluded_text += ", ".join(details) + f" (총 {total_excluded}회)"
                
                label_excluded = QtWidgets.QLabel(excluded_text)
                label_excluded.setStyleSheet(
                    "font-size: 28px; color: #FFA500; font-weight: bold; "
                    "padding: 15px;"
                )
                label_excluded.setAlignment(QtCore.Qt.AlignCenter)

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
        
        # 제외 옵션 통계가 있으면 추가
        if excluded_stats and sum(excluded_stats.values()) > 0:
            layout.addSpacing(30)
            layout.addWidget(label_excluded)
        
        layout.addSpacing(60)
        layout.addWidget(btn_close)
        layout.addStretch()

        main_layout.addWidget(container)
        self.setLayout(main_layout)

        # 팝업을 확실히 최상단으로 올리고 포커스를 준다.
        self.raise_()
        self.activateWindow()
        
        # 자동 닫기 타이머 (연속 제작 모드용)
        if auto_close_ms > 0:
            QtCore.QTimer.singleShot(auto_close_ms, self.accept)
            print(f"[POPUP] 팝업 자동 닫기 타이머 시작: {auto_close_ms}ms")

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
    4. 설정한 간격만큼 대기 후 반복
    
    Shift 키는 매크로 시작 시 자동으로 활성화되고, 종료 시 자동으로 해제됩니다.
    """

    detected = QtCore.pyqtSignal()
    text_updated = QtCore.pyqtSignal(str)
    click_count_changed = QtCore.pyqtSignal(int)
    excluded_detected = QtCore.pyqtSignal(str)  # 제외 옵션 감지 시그널

    def __init__(self, region, reader, interval_ms: int = 100, test_mode: bool = False, keep_shift: bool = False, parent=None):
        super().__init__(parent)
        self.region = region  # (x, y, w, h)
        self.reader = reader
        self.interval_ms = interval_ms
        self.test_mode = test_mode  # 테스트 모드 플래그
        self.keep_shift = keep_shift  # 연속 제작 중 Shift 유지
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
        
        # Shift 키 누름 (keep_shift가 False일 때만)
        shift_activated = False
        if not self.keep_shift:
            pyautogui.keyDown("shift")
            print("[SHIFT] Shift 키 활성화")
            shift_activated = True
        else:
            print("[SHIFT] 연속 제작 모드 - Shift 키 유지 (해제하지 않음)")
        
        try:
            while self._running:
                try:
                    # === 1단계: OCR로 화면 체크 (클릭 전에!) ===
                    img = np.array(sct.grab(monitor))
                    img = img[:, :, :3]  # BGRA -> BGR

                    try:
                        results = self.reader.readtext(img, detail=0)
                    except Exception as e:
                        print(f"[OCR] OCR 읽기 에러: {e}")
                        results = []

                    joined = " ".join(results)

                    # 실시간 OCR 텍스트 UI 전송
                    self.text_updated.emit(joined)
                    print("[OCR]", joined)

                    # === 2단계: 목표 감지 확인 ===
                    if is_target_detected(joined, test_mode=self.test_mode):
                        print("[DETECT] ✓✓✓ 목표 감지! 클릭하지 않고 즉시 중단 ✓✓✓")
                        self.detected.emit()
                        break  # 클릭하지 않고 즉시 종료
                    
                    # === 2-1단계: 제외 옵션 감지 확인 ===
                    excluded_keyword = check_excluded_option(joined)
                    if excluded_keyword:
                        self.excluded_detected.emit(excluded_keyword)

                    # === 3단계: 목표 없으면 클릭 실행 ===
                    print(f"[CLICK] 클릭 시도 중...")
                    click_success = safe_click()
                    if click_success:
                        self.click_count += 1
                        self.click_count_changed.emit(self.click_count)
                        print(f"[CLICK] 클릭 실행 완료 (총 {self.click_count}회)")
                    else:
                        print(f"[CLICK] 클릭 실패, 계속 진행...")

                    # === 4단계: 대기 후 반복 ===
                    time.sleep(self.interval_ms / 1000.0)
                    
                except Exception as e:
                    print(f"[ERROR] 매크로 루프 중 에러 발생: {e}")
                    import traceback
                    traceback.print_exc()
                    time.sleep(0.1)  # 에러 발생 시 잠시 대기 후 계속
        
        finally:
            # Shift 키 해제 (직접 활성화했을 때만)
            if shift_activated:
                pyautogui.keyUp("shift")
                print("[SHIFT] Shift 키 해제")
            else:
                print("[SHIFT] 연속 제작 모드 - Shift 키 유지 (계속 활성 상태)")
            print("[MACRO] 매크로 스레드 종료")


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
        self.setFixedSize(550, 680)  # 테스트 모드 UI 추가로 크기 확장

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
        self.speed_slider.setTickInterval(10)  # 10ms 단위로 눈금 표시
        self.speed_slider.setSingleStep(10)     # 10ms 단위로 조절
        self.speed_slider.valueChanged.connect(self.on_speed_changed)
        
        self.label_speed = QtWidgets.QLabel("100 ms (초당 10.0회)")
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
        
        # === 테스트 모드 UI ===
        test_group = QtWidgets.QGroupBox("테스트 모드")
        test_layout = QtWidgets.QVBoxLayout()
        
        self.checkbox_test_mode = QtWidgets.QCheckBox("테스트 모드 활성화 (+1, +2, +3 모두 성공)")
        self.checkbox_test_mode.setStyleSheet("font-size: 12px; color: #FF6600; font-weight: bold;")
        self.checkbox_test_mode.stateChanged.connect(self.on_test_mode_changed)
        
        test_info = QtWidgets.QLabel("※ 활성화 시: 모든 주문 스킬 레벨 +1, +2, +3 모두 감지\n※ 비활성화 시: +3만 감지 (일반 모드)")
        test_info.setStyleSheet("font-size: 10px; color: gray;")
        
        test_layout.addWidget(self.checkbox_test_mode)
        test_layout.addWidget(test_info)
        test_group.setLayout(test_layout)

        # === 연속 제작 설정 UI ===
        batch_group = QtWidgets.QGroupBox("연속 제작 설정")
        batch_layout = QtWidgets.QVBoxLayout()
        
        # 제작할 아이템 개수 (12x5 그리드 = 최대 60개)
        item_count_layout = QtWidgets.QHBoxLayout()
        item_count_label = QtWidgets.QLabel("제작할 아이템 개수:")
        self.spinbox_item_count = QtWidgets.QSpinBox()
        self.spinbox_item_count.setMinimum(1)
        self.spinbox_item_count.setMaximum(60)
        self.spinbox_item_count.setValue(1)
        self.spinbox_item_count.setSuffix(" 개 (최대 12x5=60)")
        item_count_layout.addWidget(item_count_label)
        item_count_layout.addWidget(self.spinbox_item_count)
        item_count_layout.addStretch()
        
        # 가로 간격 (X축) - 한 줄에 12개
        move_distance_layout = QtWidgets.QHBoxLayout()
        move_distance_label = QtWidgets.QLabel("가로 간격 (X축):")
        self.spinbox_move_distance = QtWidgets.QSpinBox()
        self.spinbox_move_distance.setMinimum(0)
        self.spinbox_move_distance.setMaximum(500)
        self.spinbox_move_distance.setValue(60)
        self.spinbox_move_distance.setSuffix(" px")
        move_distance_layout.addWidget(move_distance_label)
        move_distance_layout.addWidget(self.spinbox_move_distance)
        move_distance_layout.addStretch()
        
        # 세로 간격 (Y축) - 12개 끝나면 아래 줄로
        row_distance_layout = QtWidgets.QHBoxLayout()
        row_distance_label = QtWidgets.QLabel("줄 간격 (Y축):")
        self.spinbox_row_distance = QtWidgets.QSpinBox()
        self.spinbox_row_distance.setMinimum(0)
        self.spinbox_row_distance.setMaximum(500)
        self.spinbox_row_distance.setValue(60)
        self.spinbox_row_distance.setSuffix(" px")
        row_distance_layout.addWidget(row_distance_label)
        row_distance_layout.addWidget(self.spinbox_row_distance)
        row_distance_layout.addStretch()
        
        # 완성 후 대기 시간
        wait_time_layout = QtWidgets.QHBoxLayout()
        wait_time_label = QtWidgets.QLabel("완성 후 대기 시간:")
        self.spinbox_wait_time = QtWidgets.QSpinBox()
        self.spinbox_wait_time.setMinimum(0)
        self.spinbox_wait_time.setMaximum(30)
        self.spinbox_wait_time.setValue(5)  # 기본값 5초
        self.spinbox_wait_time.setSuffix(" 초")
        wait_time_layout.addWidget(wait_time_label)
        wait_time_layout.addWidget(self.spinbox_wait_time)
        wait_time_layout.addStretch()
        
        # 현재 진행 상황
        self.label_batch_progress = QtWidgets.QLabel("진행: 0 / 1")
        self.label_batch_progress.setStyleSheet("font-size: 12px; font-weight: bold; color: #0066cc;")
        
        batch_layout.addLayout(item_count_layout)
        batch_layout.addLayout(move_distance_layout)
        batch_layout.addLayout(row_distance_layout)
        batch_layout.addLayout(wait_time_layout)
        batch_layout.addWidget(self.label_batch_progress)
        batch_group.setLayout(batch_layout)

        # === 마우스 이동 감지 (강제 정지) ===
        safety_group = QtWidgets.QGroupBox("마우스 이동 감지 (강제 정지)")
        safety_layout = QtWidgets.QHBoxLayout()
        safety_label = QtWidgets.QLabel("감지 거리:")
        self.spinbox_mouse_stop_distance = QtWidgets.QSpinBox()
        self.spinbox_mouse_stop_distance.setMinimum(0)
        self.spinbox_mouse_stop_distance.setMaximum(500)
        self.spinbox_mouse_stop_distance.setValue(100)
        self.spinbox_mouse_stop_distance.setSuffix(" px (0=비활성화)")
        safety_info = QtWidgets.QLabel("매크로 중 사용자가 마우스를 이 거리 이상 움직이면 강제 정지")
        safety_info.setStyleSheet("font-size: 10px; color: gray;")
        safety_layout.addWidget(safety_label)
        safety_layout.addWidget(self.spinbox_mouse_stop_distance)
        safety_layout.addWidget(safety_info)
        safety_layout.addStretch()
        safety_group.setLayout(safety_layout)

        # === 마우스 좌표 표시 ===
        status_group = QtWidgets.QGroupBox("마우스 좌표 (실시간)")
        status_layout = QtWidgets.QHBoxLayout()
        self.label_mouse_pos = QtWidgets.QLabel("X: 0, Y: 0")
        self.label_mouse_pos.setStyleSheet("font-size: 14px; font-family: monospace; color: #00AA00;")
        status_layout.addWidget(self.label_mouse_pos)
        status_group.setLayout(status_layout)

        self.label_clicks = QtWidgets.QLabel("현재 클릭 수: 0")
        self.label_clicks.setStyleSheet("font-size: 12px;")

        # 실시간 OCR 텍스트 모니터링 라벨
        self.label_ocr = QtWidgets.QLabel("현재 인식 텍스트: (대기 중)")
        self.label_ocr.setStyleSheet("font-size: 11px; color: gray;")

        self.label_hotkeys = QtWidgets.QLabel(
            "핫키:\nF7 - 인식 영역 설정\nF8 - 매크로 시작\nF9 / F10 - 매크로 정지"
        )
        self.label_hotkeys.setStyleSheet("font-size: 12px;")

        layout.addWidget(self.label_status)
        layout.addWidget(self.label_region)
        layout.addWidget(btn_set_region)
        layout.addWidget(btn_emergency_stop)
        layout.addSpacing(10)
        layout.addWidget(test_group)
        layout.addSpacing(10)
        layout.addWidget(speed_group)
        layout.addSpacing(10)
        layout.addWidget(batch_group)
        layout.addSpacing(10)
        layout.addWidget(safety_group)
        layout.addSpacing(10)
        layout.addWidget(status_group)
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
        self.excluded_stats = {"투사체": 0, "소환수": 0, "근접": 0}  # 제외 옵션 통계
        self.emergency_stop_requested = False
        self.last_f7_state = False
        self.last_f8_state = False
        self.last_f9_state = False
        self.last_f10_state = False
        self.test_mode = False  # 테스트 모드 플래그
        
        # 연속 제작 관련 변수
        self.batch_mode = False  # 연속 제작 모드 여부
        self.current_item_index = 0  # 현재 제작 중인 아이템 인덱스 (0부터 시작)
        self.initial_region = None  # 최초 설정한 인식 영역 (백업용)
        
        # 마우스 이동 감지 (강제 정지용)
        self.mouse_anchor = None  # (x, y) - 매크로 시작/다음 아이템 이동 시 기준점

        # OCR 리더 초기화 (한 번만)
        self.reader = easyocr.Reader(["ko", "en"], gpu=False)

        # Qt 단축키 등록 (UI 포커스 시)
        # F7: 인식 영역 설정
        self.shortcut_f7 = QtWidgets.QShortcut(QtGui.QKeySequence("F7"), self)
        self.shortcut_f7.activated.connect(self.on_set_region)
        self.shortcut_shift_f7 = QtWidgets.QShortcut(QtGui.QKeySequence("Shift+F7"), self)
        self.shortcut_shift_f7.activated.connect(self.on_set_region)
        
        # F8: 매크로 시작
        self.shortcut_f8 = QtWidgets.QShortcut(QtGui.QKeySequence("F8"), self)
        self.shortcut_f8.activated.connect(self.start_macro)
        self.shortcut_shift_f8 = QtWidgets.QShortcut(QtGui.QKeySequence("Shift+F8"), self)
        self.shortcut_shift_f8.activated.connect(self.start_macro)
        
        # F9/F10: 매크로 정지 (일반 + Shift 조합)
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
        
        # 마우스 좌표 업데이트 타이머 (100ms마다)
        self.mouse_timer = QtCore.QTimer(self)
        self.mouse_timer.timeout.connect(self._update_mouse_position)
        self.mouse_timer.start(100)  # 100ms마다 업데이트
        
        # 마우스 이동 감지 타이머 (300ms마다) - 일정 거리 이상 벗어나면 강제 정지
        self.mouse_watch_timer = QtCore.QTimer(self)
        self.mouse_watch_timer.timeout.connect(self._check_mouse_moved)
        self.mouse_watch_timer.start(300)

    def _register_hotkeys(self) -> None:
        print("[HOTKEY] F7/F8/F9/F10 모두 폴링 방식으로 작동 (백그라운드 지원)")
        print("[HOTKEY] Shift 조합도 모두 지원")
        print("[HOTKEY] F7 / Shift+F7 - 인식 영역 설정")
        print("[HOTKEY] F8 / Shift+F8 - 매크로 시작")
        print("[HOTKEY] F9 / F10 / Shift+F9 / Shift+F10 - 매크로 정지")
    
    def _update_mouse_position(self) -> None:
        """
        현재 마우스 좌표를 UI에 업데이트 (100ms마다 호출)
        """
        try:
            x, y = pyautogui.position()
            self.label_mouse_pos.setText(f"X: {x}, Y: {y}")
        except Exception:
            pass
    
    def _check_mouse_moved(self) -> None:
        """
        매크로 중 사용자가 마우스를 설정 거리 이상 움직였으면 강제 정지 (300ms마다 호출)
        """
        try:
            if not self.macro_running or self.mouse_anchor is None:
                return
            threshold = self.spinbox_mouse_stop_distance.value()
            if threshold <= 0:
                return
            cur_x, cur_y = pyautogui.position()
            ax, ay = self.mouse_anchor
            dist = ((cur_x - ax) ** 2 + (cur_y - ay) ** 2) ** 0.5
            if dist > threshold:
                print(f"[MOUSE] 마우스 이동 감지 ({dist:.0f}px > {threshold}px) - 강제 정지")
                self.mouse_anchor = None
                self.stop_macro()
        except Exception:
            pass

    def _check_hotkeys(self) -> None:
        """
        백그라운드에서도 작동하는 키 체크 (50ms마다 호출됨)
        keyboard.is_pressed()를 사용한 폴링 방식
        """
        try:
            # F7 키 체크 (인식 영역 설정) - Shift 상태 무관
            f7_pressed = keyboard.is_pressed('f7')
            if f7_pressed and not self.last_f7_state:
                print("[HOTKEY] F7 눌림 감지 (인식 영역 설정)")
                self.on_set_region()
            self.last_f7_state = f7_pressed

            # F8 키 체크 (매크로 시작) - Shift 상태 무관
            f8_pressed = keyboard.is_pressed('f8')
            if f8_pressed and not self.last_f8_state:
                print("[HOTKEY] F8 눌림 감지 (매크로 시작)")
                self.start_macro()
            self.last_f8_state = f8_pressed

            # F9 키 체크 (매크로 정지) - Shift 상태 무관
            f9_pressed = keyboard.is_pressed('f9')
            if f9_pressed and not self.last_f9_state:
                print("[HOTKEY] F9 눌림 감지 (매크로 정지)")
                self.stop_macro()
            self.last_f9_state = f9_pressed

            # F10 키 체크 (매크로 정지) - Shift 상태 무관
            f10_pressed = keyboard.is_pressed('f10')
            if f10_pressed and not self.last_f10_state:
                print("[HOTKEY] F10 눌림 감지 (매크로 정지)")
                self.stop_macro()
            self.last_f10_state = f10_pressed

        except Exception as e:
            # 에러 발생 시 조용히 넘어감 (너무 많은 로그 방지
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
    
    @QtCore.pyqtSlot(int)
    def on_test_mode_changed(self, state: int) -> None:
        """
        테스트 모드 체크박스가 변경되면 호출됨
        """
        self.test_mode = (state == QtCore.Qt.Checked)
        if self.test_mode:
            print("[TEST] 테스트 모드 활성화: +1, +2, +3 모두 감지")
        else:
            print("[TEST] 일반 모드: +3만 감지")

    @QtCore.pyqtSlot(int, int, int, int)
    def set_region(self, x: int, y: int, w: int, h: int) -> None:
        self.region = (x, y, w, h)
        # F7로 설정할 때마다 초기 영역 업데이트 (연속 제작의 시작점)
        self.initial_region = (x, y, w, h)
        print(f"[REGION] 인식 영역 설정: x={x}, y={y}, w={w}, h={h}")
        self.label_region.setText(f"인식 영역: x={x}, y={y}, w={w}, h={h}")
        self.region_overlay.set_region(x, y, w, h)

    def start_macro(self) -> None:
        try:
            if not self.region:
                QtWidgets.QMessageBox.warning(self, "경고", "먼저 인식 영역을 설정해주세요.")
                return
            if self.macro_running:
                return

            self.macro_running = True
            self.emergency_stop_requested = False
            self.click_count = 0
            self.excluded_stats = {"투사체": 0, "소환수": 0, "근접": 0}  # 제외 옵션 통계 초기화
            self.label_clicks.setText("현재 클릭 수: 0")
            
            # 연속 제작 모드 설정
            total_items = self.spinbox_item_count.value()
            if total_items > 1:
                self.batch_mode = True
                self.current_item_index = 0
                # 초기 영역으로 리셋
                if self.initial_region:
                    self.region = self.initial_region
                    x, y, w, h = self.initial_region
                    self.label_region.setText(f"인식 영역: x={x}, y={y}, w={w}, h={h}")
                    self.region_overlay.set_region(x, y, w, h)
                print(f"[BATCH] 연속 제작 모드 시작: {total_items}개 아이템")
                # 연속 제작 모드일 때는 미리 Shift 활성화
                pyautogui.keyDown("shift")
                print(f"[SHIFT] 연속 제작 시작 - Shift 키 미리 활성화")
            else:
                self.batch_mode = False
                self.current_item_index = 0
                print("[BATCH] 단일 제작 모드")
            
            self._update_batch_progress()
            self.label_status.setText(f"상태: 매크로 동작 중 ({self.click_interval_ms}ms 간격)")
            
            # 마우스 이동 감지용 기준점 (매크로 시작 시점의 마우스 위치)
            self.mouse_anchor = pyautogui.position()

            # 통합 매크로 쓰레드 (OCR 체크 후 클릭) - 현재 설정된 속도 사용
            # 연속 제작 모드이면 항상 keep_shift=True (이미 Shift가 활성화되어 있음)
            keep_shift = self.batch_mode
            
            self.macro_thread = MacroThread(
                self.region, 
                self.reader, 
                interval_ms=self.click_interval_ms,
                test_mode=self.test_mode,
                keep_shift=keep_shift
            )
            self.macro_thread.detected.connect(self.on_detected)
            self.macro_thread.text_updated.connect(self.on_ocr_text_updated)
            self.macro_thread.click_count_changed.connect(self.on_click_count_changed)
            self.macro_thread.excluded_detected.connect(self.on_excluded_detected)
            self.macro_thread.start()
            
            mode_text = "테스트 모드 (+1/+2/+3)" if self.test_mode else "일반 모드 (+3만)"
            shift_text = "Shift 유지" if keep_shift else "Shift 자동 활성화"
            print(f"[MACRO] 매크로 시작 - 클릭 간격: {self.click_interval_ms}ms ({shift_text}) [{mode_text}]")
        
        except Exception as e:
            import traceback
            error_msg = f"[ERROR] start_macro 실행 중 에러 발생:\n{traceback.format_exc()}"
            print(error_msg)
            
            # 에러 로그 파일 저장
            try:
                with open("error_log.txt", "a", encoding="utf-8") as f:
                    f.write(f"\n\n{'='*50}\n")
                    f.write(f"start_macro Error - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"{'='*50}\n")
                    f.write(traceback.format_exc())
            except:
                pass
            
            self.macro_running = False
            self.label_status.setText("상태: 에러 발생 (error_log.txt 확인)")
            QtWidgets.QMessageBox.critical(
                self, 
                "에러", 
                f"매크로 시작 중 에러가 발생했습니다.\n\nerror_log.txt 파일을 확인해주세요.\n\n에러: {str(e)}"
            )

    @QtCore.pyqtSlot()
    def stop_macro(self) -> None:
        """
        매크로를 강제로 중지한다.
        macro_running 플래그와 상관없이 매크로 쓰레드를 정리한다.
        """
        print("[MACRO] stop_macro 호출")
        
        self.macro_running = False
        self.batch_mode = False  # 연속 제작 모드 해제
        self.emergency_stop_requested = False
        self.mouse_anchor = None  # 마우스 이동 감지 해제
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

    def _update_batch_progress(self) -> None:
        """
        연속 제작 진행 상황을 UI에 업데이트
        """
        total_items = self.spinbox_item_count.value()
        current = self.current_item_index + 1  # 1부터 시작하도록 표시
        self.label_batch_progress.setText(f"진행: {current} / {total_items}")
        print(f"[BATCH] 진행 상황: {current} / {total_items}")

    @QtCore.pyqtSlot(int)
    def on_click_count_changed(self, count: int) -> None:
        self.click_count = count
        self.label_clicks.setText(f"현재 클릭 수: {count}")

    @QtCore.pyqtSlot()
    def on_detected(self) -> None:
        """
        목표 옵션 감지 시 호출됨.
        연속 제작 모드인 경우 다음 아이템으로 자동 이동.
        """
        # 매크로 정지
        self.macro_running = False
        if self.macro_thread:
            self.macro_thread.stop()
            self.macro_thread.wait(1000)
            self.macro_thread = None
        
        # 연속 제작 모드 처리
        if self.batch_mode:
            total_items = self.spinbox_item_count.value()
            self.current_item_index += 1
            
            if self.current_item_index < total_items:
                # 연속 제작 중 - 팝업 없이 바로 다음 아이템으로 진행
                # Shift는 유지됨!
                print(f"[SHIFT] 연속 제작 중 - Shift 키 유지 (해제하지 않음)")
                print(f"[BATCH] 연속 제작 중: 팝업 없이 즉시 다음 아이템으로 진행 ({self.current_item_index}/{total_items})")
                print(f"[BATCH] 현재 아이템 {self.current_item_index}: 클릭 {self.click_count}회로 완료")
                
                # 다음 아이템으로 이동
                wait_time = self.spinbox_wait_time.value()
                
                print(f"[BATCH] {wait_time}초 대기 후 다음 아이템으로 이동...")
                self.label_status.setText(f"상태: 아이템 {self.current_item_index} 완료, {wait_time}초 대기 중...")
                
                # 대기 시간 (Shift 유지)
                QtCore.QTimer.singleShot(wait_time * 1000, self._move_to_next_item)
            else:
                # 모든 아이템 제작 완료 - Shift 해제 후 팝업 표시
                print(f"[SHIFT] 모든 제작 완료 - Shift 키 해제")
                pyautogui.keyUp("shift")
                
                print("[BATCH] 모든 아이템 제작 완료 - 팝업 표시")
                popup = BlockPopup(self.click_count, self.excluded_stats, self)
                popup.exec_()
                
                self.batch_mode = False
                self.label_status.setText("상태: 연속 제작 완료!")
                QtWidgets.QMessageBox.information(
                    self, 
                    "완료", 
                    f"총 {total_items}개 아이템 제작이 완료되었습니다!"
                )
        else:
            # 단일 제작 모드 - Shift 해제 후 팝업 표시
            print(f"[SHIFT] 단일 제작 완료 - Shift 키 해제")
            pyautogui.keyUp("shift")
            
            print("[SINGLE] 단일 제작 모드 - 팝업 표시")
            popup = BlockPopup(self.click_count, self.excluded_stats, self)
            popup.exec_()
            self.label_status.setText("상태: 대기 중")
    
    def _move_to_next_item(self) -> None:
        """
        다음 아이템으로 마우스와 인식 영역을 이동.
        그리드: 가로 12개 x 세로 5줄 = 최대 60개.
        첫 인식 영역 = (0,0), 12개 끝나면 아래 줄로 이동 후 가로는 처음부터.
        """
        if not self.initial_region:
            print("[BATCH] 오류: initial_region 없음")
            return
        
        move_distance = self.spinbox_move_distance.value()
        row_distance = self.spinbox_row_distance.value()
        
        # 현재 이동할 아이템 인덱스 (0-based). current_item_index는 on_detected에서 이미 +1 됨
        idx = self.current_item_index
        col = idx % 12   # 가로 위치 (0~11)
        row = idx // 12  # 세로 줄 (0~4)
        
        init_x, init_y, w, h = self.initial_region
        new_region_x = init_x + col * move_distance
        new_region_y = init_y + row * row_distance
        
        print(f"[SHIFT] Shift 키 유지 중 (활성 상태)")
        print(f"[BATCH] 다음 아이템으로 이동: 인덱스 {idx} → 그리드 ({row+1}줄, {col+1}번)")
        
        # 마우스: 현재 박스 내 상대 위치를 유지하여 다음 박스로 이동
        if self.region:
            cur_x, cur_y = pyautogui.position()
            old_rx, old_ry, _, _ = self.region
            offset_x = cur_x - old_rx
            offset_y = cur_y - old_ry
            new_mouse_x = new_region_x + offset_x
            new_mouse_y = new_region_y + offset_y
            pyautogui.moveTo(new_mouse_x, new_mouse_y, duration=0.3)
            print(f"[BATCH] 마우스 이동: ({cur_x}, {cur_y}) → ({new_mouse_x}, {new_mouse_y})")
        
        # 마우스 이동 감지 기준점을 새 위치로 갱신 (프로그램 이동이므로 강제 정지 방지)
        self.mouse_anchor = pyautogui.position()
        
        self.region = (new_region_x, new_region_y, w, h)
        self.label_region.setText(f"인식 영역: x={new_region_x}, y={new_region_y}, w={w}, h={h}")
        self.region_overlay.set_region(new_region_x, new_region_y, w, h)
        print(f"[BATCH] 인식 영역 이동: ({row+1}줄, {col+1}번) x={new_region_x}, y={new_region_y}")
        
        # 진행 상황 업데이트
        self._update_batch_progress()
        
        # 다음 아이템 제작 시작
        self.macro_running = True
        self.click_count = 0
        self.excluded_stats = {"투사체": 0, "소환수": 0, "근접": 0}
        self.label_clicks.setText("현재 클릭 수: 0")
        self.label_status.setText(f"상태: 매크로 동작 중 ({self.click_interval_ms}ms 간격)")
        
        print(f"[SHIFT] 새로운 MacroThread 시작 - Shift 키 유지 (keep_shift=True)")
        self.macro_thread = MacroThread(
            self.region,
            self.reader,
            interval_ms=self.click_interval_ms,
            test_mode=self.test_mode,
            keep_shift=True
        )
        self.macro_thread.detected.connect(self.on_detected)
        self.macro_thread.text_updated.connect(self.on_ocr_text_updated)
        self.macro_thread.click_count_changed.connect(self.on_click_count_changed)
        self.macro_thread.excluded_detected.connect(self.on_excluded_detected)
        self.macro_thread.start()
        
        print(f"[BATCH] 아이템 {self.current_item_index + 1} 제작 시작")
    
    @QtCore.pyqtSlot(str)
    def on_excluded_detected(self, excluded_keyword: str) -> None:
        """
        제외 옵션 감지 시 카운트 증가
        """
        if excluded_keyword in self.excluded_stats:
            self.excluded_stats[excluded_keyword] += 1
            total = sum(self.excluded_stats.values())
            print(f"[EXCLUDED] {excluded_keyword} 카운트 증가: {self.excluded_stats[excluded_keyword]}회 (총 {total}회)")

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
    try:
        app = QtWidgets.QApplication(sys.argv)
        win = MainWindow()
        win.show()
        sys.exit(app.exec_())
    except Exception as e:
        # 에러를 파일로 저장
        import traceback
        error_log = f"""
========================================
ERROR LOG - {time.strftime('%Y-%m-%d %H:%M:%S')}
========================================

{traceback.format_exc()}

========================================
"""
        try:
            with open("error_log.txt", "w", encoding="utf-8") as f:
                f.write(error_log)
            print("[ERROR] 에러가 발생했습니다. error_log.txt 파일을 확인해주세요.")
            print(error_log)
        except:
            print("[ERROR] 에러 로그 저장 실패")
            print(error_log)
        
        # 에러 메시지 표시 후 대기
        input("\n\n에러 확인 후 Enter 키를 눌러 종료하세요...")


if __name__ == "__main__":
    main()

