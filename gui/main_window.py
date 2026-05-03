from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QLabel, QVBoxLayout,
    QHBoxLayout, QWidget, QFrame,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

from gui.backtest_tab import BacktestTab
from gui.monitor_tab  import MonitorTab
from gui.trade_tab    import TradeTab
from gui.styles       import DARK_STYLE


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RSI + MACD  자동매매")
        self.setMinimumSize(1180, 740)
        self.setStyleSheet(DARK_STYLE)
        self._setup_ui()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # ── 헤더 ─────────────────────────────────────────────
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet(
            "background-color:#161b22;"
            "border-bottom:1px solid #21262d;"
        )
        hl = QHBoxLayout(header)
        hl.setContentsMargins(24, 0, 24, 0)

        # 좌측: 로고 + 타이틀
        logo_row = QHBoxLayout()
        logo_row.setSpacing(10)

        dot = QLabel("●")
        dot.setStyleSheet("color:#58a6ff; font-size:18px; background:transparent;")
        logo_row.addWidget(dot)

        title = QLabel("RSI + MACD  자동매매")
        title.setObjectName("headerTitle")
        logo_row.addWidget(title)

        divider = QLabel("|")
        divider.setStyleSheet("color:#30363d; font-size:18px; background:transparent;")
        logo_row.addWidget(divider)

        sub = QLabel("Backtesting · Real-time Monitor · Auto Trading")
        sub.setObjectName("headerSub")
        logo_row.addWidget(sub)

        hl.addLayout(logo_row)
        hl.addStretch()

        # 우측: 상태 뱃지
        badge = QLabel("  Yahoo Finance  ")
        badge.setStyleSheet(
            "background:#0c2d6b; color:#58a6ff;"
            "border:1px solid #1f4e8c; border-radius:12px;"
            "padding:3px 10px; font-size:11px; font-weight:600;"
            "background:transparent;"
            "background-color:#0c2d6b;"
        )
        hl.addWidget(badge)

        root.addWidget(header)

        # ── 탭 ───────────────────────────────────────────────
        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.setContentsMargins(0, 0, 0, 0)

        bt = BacktestTab()
        mo = MonitorTab()
        tr = TradeTab()

        tabs.addTab(bt, "  📊  백테스트  ")
        tabs.addTab(mo, "  👁  실시간 감시  ")
        tabs.addTab(tr, "  🤖  자동매매  ")

        root.addWidget(tabs)
