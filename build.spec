# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    ["app.py"],
    pathex=["."],
    binaries=[],
    datas=[
        ("config.py", "."),
        ("src", "src"),
        ("gui", "gui"),
    ],
    hiddenimports=[
        "yfinance", "pandas", "numpy", "matplotlib",
        "matplotlib.backends.backend_qt5agg",
        "matplotlib.figure",
        "PyQt5", "PyQt5.QtWidgets", "PyQt5.QtCore",
        "PyQt5.QtGui", "PyQt5.QAxContainer",
        "tabulate", "colorama", "schedule", "requests",
        "src.data.fetcher",
        "src.indicators.rsi",
        "src.indicators.macd",
        "src.strategy.rsi_strategy",
        "src.strategy.rsi_macd_strategy",
        "src.backtest.engine",
        "src.trading.monitor",
        "src.trading.live_trader",
        "src.broker.kiwoom",
        "src.utils.display",
        "src.utils.chart",
        "gui.main_window",
        "gui.backtest_tab",
        "gui.monitor_tab",
        "gui.trade_tab",
        "gui.chart_window",
        "gui.styles",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    console=False,       # GUI 앱 → 콘솔 창 숨김
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
