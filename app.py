import sys
import os

# 패키징 후 경로 문제 해결
if getattr(sys, "frozen", False):
    os.chdir(sys._MEIPASS)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("RSI+MACD 자동매매")

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
