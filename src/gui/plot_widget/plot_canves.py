from PySide6.QtWidgets import QWidget

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