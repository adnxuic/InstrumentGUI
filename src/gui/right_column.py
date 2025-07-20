from PySide6.QtWidgets import QFrame
import os

current_path = os.path.dirname(os.path.abspath(__file__))
qss_path = os.path.join(current_path, "style.qss")

class PyRightColumn(QFrame):
    def __init__(self):
        super().__init__()

        self.setObjectName("right_column")
        with open(qss_path, "r") as f:
            self.setStyleSheet(f.read())
