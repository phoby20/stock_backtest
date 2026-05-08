DARK_STYLE = """
/* ── Base ───────────────────────────────────────────────────── */
QMainWindow, QDialog {
    background-color: #0d1117;
    color: #e6edf3;
}
QWidget {
    background-color: #0d1117;
    color: #e6edf3;
    font-family: 'Segoe UI', 'SF Pro Text', 'Apple SD Gothic Neo', sans-serif;
    font-size: 13px;
}

/* ── Tab ─────────────────────────────────────────────────────── */
QTabWidget::pane {
    border: none;
    background-color: #0d1117;
}
QTabWidget::tab-bar { alignment: left; }
QTabBar {
    background: #161b22;
    border-bottom: 1px solid #21262d;
}
QTabBar::tab {
    background: transparent;
    color: #8b949e;
    padding: 10px 22px;
    border: none;
    border-bottom: 2px solid transparent;
    font-size: 13px;
    font-weight: 500;
    min-width: 100px;
}
QTabBar::tab:selected {
    color: #e6edf3;
    border-bottom: 2px solid #58a6ff;
}
QTabBar::tab:hover:!selected { color: #c9d1d9; }

/* ── Card (GroupBox) ─────────────────────────────────────────── */
QGroupBox {
    background-color: #161b22;
    border: 1px solid #21262d;
    border-radius: 8px;
    margin-top: 18px;
    padding: 14px 12px 12px 12px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: #6e7681;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    top: -1px;
    padding: 0 6px;
    background-color: #161b22;
    color: #6e7681;
}

/* ── Input Fields ────────────────────────────────────────────── */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #21262d;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 0px 10px;
    color: #e6edf3;
    min-height: 32px;
    font-size: 13px;
    selection-background-color: #1f4e8c;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border-color: #388bfd;
    background-color: #1c2128;
}
QLineEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover {
    border-color: #484f58;
    background-color: #1c2128;
}
QLineEdit::placeholder { color: #484f58; }
QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled, QComboBox:disabled {
    color: #484f58;
    background-color: #161b22;
    border-color: #21262d;
}

/* ── SpinBox Buttons ─────────────────────────────────────────── */
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    background-color: #2d333b;
    border: none;
    border-left: 1px solid #30363d;
    width: 26px;
}
QSpinBox::up-button, QDoubleSpinBox::up-button {
    border-top-right-radius: 5px;
    border-bottom: 1px solid #21262d;
    margin: 2px 2px 1px 0;
}
QSpinBox::down-button, QDoubleSpinBox::down-button {
    border-bottom-right-radius: 5px;
    margin: 1px 2px 2px 0;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover,
QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #484f58;
}
QSpinBox::up-button:pressed, QSpinBox::down-button:pressed,
QDoubleSpinBox::up-button:pressed, QDoubleSpinBox::down-button:pressed {
    background-color: #1f6feb;
}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 5px solid #c9d1d9;
    width: 0; height: 0;
}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #c9d1d9;
    width: 0; height: 0;
}

/* ── ComboBox ────────────────────────────────────────────────── */
QComboBox {
    padding-right: 32px;
}
QComboBox::drop-down {
    border: none;
    width: 30px;
    background: transparent;
}
QComboBox::down-arrow {
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #8b949e;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #1c2128;
    border: 1px solid #30363d;
    border-radius: 6px;
    color: #e6edf3;
    selection-background-color: #1f4e8c;
    padding: 4px;
    outline: none;
    font-size: 13px;
}
QComboBox QAbstractItemView::item {
    padding: 7px 12px;
    min-height: 30px;
    border-radius: 4px;
}
QComboBox QAbstractItemView::item:hover { background-color: #30363d; }
QComboBox QAbstractItemView::item:selected { background-color: #1f4e8c; }

/* ── Button (secondary default) ──────────────────────────────── */
QPushButton {
    background-color: #21262d;
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 7px 18px;
    font-weight: 600;
    font-size: 13px;
    min-height: 36px;
    letter-spacing: 0.1px;
}
QPushButton:hover {
    background-color: #30363d;
    border-color: #484f58;
    color: #e6edf3;
}
QPushButton:pressed { background-color: #161b22; }
QPushButton:disabled {
    background-color: #161b22;
    color: #484f58;
    border-color: #21262d;
}

QPushButton#primaryBtn {
    background-color: #1f6feb;
    color: #ffffff;
    border: none;
}
QPushButton#primaryBtn:hover   { background-color: #388bfd; }
QPushButton#primaryBtn:pressed { background-color: #1158c7; }
QPushButton#primaryBtn:disabled { background-color: #21262d; color: #484f58; border: none; }

QPushButton#stopBtn {
    background-color: #b62324;
    color: #ffffff;
    border: none;
}
QPushButton#stopBtn:hover   { background-color: #d1242f; }
QPushButton#stopBtn:pressed { background-color: #8e1519; }
QPushButton#stopBtn:disabled { background-color: #21262d; color: #484f58; border: none; }

QPushButton#chartBtn {
    background-color: #6e40c9;
    color: #ffffff;
    border: none;
}
QPushButton#chartBtn:hover   { background-color: #8957e5; }
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

/* ── Text Editor (log) ──────────────────────────────────────── */
QTextEdit, QPlainTextEdit {
    background-color: #010409;
    border: 1px solid #21262d;
    border-radius: 6px;
    color: #8b949e;
    font-family: 'Cascadia Code', 'JetBrains Mono', 'Consolas', 'Courier New', monospace;
    font-size: 12px;
    padding: 8px;
    line-height: 1.6;
}

/* ── Table ───────────────────────────────────────────────────── */
QTableWidget {
    background-color: #0d1117;
    border: 1px solid #21262d;
    border-radius: 6px;
    gridline-color: #21262d;
    color: #e6edf3;
    alternate-background-color: #161b22;
    font-size: 13px;
}
QTableWidget::item { padding: 7px 12px; }
QTableWidget::item:selected {
    background-color: #1f4e8c;
    color: #e6edf3;
}
QHeaderView::section {
    background-color: #161b22;
    color: #6e7681;
    padding: 8px 12px;
    border: none;
    border-bottom: 1px solid #21262d;
    border-right: 1px solid #21262d;
    font-weight: 700;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}
QHeaderView::section:last { border-right: none; }

/* ── Label ───────────────────────────────────────────────────── */
QLabel { color: #e6edf3; background: transparent; border: none; }
QLabel#headerTitle {
    font-size: 16px;
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
    font-weight: 700;
    color: #6e7681;
    letter-spacing: 1px;
    text-transform: uppercase;
    border: none;
}
QLabel#resultSummary {
    background-color: #161b22;
    border: 1px solid #21262d;
    border-radius: 6px;
    padding: 12px 16px;
    color: #c9d1d9;
    font-size: 13px;
}
QLabel#warningLabel {
    background-color: #2d1a00;
    border: 1px solid #4d2d00;
    border-radius: 6px;
    color: #e3b341;
    padding: 10px 14px;
    font-size: 12px;
    line-height: 1.5;
}
QLabel#infoLabel {
    background-color: #0c2d6b;
    border: 1px solid #1158c7;
    border-radius: 6px;
    color: #58a6ff;
    padding: 10px 14px;
    font-size: 12px;
}

/* ── Checkbox ────────────────────────────────────────────────── */
QCheckBox {
    color: #e6edf3;
    spacing: 8px;
    font-size: 13px;
    min-height: 24px;
}
QCheckBox::indicator {
    width: 16px; height: 16px;
    border: 1.5px solid #484f58;
    border-radius: 4px;
    background-color: #21262d;
}
QCheckBox::indicator:checked {
    background-color: #1f6feb;
    border-color: #1f6feb;
}
QCheckBox::indicator:hover { border-color: #58a6ff; }
QCheckBox::indicator:checked:hover { background-color: #388bfd; border-color: #388bfd; }

/* ── Scrollbar ───────────────────────────────────────────────── */
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #2d333b;
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
    background: #2d333b;
    border-radius: 3px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover { background: #484f58; }

/* ── Splitter ────────────────────────────────────────────────── */
QSplitter::handle { background-color: #21262d; }
QSplitter::handle:horizontal { width: 1px; }
QSplitter::handle:vertical   { height: 1px; }

/* ── Tooltip ─────────────────────────────────────────────────── */
QToolTip {
    background-color: #1c2128;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
    opacity: 245;
}
"""
