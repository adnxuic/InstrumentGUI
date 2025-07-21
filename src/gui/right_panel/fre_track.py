from PySide6.QtWidgets import QWidget


class PyFreTrack(QWidget):
    def __init__(self, instruments_control=None):
        super().__init__()
        self.instruments_control = instruments_control