@echo off
chcp 65001 > nul
echo ================================================
echo   RSI+MACD 자동매매 프로그램 빌드 시작
echo ================================================

echo [1/3] 의존성 설치 중...
pip install -r requirements_win.txt -q

echo [2/3] PyInstaller 빌드 중...
pyinstaller build.spec --clean --noconfirm

echo [3/3] 완료!
echo.
echo 실행 파일 위치: dist\RSI_MACD_Trader\RSI_MACD_Trader.exe
echo.
pause
