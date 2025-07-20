import sys
from typing import Optional

from PySide6.QtWidgets import QFrame, QVBoxLayout, QTabWidget

import matplotlib

import os

current_path = os.path.dirname(os.path.abspath(__file__))
qss_path = os.path.join(current_path, "style.qss")

matplotlib.use("QtAgg")


class PyFigureWindow(QFrame):
    def __init__(self):
        super().__init__()

        self.setObjectName('figure_window')
        with open(qss_path, "r") as f:
            self.setStyleSheet(f.read())
        
        