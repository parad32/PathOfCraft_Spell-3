import re
import sys
import time

import pyautogui
import keyboard
import mss
import numpy as np
import easyocr

from PyQt5 import QtWidgets, QtCore, QtGui


OPTION_DISPLAY = {
    "주문":  "모든 주문 스킬레벨 +3",
    "근접":  "모든 근접 스킬레벨 +3",
    "투사체": "모든 투사체 스킬레벨 +3",
    "소환수": "모든 소환수 스킬레벨 +3",
}


def detect_option_type(raw_text: str) -> str:
    """
    조건: 종류 키워드(주문/근접/투사체/소환수) + '+3' 두 가지만 체크.
    감지 성공 시 종류 문자열, 아니면 "" 반환.
    """
    if not raw_text:
        return ""

    compact = "".join(raw_text.split())
    print("[MATCH] compact:", compact)

    # +3 체크 (정규식으로 +1/+2 오탐 방지)
    if not re.search(r'\+\s*3', raw_text):
        print("[MATCH] '+3' 없음")
        return ""
    if re.search(r'\+\s*[12](?!\d)', raw_text):
        print("[MATCH] +1/+2 감지 — 제외")
        return ""

    # ══════════════════════════════════════════════════════════════════════
    # 주문
    # 주: ㅈ(→ㅊ/ㅉ/ㅅ/ㅆ/ㄷ/ㄸ/ㄹ/ㄴ/ㄱ) × ㅜ(→ㅡ/ㅗ/ㅠ/ㅛ/ㅓ/ㅣ)
    # 문: ㅁ(→ㄴ/ㅂ/ㅍ/ㄹ/ㅎ/ㅇ/ㄷ/ㄱ) × ㅜ(→ㅡ/ㅗ/ㅠ/ㅓ/ㅣ/ㅔ)
    #     받침ㄴ(→ㄹ/ㄷ/ㅁ/ㅅ/ㅇ/ㄱ/탈락)
    # ══════════════════════════════════════════════════════════════════════
    keyword_jumun = [
        # ── 주 + 문 기본 / 문 모음 변형 ──
        "주문", "주믄", "주몬", "주뮨", "주먼", "주민", "주멘", "주맨",
        # ── 주 + 문 받침 변형 (ㄴ→ㄹ/ㄷ/ㅁ/ㅅ/ㅇ/ㄱ/탈락) ──
        "주물", "주묻", "주뭄", "주뭇", "주뭉", "주묵", "주무",
        "주뭣", "주뭐",
        # ── 주 + 문 초성 ㅁ→ㅂ ──
        "주분", "주본", "주빈", "주번", "주벤", "주붕",
        # ── 주 + 문 초성 ㅁ→ㅍ ──
        "주폰", "주픈", "주푼", "주핀", "주펀", "주풍",
        # ── 주 + 문 초성 ㅁ→ㄹ ──
        "주론", "주룬", "주른", "주렌", "주랜", "주릉",
        # ── 주 + 문 초성 ㅁ→ㄴ ──
        "주눈", "주논", "주는", "주닌", "주넌",
        # ── 주 + 문 초성 ㅁ→ㅎ ──
        "주혼", "주훈", "주흔", "주헌", "주흥",
        # ── 주 + 문 초성 ㅁ→ㅇ ──
        "주온", "주운", "주은", "주언", "주응",
        # ── 주 + 문 초성 ㅁ→ㄷ/ㄱ ──
        "주돈", "주든", "주던",
        "주곤", "주근", "주건",
        # ── 추 (ㅈ→ㅊ) + 문 변형 ──
        "추문", "추믄", "추몬", "추뮨", "추먼",
        "추뭄", "추물", "추뭉", "추묵",
        "추분", "추본", "추론", "추눈",
        # ── 쭈 (ㅈ→ㅉ) + 문 변형 ──
        "쭈문", "쭈믄", "쭈몬", "쭈뮨",
        "쭈뭄", "쭈물", "쭈분", "쭈뭉",
        # ── 쥬 (ㅜ→ㅠ) + 문 변형 ──
        "쥬문", "쥬믄", "쥬몬", "쥬뮨", "쥬먼",
        "쥬뭄", "쥬물", "쥬뭉",
        "쥬분", "쥬본", "쥬론",
        # ── 죠 (ㅜ→ㅛ) + 문 변형 ──
        "죠문", "죠믄", "죠몬", "죠뭄", "죠분",
        # ── 즈 (ㅜ→ㅡ) + 문 변형 ──
        "즈문", "즈믄", "즈몬", "즈뭄",
        # ── 조 (ㅜ→ㅗ) + 문 변형 ──
        "조문", "조믄", "조몬", "조뭄", "조분",
        # ── 저 (ㅜ→ㅓ) + 문 변형 ──
        "저문", "저믄", "저몬", "저뭄",
        # ── 지 (ㅜ→ㅣ) + 문 변형 ──
        "지문", "지믄", "지몬",
        # ── 수 (ㅈ→ㅅ) + 문 변형 ──
        "수문", "수믄", "수몬", "수뭄", "수분",
        # ── 두/뚜 (ㅈ→ㄷ/ㄸ) + 문 변형 ──
        "두문", "두믄", "두몬", "두뭄",
        "뚜문", "뚜믄",
        # ── 루 (ㅈ→ㄹ) + 문 변형 ──
        "루문", "루믄", "루몬",
        # ── 누 (ㅈ→ㄴ) + 문 변형 ──
        "누문", "누믄",
        # ── 구 (ㅈ→ㄱ) + 문 변형 ──
        "구문", "구믄",
        # ── 기타 혼동 ──
        "쥐문", "쥐믄",
        "줌문", "줌뭄",
        "주뭔", "주므", "주밀", "주믈",
    ]

    # ══════════════════════════════════════════════════════════════════════
    # 근접
    # 근: ㄱ(→ㄲ/ㅋ/ㄴ/ㄷ/ㄸ/ㄹ/ㄻ/ㅁ/ㅂ) × ㅡ(→ㅣ/ㅜ/ㅓ/ㅗ/ㅏ)
    #     받침ㄴ(→ㄹ/ㄷ/ㅁ/ㅂ/ㅇ/탈락)
    # 접: ㅈ(→ㅊ/ㅉ/ㅅ/ㅆ/ㄷ) × ㅓ(→ㅜ/ㅏ/ㅔ/ㅣ/ㅡ/ㅗ)
    #     받침ㅂ(→ㅅ/ㄱ/ㄴ/ㄹ/ㅁ/ㅇ/탈락)
    # ══════════════════════════════════════════════════════════════════════
    keyword_gunjub = [
        # ── 근 + 접 기본 / 접 모음 변형 ──
        "근접", "근줍", "근잡", "근젭", "근집", "근즙", "근좁", "근잽",
        # ── 근 + 접 받침 변형 (ㅂ→ㅅ/ㄱ/ㄴ/ㄹ/ㅁ/ㅇ/탈락) ──
        "근젓", "근적", "근전", "근절", "근점", "근정", "근저",
        "근젠", "근젤", "근젬", "근젱",
        # ── 근 + 접 초성 ㅈ→ㅊ ──
        "근첩", "근쳡", "근쳐", "근처", "근쳔", "근최",
        # ── 근 + 접 초성 ㅈ→ㅉ ──
        "근쩝", "근쩜", "근쪼", "근쪽",
        # ── 근 + 접 초성 ㅈ→ㅅ/ㅆ ──
        "근섭", "근셥", "근솝", "근샵",
        # ── 긴 (ㅡ→ㅣ, 가장 흔한 근 오인식) + 접 변형 ──
        "긴접", "긴줍", "긴잡", "긴젭", "긴집", "긴즙",
        "긴첩", "긴쩝", "긴전", "긴절", "긴정", "긴적", "긴저",
        "긴젠", "긴젤", "긴섭",
        # ── 군 (ㅡ→ㅜ) + 접 변형 ──
        "군접", "군줍", "군잡", "군젭", "군집",
        "군첩", "군전", "군절", "군젓", "군적",
        # ── 건 (ㅡ→ㅓ) + 접 변형 ──
        "건접", "건줍", "건잡", "건젭", "건집",
        "건첩", "건젓", "건적", "건전",
        # ── 곤 (ㅡ→ㅗ) + 접 변형 ──
        "곤접", "곤줍", "곤잡", "곤젭",
        # ── 간 (ㅡ→ㅏ) + 접 변형 ──
        "간접", "간줍", "간잡",
        # ── 끈 (ㄱ→ㄲ) + 접 변형 ──
        "끈접", "끈줍", "끈잡", "끈젭", "끈집",
        "끈첩", "끈전", "끈절",
        # ── 큰 (ㄱ→ㅋ) + 접 변형 ──
        "큰접", "큰줍", "큰잡", "큰젭", "큰집",
        "큰첩", "큰전",
        # ── 른/는/든 (ㄱ→ㄹ/ㄴ/ㄷ) + 접 변형 ──
        "른접", "른줍", "른잡", "른젭",
        "는접", "는줍", "는잡",
        "든접", "든줍", "든잡",
        # ── 근 받침 변형 (ㄴ→ㄹ/ㅁ/ㅇ) ──
        "글접", "글줍", "글잡",
        "금접", "금줍",
        "긍접",
        # ── 기타 혼동 ──
        "귀접", "귄접",
        "근줘", "근쥐", "근줴",
    ]

    # ══════════════════════════════════════════════════════════════════════
    # 투사체
    # 투: ㅌ(→ㄷ/ㄸ/ㄹ/ㅊ/ㅍ/ㅎ/ㅂ/ㄱ/ㅅ) × ㅜ(→ㅗ/ㅡ/ㅣ/ㅠ)
    # 사: ㅅ(→ㅆ/ㅈ/ㅊ/ㅎ/ㄷ) × ㅏ(→ㅐ/ㅔ/ㅓ/ㅗ/ㅣ/ㅑ/ㅒ)
    # 체: ㅊ(→ㅈ/ㅉ/ㅎ/ㅋ/ㅅ/ㄷ/ㄱ) × ㅔ(→ㅐ/ㅓ/ㅕ/ㅣ/ㅡ/ㅒ)
    # ══════════════════════════════════════════════════════════════════════
    keyword_tusache = [
        # ── 투 + 사 + 체 기본 / 체 변형 ──
        "투사체", "투사채", "투사처", "투사쳐",
        "투사제", "투사케", "투사헤", "투사데", "투사게",
        "투사세", "투사치", "투사쩨", "투사쳬", "투사쫴",
        # ── 투 + 새(ㅏ→ㅐ) + 체 변형 ──
        "투새체", "투새채", "투새처", "투새쳐",
        "투새제", "투새케", "투새데", "투새세", "투새치",
        # ── 투 + 세(ㅏ→ㅔ) + 체 변형 ──
        "투세체", "투세채", "투세처", "투세쳐",
        "투세제", "투세케",
        # ── 투 + 서(ㅏ→ㅓ) + 체 변형 ──
        "투서체", "투서채", "투서처",
        "투서제", "투서케",
        # ── 투 + 소(ㅏ→ㅗ) + 체 변형 ──
        "투소체", "투소채", "투소처", "투소제",
        # ── 투 + 시(ㅏ→ㅣ) + 체 변형 ──
        "투시체", "투시채", "투시처",
        # ── 투 + 자(ㅅ→ㅈ) + 체 변형 ──
        "투자체", "투자채", "투자처", "투자제", "투자케",
        # ── 투 + 차(ㅅ→ㅊ) + 체 변형 ──
        "투차체", "투차채", "투차처",
        # ── 투 + 하(ㅅ→ㅎ) + 체 변형 ──
        "투하체", "투하채", "투하처",
        # ── 두(ㅌ→ㄷ) + 사+체 변형 ──
        "두사체", "두사채", "두사처", "두사쳐",
        "두사제", "두사케", "두사세",
        "두새체", "두새채", "두새처", "두새제", "두새케",
        "두세체", "두세채", "두세처",
        "두서체", "두서채",
        "두소체", "두소채",
        "두시체", "두시채",
        "두자체", "두자채", "두자처",
        "두차체", "두차채",
        "두하체",
        # ── 뚜(ㅌ→ㄸ) + 사+체 변형 ──
        "뚜사체", "뚜사채", "뚜사처", "뚜사제",
        "뚜새체", "뚜새채", "뚜새처",
        "뚜서체", "뚜자체",
        # ── 루(ㅌ→ㄹ) + 사+체 변형 ──
        "루사체", "루사채", "루사처", "루사제",
        "루새체", "루새채", "루새처",
        "루서체", "루세체",
        "루자체", "루차체",
        # ── 추(ㅌ→ㅊ) + 사+체 변형 ──
        "추사체", "추사채", "추사처", "추사제",
        "추새체", "추새채", "추새처",
        "추서체", "추자체",
        # ── 푸(ㅌ→ㅍ) + 사+체 변형 ──
        "푸사체", "푸사채", "푸새체", "푸새채",
        # ── 후(ㅌ→ㅎ) + 사+체 변형 ──
        "후사체", "후사채", "후새체",
        # ── 부(ㅌ→ㅂ) + 사+체 변형 ──
        "부사체", "부사채", "부새체",
        # ── 구(ㅌ→ㄱ) + 사+체 변형 ──
        "구사체", "구사채",
        # ── 수(ㅌ→ㅅ) + 사+체 변형 ──
        "수사체", "수사채",
        # ── 토(ㅜ→ㅗ) + 사+체 변형 ──
        "토사체", "토사채", "토새체", "토새채",
        # ── 트(ㅜ→ㅡ) + 사+체 변형 ──
        "트사체", "트사채", "트새체",
        # ── 기타 혼동 ──
        "투싸체", "두싸체", "투씨체", "투씨채",
        "뚜새체", "루새체",
    ]

    # ══════════════════════════════════════════════════════════════════════
    # 소환수
    # 소: ㅅ(→ㅆ/ㅈ/ㅊ/ㅎ/ㅂ/ㄷ) × ㅗ(→ㅛ/ㅓ/ㅣ/ㅜ/ㅏ/ㅡ)
    # 환: ㅎ(→ㅇ/ㄱ/ㄴ/ㄹ/ㅁ) × ㅘ(→ㅏ/ㅗ/ㅡ/ㅜ/ㅐ/ㅔ)
    #     받침ㄴ(→ㄹ/ㅇ/ㅁ/ㄷ/탈락)
    # 수: ㅅ(→ㅆ/ㅈ/ㅊ/ㅎ/ㅂ/ㅇ) × ㅜ(→ㅡ/ㅣ/ㅠ/ㅓ/ㅗ/ㅒ)
    # ══════════════════════════════════════════════════════════════════════
    keyword_sohwansu = [
        # ── 소 + 환 + 수 기본 / 수 변형 ──
        "소환수", "소환스", "소환시", "소환슈", "소환쉬",
        "소환주", "소환추", "소환쑤", "소환우", "소환유",
        "소환서", "소환소", "소환쓰",
        # ── 소 + 한(환 ㅘ→ㅏ, 가장 흔한 오인식) + 수 변형 ──
        "소한수", "소한스", "소한시", "소한슈", "소한쉬",
        "소한주", "소한추", "소한우", "소한유", "소한서", "소한쓰",
        # ── 소 + 항(환 ㄴ→ㅇ) + 수 변형 ──
        "소항수", "소항스", "소항시", "소항슈",
        "소항주", "소항우", "소항서",
        # ── 소 + 활(환 ㄴ→ㄹ) + 수 변형 ──
        "소활수", "소활스", "소활시", "소활슈",
        "소활주", "소활우",
        # ── 소 + 혼(환 ㅘ→ㅗ) + 수 변형 ──
        "소혼수", "소혼스", "소혼시", "소혼주", "소혼슈",
        # ── 소 + 흔(환 ㅘ→ㅡ) + 수 변형 ──
        "소흔수", "소흔스", "소흔시",
        # ── 소 + 훈(환 ㅘ→ㅜ) + 수 변형 ──
        "소훈수", "소훈스", "소훈시",
        # ── 소 + 핸(환 ㅘ→ㅐ) + 수 변형 ──
        "소핸수", "소핸스",
        # ── 소 + 헨(환 ㅘ→ㅔ) + 수 변형 ──
        "소헨수", "소헨스",
        # ── 소 + 완(환 ㅎ→ㅇ) + 수 변형 ──
        "소완수", "소완스", "소완시", "소완주", "소완슈",
        # ── 소 + 황(환 ㄴ→ㅇ, ㅘ유지) + 수 변형 ──
        "소황수", "소황스", "소황시",
        # ── 소 + 화(환 받침탈락) + 수 변형 ──
        "소화수", "소화스", "소화시", "소화주", "소화슈",
        # ── 소 + 관(환 ㅎ→ㄱ) + 수 변형 ──
        "소관수", "소관스",
        # ── 소 + 만(환 ㅎ→ㅁ, ㅘ→ㅏ) + 수 변형 ──
        "소만수", "소만스",
        # ── 쇼(ㅗ→ㅛ) + 환+수 변형 ──
        "쇼환수", "쇼환스", "쇼환시", "쇼환주", "쇼환슈",
        "쇼한수", "쇼한스", "쇼한시", "쇼한주",
        "쇼항수", "쇼항스", "쇼항시",
        "쇼활수", "쇼활스",
        "쇼혼수", "쇼화수", "쇼완수",
        "쇼훈수", "쇼황수",
        # ── 조(ㅅ→ㅈ) + 환+수 변형 ──
        "조환수", "조환스", "조환시",
        "조한수", "조한스", "조한시",
        "조항수", "조항스",
        "조활수", "조화수",
        # ── 초(ㅅ→ㅊ) + 환+수 변형 ──
        "초환수", "초환스", "초환시",
        "초한수", "초한스",
        "초항수", "초활수",
        # ── 호(ㅅ→ㅎ) + 환+수 변형 ──
        "호환수", "호환스",
        "호한수", "호한스",
        "호항수", "호활수",
        # ── 보(ㅅ→ㅂ) + 환+수 변형 ──
        "보환수", "보환스",
        "보한수", "보항수",
        # ── 도(ㅅ→ㄷ) + 환+수 변형 ──
        "도환수", "도한수",
        # ── 서/시/수(ㅗ→ㅓ/ㅣ/ㅜ) + 환+수 변형 ──
        "서환수", "서환스",
        "서한수", "서한스", "서항수", "서활수",
        "시환수", "시환스",
        "시한수", "시항수",
        "수환수", "수한수",
        # ── 소(ㅗ→ㅏ: 사) + 환+수 변형 ──
        "사환수", "사한수",
        # ── 쏘(ㅆ) + 환+수 변형 ──
        "쏘환수", "쏘한수", "쏘항수",
        # ── 기타 혼동 ──
        "소왼수", "소횐수", "소훤수",
    ]

    for kind, keywords in [
        ("주문",  keyword_jumun),
        ("근접",  keyword_gunjub),
        ("투사체", keyword_tusache),
        ("소환수", keyword_sohwansu),
    ]:
        if any(k in compact for k in keywords):
            print(f"[MATCH] ✓ 종류='{kind}' 감지!")
            return kind

    print("[MATCH] 종류 키워드(주문/근접/투사체/소환수) 없음")
    return ""


