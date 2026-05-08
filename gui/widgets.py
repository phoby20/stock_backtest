"""공통 위젯 헬퍼"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea, QSizePolicy
from PyQt5.QtCore import Qt


def form_row(label_text: str, widget, hint: str = "") -> QWidget:
    """레이블을 위, 입력창을 아래에 배치 → 창 크기와 무관하게 겹침 없음"""
    container = QWidget()
    container.setStyleSheet("background: transparent;")
    vl = QVBoxLayout(container)
    vl.setContentsMargins(0, 0, 0, 0)
    vl.setSpacing(6)

    lbl = QLabel(label_text)
    lbl.setStyleSheet(
        "color:#8b949e; font-size:12px; font-weight:600;"
        "letter-spacing:0.5px; background:transparent;"
    )
    vl.addWidget(lbl)
    vl.addWidget(widget)

    if hint:
        hint_lbl = QLabel(hint)
        hint_lbl.setStyleSheet("color:#484f58; font-size:10px; background:transparent;")
        hint_lbl.setWordWrap(True)
        vl.addWidget(hint_lbl)

    return container


def hline() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setStyleSheet("border:none; border-top:1px solid #21262d; margin:6px 0;")
    return line


def make_scroll_sidebar(inner: QWidget, min_width=260, max_width=400) -> QScrollArea:
    """사이드바를 스크롤 가능한 영역으로 감쌈"""
    scroll = QScrollArea()
    scroll.setWidget(inner)
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    scroll.setMinimumWidth(min_width)
    scroll.setMaximumWidth(max_width)
    scroll.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
    scroll.setStyleSheet(
        "QScrollArea { border:none; background:#161b22; }"
        "QScrollArea > QWidget > QWidget { background:#161b22; }"
    )
    return scroll
