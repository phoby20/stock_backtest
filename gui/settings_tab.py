"""설정 탭 — 브로커 인증 정보 관리"""
import sys
from pathlib import Path

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QScrollArea,
    QSizePolicy,
)

from gui.widgets import form_row, hline
from src.utils.config_store import save_secret, load_secret, _DIR


# ── 비밀번호 입력창 + 표시/숨김 버튼 ──────────────────────────────

class _PasswordRow(QWidget):
    def __init__(self, placeholder=""):
        super().__init__()
        self.setStyleSheet("background:transparent;")
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)

        self.edit = QLineEdit()
        self.edit.setPlaceholderText(placeholder)
        self.edit.setEchoMode(QLineEdit.Password)
        row.addWidget(self.edit)

        self._toggle = QPushButton("표시")
        self._toggle.setFixedWidth(72)
        self._toggle.setFixedHeight(32)
        self._toggle.setCheckable(True)
        self._toggle.setToolTip("비밀번호 표시 / 숨기기")
        self._toggle.setStyleSheet(
            "QPushButton {"
            "  background:#21262d; color:#8b949e;"
            "  border:1px solid #30363d; border-radius:6px;"
            "  font-size:12px; font-weight:600; padding:0 10px;"
            "}"
            "QPushButton:hover { background:#30363d; color:#c9d1d9; border-color:#484f58; }"
            "QPushButton:checked { background:#0d2147; color:#58a6ff; border-color:#388bfd; }"
            "QPushButton:checked:hover { background:#102050; border-color:#58a6ff; }"
        )
        self._toggle.toggled.connect(self._on_toggle)
        row.addWidget(self._toggle)

    def _on_toggle(self, checked: bool):
        self.edit.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)
        self._toggle.setText("숨기기" if checked else "표시")

    def text(self) -> str:
        return self.edit.text()

    def setText(self, val: str):
        self.edit.setText(val)


# ── 섹션 카드 ──────────────────────────────────────────────────────

class _Card(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(
            "QFrame { background:#161b22; border:1px solid #30363d;"
            "  border-radius:8px; }"
        )
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20, 16, 20, 20)
        self._layout.setSpacing(12)

    def add(self, widget):
        self._layout.addWidget(widget)


# ── 설정 탭 ────────────────────────────────────────────────────────

class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._load()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border:none; background:#0d1117; }")

        content = QWidget()
        content.setStyleSheet("background:#0d1117;")
        vl = QVBoxLayout(content)
        vl.setContentsMargins(48, 36, 48, 36)
        vl.setSpacing(20)
        vl.setAlignment(Qt.AlignTop)

        # ── 페이지 제목 ───────────────────────────────────────
        title = QLabel("설정")
        title.setStyleSheet(
            "color:#e6edf3; font-size:22px; font-weight:bold;"
            "background:transparent;"
        )
        vl.addWidget(title)

        desc = QLabel(
            "인증 정보는 AES-128 암호화되어 로컬 파일에 저장됩니다.\n"
            f"저장 위치: {_DIR}"
        )
        desc.setStyleSheet("color:#8b949e; font-size:12px; background:transparent;")
        vl.addWidget(desc)

        vl.addWidget(hline())

        # ── KIS 카드 ──────────────────────────────────────────
        kis_card = _Card()

        kis_title = QLabel("한국투자증권 (KIS)")
        kis_title.setStyleSheet(
            "color:#e6edf3; font-size:14px; font-weight:bold; background:transparent;"
        )
        kis_card.add(kis_title)

        self.kisAppKeyEdit = QLineEdit()
        self.kisAppKeyEdit.setPlaceholderText("App Key")
        kis_card.add(form_row("App Key", self.kisAppKeyEdit))

        self.kisAppSecretRow = _PasswordRow("App Secret")
        kis_card.add(form_row("App Secret", self.kisAppSecretRow))

        self.kisAccountEdit = QLineEdit()
        self.kisAccountEdit.setPlaceholderText("예: 12345678-01")
        kis_card.add(form_row("계좌번호", self.kisAccountEdit))

        vl.addWidget(kis_card)

        # ── 키움 카드 ─────────────────────────────────────────
        kiwoom_card = _Card()

        kiwoom_title = QLabel("키움증권 (Kiwoom)")
        kiwoom_title.setStyleSheet(
            "color:#e6edf3; font-size:14px; font-weight:bold; background:transparent;"
        )
        kiwoom_card.add(kiwoom_title)

        if sys.platform != "win32":
            warn = QLabel("⚠️  키움 OpenAPI+는 Windows 전용입니다. macOS에서는 KIS를 사용하세요.")
            warn.setObjectName("warningLabel")
            warn.setWordWrap(True)
            kiwoom_card.add(warn)

        self.kiwoomAccountEdit = QLineEdit()
        self.kiwoomAccountEdit.setPlaceholderText("예: 1234567890  (10자리)")
        kiwoom_card.add(form_row("계좌번호", self.kiwoomAccountEdit))

        vl.addWidget(kiwoom_card)

        # ── 저장 버튼 ─────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignLeft)

        self.saveBtn = QPushButton("저장")
        self.saveBtn.setObjectName("primaryBtn")
        self.saveBtn.setFixedWidth(110)
        self.saveBtn.setMinimumHeight(36)
        self.saveBtn.clicked.connect(self._save)
        btn_row.addWidget(self.saveBtn)

        self.statusLabel = QLabel("")
        self.statusLabel.setStyleSheet("font-size:12px; background:transparent;")
        btn_row.addWidget(self.statusLabel)

        vl.addLayout(btn_row)
        vl.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)

    # ── 불러오기 / 저장 ───────────────────────────────────────────

    def _load(self):
        self.kisAppKeyEdit.setText(load_secret("kis_app_key"))
        self.kisAppSecretRow.setText(load_secret("kis_app_secret"))
        self.kisAccountEdit.setText(load_secret("kis_account"))
        self.kiwoomAccountEdit.setText(load_secret("kiwoom_account"))

    def _save(self):
        save_secret("kis_app_key",    self.kisAppKeyEdit.text().strip())
        save_secret("kis_app_secret", self.kisAppSecretRow.text().strip())
        save_secret("kis_account",    self.kisAccountEdit.text().strip())
        save_secret("kiwoom_account", self.kiwoomAccountEdit.text().strip())

        self.statusLabel.setStyleSheet("color:#00C853; font-size:12px; background:transparent;")
        self.statusLabel.setText("  저장되었습니다.")
        QTimer.singleShot(3000, lambda: self.statusLabel.setText(""))