class SelectionOverlay(QtWidgets.QWidget):
    """전체 화면을 덮는 선택 오버레이. 드래그로 인식 영역 지정."""

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
            self.region_selected.emit(x1, y1, x2 - x1, y2 - y1)
            self.close()

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.fillRect(self.rect(), QtGui.QColor(0, 0, 0, 80))
        if self.start_pos and self.end_pos:
            x1 = min(self.start_pos.x(), self.end_pos.x())
            y1 = min(self.start_pos.y(), self.end_pos.y())
            x2 = max(self.start_pos.x(), self.end_pos.x())
            y2 = max(self.start_pos.y(), self.end_pos.y())
            painter.setPen(QtGui.QPen(QtGui.QColor(255, 0, 0), 3))
            painter.drawRect(QtCore.QRect(x1, y1, x2 - x1, y2 - y1))


class RegionBorderOverlay(QtWidgets.QWidget):
    """인식 영역에 빨간 테두리 표시. 마우스 입력은 통과."""

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
    """옵션 감지 시 뜨는 전체 화면 팝업."""

    def __init__(self, option_type: str, click_count: int, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.WindowStaysOnTopHint
            | QtCore.Qt.Tool
        )
        self.setModal(True)
        self.setWindowState(QtCore.Qt.WindowFullScreen)
        self.setWindowModality(QtCore.Qt.ApplicationModal)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        container = QtWidgets.QWidget()
        container.setStyleSheet("background-color: rgba(0, 0, 0, 230);")

        layout = QtWidgets.QVBoxLayout(container)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        layout.setContentsMargins(100, 100, 100, 100)

        label_title = QtWidgets.QLabel("🎉 축하합니다! 🎉")
        label_title.setStyleSheet(
            "font-size: 80px; font-weight: bold; color: #FFD700; padding: 40px;"
        )
        label_title.setAlignment(QtCore.Qt.AlignCenter)

        display_name = OPTION_DISPLAY.get(option_type, option_type)
        msg = f'"{display_name}"\n\n옵션이 감지되었습니다!'
        label_msg = QtWidgets.QLabel(msg)
        label_msg.setStyleSheet(
            "font-size: 40px; color: white; padding: 30px; line-height: 1.5;"
        )
        label_msg.setAlignment(QtCore.Qt.AlignCenter)

        label_count = QtWidgets.QLabel(f"총 {click_count}회 클릭")
        label_count.setStyleSheet(
            "font-size: 50px; color: #00FF00; font-weight: bold; padding: 20px;"
        )
        label_count.setAlignment(QtCore.Qt.AlignCenter)

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
        self.raise_()
        self.activateWindow()

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() in (QtCore.Qt.Key_Escape, QtCore.Qt.Key_F9, QtCore.Qt.Key_F10):
            self.accept()
        else:
            super().keyPressEvent(event)


