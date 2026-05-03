DARK_STYLE = """
/* ── 기본 배경 ─────────────────────────────────────────── */
QMainWindow, QDialog {
    background-color: #0d1117;
    color: #e6edf3;
}
QWidget {
    background-color: #0d1117;
    color: #e6edf3;
    font-family: 'Segoe UI', 'Apple SD Gothic Neo', sans-serif;
    font-size: 13px;
}

/* ── 탭 ────────────────────────────────────────────────── */
QTabWidget::pane {
    border: none;
    background-color: #0d1117;
    padding-top: 2px;
}
QTabWidget::tab-bar { alignment: left; }
QTabBar {
    background: #161b22;
    border-bottom: 1px solid #21262d;
}
QTabBar::tab {
    background: transparent;
    color: #8b949e;
    padding: 11px 22px;
    border: none;
    border-bottom: 2px solid transparent;
    font-size: 13px;
    font-weight: 500;
    min-width: 120px;
}
QTabBar::tab:selected {
    color: #e6edf3;
    border-bottom: 2px solid #58a6ff;
    background: transparent;
}
QTabBar::tab:hover:!selected { color: #c9d1d9; }

/* ── 카드(GroupBox) ────────────────────────────────────── */
QGroupBox {
    background-color: #161b22;
    border: 1px solid #21262d;
    border-radius: 10px;
    margin-top: 14px;
    padding: 14px 12px 10px 12px;
    color: #8b949e;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    top: -1px;
    padding: 0 6px;
    background-color: #161b22;
    color: #8b949e;
}

/* ── 입력 필드 ─────────────────────────────────────────── */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #21262d;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px 10px;
    color: #e6edf3;
    min-height: 24px;
    selection-background-color: #1f4e8c;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 1px solid #58a6ff;
    outline: none;
}
QLineEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover {
    border: 1px solid #484f58;
}
QLineEdit::placeholder { color: #484f58; }

QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    background: #30363d;
    border: none;
    border-radius: 3px;
    width: 16px;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover,
QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
    background: #484f58;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #8b949e;
    margin-right: 6px;
}
QComboBox QAbstractItemView {
    background-color: #21262d;
    border: 1px solid #30363d;
    border-radius: 6px;
    color: #e6edf3;
    selection-background-color: #1f4e8c;
    padding: 4px;
    outline: none;
}
QComboBox QAbstractItemView::item { padding: 6px 10px; border-radius: 4px; }
QComboBox QAbstractItemView::item:hover { background-color: #30363d; }

/* ── 버튼 ──────────────────────────────────────────────── */
QPushButton {
    background-color: #238636;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: 600;
    font-size: 13px;
    min-height: 32px;
    letter-spacing: 0.3px;
}
QPushButton:hover  { background-color: #2ea043; }
QPushButton:pressed { background-color: #1a7f37; }
QPushButton:disabled { background-color: #21262d; color: #484f58; }

QPushButton#primaryBtn {
    background-color: #1f6feb;
}
QPushButton#primaryBtn:hover  { background-color: #388bfd; }
QPushButton#primaryBtn:pressed { background-color: #1158c7; }

QPushButton#stopBtn {
    background-color: #b62324;
}
QPushButton#stopBtn:hover  { background-color: #d1242f; }
QPushButton#stopBtn:pressed { background-color: #8e1519; }

QPushButton#chartBtn {
    background-color: #6e40c9;
}
QPushButton#chartBtn:hover  { background-color: #8957e5; }
QPushButton#chartBtn:pressed { background-color: #553098; }

QPushButton#ghostBtn {
    background-color: transparent;
    color: #58a6ff;
    border: 1px solid #30363d;
}
QPushButton#ghostBtn:hover {
    background-color: #161b22;
    border-color: #58a6ff;
}

/* ── 텍스트 에디터(로그) ───────────────────────────────── */
QTextEdit, QPlainTextEdit {
    background-color: #010409;
    border: 1px solid #21262d;
    border-radius: 8px;
    color: #8b949e;
    font-family: 'Cascadia Code', 'Consolas', 'Courier New', monospace;
    font-size: 12px;
    padding: 8px;
    line-height: 1.6;
}

/* ── 테이블 ────────────────────────────────────────────── */
QTableWidget {
    background-color: #161b22;
    border: 1px solid #21262d;
    border-radius: 8px;
    gridline-color: #21262d;
    color: #e6edf3;
    alternate-background-color: #0d1117;
}
QTableWidget::item { padding: 6px 10px; }
QTableWidget::item:selected {
    background-color: #1f4e8c;
    color: #e6edf3;
}
QHeaderView::section {
    background-color: #161b22;
    color: #8b949e;
    padding: 8px 10px;
    border: none;
    border-bottom: 1px solid #21262d;
    border-right: 1px solid #21262d;
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
QHeaderView::section:last { border-right: none; }

/* ── 라벨 ──────────────────────────────────────────────── */
QLabel { color: #e6edf3; background: transparent; }
QLabel#headerTitle {
    font-size: 17px;
    font-weight: 700;
    color: #e6edf3;
    letter-spacing: -0.3px;
}
QLabel#headerSub {
    font-size: 12px;
    color: #6e7681;
}
QLabel#sectionLabel {
    font-size: 11px;
    font-weight: 600;
    color: #8b949e;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}
QLabel#resultSummary {
    background-color: #161b22;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 10px 14px;
    color: #c9d1d9;
    font-size: 13px;
    line-height: 1.5;
}
QLabel#warningLabel {
    background-color: #2d1a00;
    border: 1px solid #4d2d00;
    border-radius: 8px;
    color: #e3b341;
    padding: 10px 14px;
    font-size: 12px;
}
QLabel#infoLabel {
    background-color: #0c2d6b;
    border: 1px solid #1158c7;
    border-radius: 8px;
    color: #58a6ff;
    padding: 10px 14px;
    font-size: 12px;
}

/* ── 체크박스 ──────────────────────────────────────────── */
QCheckBox {
    color: #e6edf3;
    spacing: 8px;
    font-size: 13px;
}
QCheckBox::indicator {
    width: 16px; height: 16px;
    border: 1px solid #30363d;
    border-radius: 4px;
    background-color: #21262d;
}
QCheckBox::indicator:checked {
    background-color: #1f6feb;
    border-color: #1f6feb;
}
QCheckBox::indicator:hover { border-color: #58a6ff; }

/* ── 스크롤바 ──────────────────────────────────────────── */
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #30363d;
    border-radius: 3px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #484f58; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QScrollBar:horizontal {
    background: transparent;
    height: 6px;
}
QScrollBar::handle:horizontal {
    background: #30363d;
    border-radius: 3px;
}

/* ── 스플리터 ──────────────────────────────────────────── */
QSplitter::handle { background-color: #21262d; }
QSplitter::handle:horizontal { width: 1px; }
QSplitter::handle:vertical   { height: 1px; }
"""
