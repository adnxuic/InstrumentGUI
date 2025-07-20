from PySide6.QtWidgets import QWidget, QScrollArea, QVBoxLayout
from PySide6.QtCore import Qt

import matplotlib as mpl
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.backends.backend_qtagg import (
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.style import use

import numpy as np
from numpy import (sin, cos, tan, pi,
                   exp, log,
                   sinh, cosh, tanh, arcsin, arccos, arctan, arcsinh)

mpl.use("QtAgg")


#
# mpl.rcParams['text.usetex'] = True
# preamble = r'\usepackage{amsmath,amssymb,amsthm}'
# mpl.rcParams['text.latex.preamble'] = preamble


class PyFigureCanvas(QWidget):
    def __init__(self, parent=None, width=4, height=3, dpi=100, style=None):
        super().__init__()

        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.canva = FigureCanvasQTAgg(self.fig)
        self.canva.setFixedSize(width * dpi, height * dpi)

        self.init_set()

    def init_set(self):
        # 添加滚动条
        self.scroArea = QScrollArea()
        self.scroArea.setWidget(self.canva)
        self.scroArea.setAlignment(Qt.AlignCenter)
        self.scroArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)  # 设置显示策略
        self.scroArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)  # 设置显示策略

        layout = QVBoxLayout()

        toolbox = NavigationToolbar(self.canva, self)

        layout.addWidget(toolbox)
        layout.addWidget(self.scroArea)

        self.setLayout(layout)