class MacroThread(QtCore.QThread):
    """OCR 체크 후 클릭을 수행하는 통합 매크로 쓰레드."""

    detected = QtCore.pyqtSignal(str)
    text_updated = QtCore.pyqtSignal(str)
    click_count_changed = QtCore.pyqtSignal(int)

    def __init__(self, region, reader, interval_ms: int = 100, parent=None):
        super().__init__(parent)
        self.region = region
        self.reader = reader
        self.interval_ms = interval_ms
        self._running = True
        self.click_count = 0

    def stop(self) -> None:
        self._running = False

    def run(self) -> None:
        print("[MACRO] 매크로 스레드 시작")
        sct = mss.mss()
        x, y, w, h = self.region
        monitor = {"top": y, "left": x, "width": w, "height": h}

        pyautogui.keyDown("shift")
        try:
            while self._running:
                img = np.array(sct.grab(monitor))
                img = img[:, :, :3]

                try:
                    results = self.reader.readtext(img, detail=0)
                except Exception:
                    results = []

                joined = " ".join(results)
                self.text_updated.emit(joined)
                print("[OCR]", joined)

                option_type = detect_option_type(joined)
                if option_type:
                    print(f"[DETECT] ✓✓✓ 종류={option_type} — 클릭하지 않고 중단")
                    self.detected.emit(option_type)
                    break

                pyautogui.click()
                self.click_count += 1
                self.click_count_changed.emit(self.click_count)
                print(f"[CLICK] 클릭 실행 (총 {self.click_count}회)")

                time.sleep(self.interval_ms / 1000.0)
        finally:
            pyautogui.keyUp("shift")
            print("[MACRO] 매크로 스레드 종료, Shift 해제")


