# -*- mode: python ; coding: utf-8 -*-
import sys
block_cipher = None

_hidden = [
    "yfinance", "pandas", "numpy", "matplotlib",
    "matplotlib.backends.backend_qt5agg",
    "matplotlib.figure",
    "PyQt5", "PyQt5.QtWidgets", "PyQt5.QtCore", "PyQt5.QtGui",
    "tabulate", "colorama", "schedule", "requests",
    "src.data.fetcher",
    "src.indicators.rsi",
    "src.indicators.macd",
    "src.strategy.rsi_strategy",
    "src.strategy.rsi_macd_strategy",
    "src.backtest.engine",
    "src.trading.monitor",
    "src.trading.live_trader",
    "src.broker.base",
    "src.broker.kis",
    "src.broker.kiwoom",
    "src.utils.display",
    "src.utils.chart",
    "gui.main_window",
    "gui.backtest_tab",
    "gui.monitor_tab",
    "gui.trade_tab",
    "gui.chart_window",
    "gui.styles",
    "gui.widgets",
]

# QAxContainer 은 Windows 전용 (키움 OpenAPI+)
if sys.platform == "win32":
    _hidden.append("PyQt5.QAxContainer")

a = Analysis(
    ["app.py"],
    pathex=["."],
    binaries=[],
    datas=[
        ("config.py",            "."),
        ("src",                  "src"),
        ("gui",                  "gui"),
        ("src/fonts",            "src/fonts"),   # NanumGothic.ttf 포함
    ],
    hiddenimports=_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "fastapi", "uvicorn", "mangum",          # 웹 전용
        "PyQt5.QtWebEngineWidgets",              # Qt WebEngine (97MB)
        "PyQt5.QtWebEngineCore",
        "PyQt5.QtWebEngine",
        "PyQt5.QtBluetooth",
        "PyQt5.QtNfc",
        "PyQt5.QtLocation",
        "PyQt5.QtMultimedia",
        "PyQt5.QtMultimediaWidgets",
        "PyQt5.QtSql",
        "PyQt5.QtTest",
        "PyQt5.QtXml",
        "tkinter", "_tkinter",                   # Tkinter 불필요
        "IPython", "jupyter", "notebook",
        "scipy", "sklearn", "sklearn",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="RSI_MACD_Trader",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="RSI_MACD_Trader",
)

# macOS: .app 번들 생성
if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="RSI_MACD_Trader.app",
        icon=None,
        bundle_identifier="com.rsimacd.trader",
        info_plist={
            "NSHighResolutionCapable": True,
            "CFBundleShortVersionString": "1.0.0",
            "CFBundleName": "RSI MACD Trader",
        },
    )
