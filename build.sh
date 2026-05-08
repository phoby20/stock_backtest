#!/bin/bash
set -e

echo "================================================"
echo "  RSI+MACD 자동매매 프로그램 빌드 (macOS)"
echo "================================================"

echo "[1/3] 의존성 설치 중..."
pip install -r requirements_gui.txt -q

echo "[2/3] PyInstaller 빌드 중..."
pyinstaller build.spec --clean --noconfirm

echo "[3/3] 배포 패키지 생성 중..."
cd dist
zip -r RSI_MACD_Trader_macOS.zip RSI_MACD_Trader.app
cd ..

echo ""
echo "✅ 완료!"
echo "   앱 위치:    dist/RSI_MACD_Trader.app"
echo "   배포 파일:  dist/RSI_MACD_Trader_macOS.zip"
echo ""