class MainWindow(QtWidgets.QMainWindow):
    """메인 윈도우."""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("옵션 감지 매크로")
        self.setFixedSize(420, 290)

        central = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central)

        self.label_status = QtWidgets.QLabel("상태: 대기 중")
        self.label_status.setStyleSheet("font-size: 14px;")

        self.label_region = QtWidgets.QLabel("인식 영역: 미설정")
        self.label_region.setStyleSheet("font-size: 12px;")

        btn_set_region = QtWidgets.QPushButton("인식 영역 설정")
        btn_set_region.clicked.connect(self.on_set_region)

        btn_emergency_stop = QtWidgets.QPushButton("긴급 정지 (F9/F10)")
        btn_emergency_stop.setStyleSheet(
            "background-color: #ff4444; color: white; font-weight: bold;"
        )
        btn_emergency_stop.clicked.connect(self.stop_macro)

        self.label_clicks = QtWidgets.QLabel("현재 클릭 수: 0")
        self.label_clicks.setStyleSheet("font-size: 12px;")

        self.label_ocr = QtWidgets.QLabel("현재 인식 텍스트: (대기 중)")
        self.label_ocr.setStyleSheet("font-size: 11px; color: gray;")

        self.label_hotkeys = QtWidgets.QLabel(
            "핫키:\nF7 - 인식 영역 설정\nF8 - 매크로 시작/정지\nF9 / F10 - 긴급 정지\n"
            "감지 대상: 주문 / 근접 / 투사체 / 소환수 스킬레벨 +3"
        )
        self.label_hotkeys.setStyleSheet("font-size: 11px;")

        layout.addWidget(self.label_status)
        layout.addWidget(self.label_region)
        layout.addWidget(btn_set_region)
        layout.addWidget(btn_emergency_stop)
        layout.addSpacing(10)
        layout.addWidget(self.label_clicks)
        layout.addSpacing(5)
        layout.addWidget(self.label_ocr)
        layout.addSpacing(5)
        layout.addWidget(self.label_hotkeys)

        self.setCentralWidget(central)

        self.region = None
        self.region_overlay = RegionBorderOverlay()
        self.macro_thread = None
        self.macro_running = False
        self.click_count = 0
        self.last_f7_state = False
        self.last_f8_state = False
        self.last_f9_state = False
        self.last_f10_state = False

        self.reader = easyocr.Reader(["ko", "en"], gpu=False)

        self.shortcut_f7 = QtWidgets.QShortcut(QtGui.QKeySequence("F7"), self)
        self.shortcut_f7.activated.connect(self.on_set_region)
        self.shortcut_f8 = QtWidgets.QShortcut(QtGui.QKeySequence("F8"), self)
        self.shortcut_f8.activated.connect(self.toggle_macro)
        self.shortcut_f9 = QtWidgets.QShortcut(QtGui.QKeySequence("F9"), self)
        self.shortcut_f9.activated.connect(self.stop_macro)
        self.shortcut_f10 = QtWidgets.QShortcut(QtGui.QKeySequence("F10"), self)
        self.shortcut_f10.activated.connect(self.stop_macro)
        self.shortcut_shift_f9 = QtWidgets.QShortcut(QtGui.QKeySequence("Shift+F9"), self)
        self.shortcut_shift_f9.activated.connect(self.stop_macro)
        self.shortcut_shift_f10 = QtWidgets.QShortcut(QtGui.QKeySequence("Shift+F10"), self)
        self.shortcut_shift_f10.activated.connect(self.stop_macro)

        self.hotkey_timer = QtCore.QTimer(self)
        self.hotkey_timer.timeout.connect(self._check_hotkeys)
        self.hotkey_timer.start(50)

    def _check_hotkeys(self) -> None:
        try:
            f7 = keyboard.is_pressed('f7')
            if f7 and not self.last_f7_state:
                self.on_set_region()
            self.last_f7_state = f7

            f8 = keyboard.is_pressed('f8')
            if f8 and not self.last_f8_state:
                self.toggle_macro()
            self.last_f8_state = f8

            f9 = keyboard.is_pressed('f9')
            if f9 and not self.last_f9_state:
                self.emergency_stop()
            self.last_f9_state = f9

            f10 = keyboard.is_pressed('f10')
            if f10 and not self.last_f10_state:
                self.emergency_stop()
            self.last_f10_state = f10
        except Exception:
            pass

    def on_set_region(self) -> None:
        self.selection_overlay = SelectionOverlay()
        self.selection_overlay.region_selected.connect(self.set_region)
        self.selection_overlay.show()
        self.selection_overlay.raise_()
        self.selection_overlay.activateWindow()

    @QtCore.pyqtSlot(int, int, int, int)
    def set_region(self, x: int, y: int, w: int, h: int) -> None:
        self.region = (x, y, w, h)
        self.label_region.setText(f"인식 영역: x={x}, y={y}, w={w}, h={h}")
        self.region_overlay.set_region(x, y, w, h)

    def toggle_macro(self) -> None:
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
        self.click_count = 0
        self.label_clicks.setText("현재 클릭 수: 0")
        self.label_status.setText("상태: 매크로 동작 중")

        self.macro_thread = MacroThread(self.region, self.reader, interval_ms=100)
        self.macro_thread.detected.connect(self.on_detected)
        self.macro_thread.text_updated.connect(self.on_ocr_text_updated)
        self.macro_thread.click_count_changed.connect(self.on_click_count_changed)
        self.macro_thread.start()

    @QtCore.pyqtSlot()
    def stop_macro(self) -> None:
        print("[MACRO] stop_macro 호출")
        self.macro_running = False
        self.label_status.setText("상태: 대기 중")

        if self.macro_thread:
            self.macro_thread.stop()
            self.macro_thread.wait(2000)
            self.macro_thread = None

    @QtCore.pyqtSlot(int)
    def on_click_count_changed(self, count: int) -> None:
        self.click_count = count
        self.label_clicks.setText(f"현재 클릭 수: {count}")

    @QtCore.pyqtSlot(str)
    def on_detected(self, option_type: str) -> None:
        self.stop_macro()
        popup = BlockPopup(option_type, self.click_count, self)
        popup.exec_()

    @QtCore.pyqtSlot(str)
    def on_ocr_text_updated(self, text: str) -> None:
        self.label_ocr.setText(f"현재 인식 텍스트: {text if text else '(없음)'}")

    def emergency_stop(self) -> None:
        print("[HOTKEY] emergency_stop 호출됨")
        if self.macro_thread and self.macro_thread.isRunning():
            self.macro_thread.stop()
        QtCore.QMetaObject.invokeMethod(
            self, "stop_macro", QtCore.Qt.QueuedConnection
        )

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.stop_macro()
        self.region_overlay.close()
        if hasattr(self, 'hotkey_timer'):
            self.hotkey_timer.stop()
        event.accept()


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
