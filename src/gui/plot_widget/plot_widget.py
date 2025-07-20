import sys
from typing import Optional

from PySide6.QtWidgets import QFrame, QVBoxLayout, QTabWidget, QStackedLayout

from .plot_canves import PyFigureCanvas

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

        self.init_set()

    def init_set(self):
        self.data_record_figure_canvas = PyFigureCanvas()
        self.fre_sweeper_figure_canvas = PyFigureCanvas()
        self.fre_track_figure_canvas = PyFigureCanvas()

        # 创建堆叠布局
        self.stacked_layout = QStackedLayout(self)
        
        # 添加所有面板到堆叠布局
        self.stacked_layout.addWidget(self.data_record_figure_canvas)
        self.stacked_layout.addWidget(self.fre_sweeper_figure_canvas)
        self.stacked_layout.addWidget(self.fre_track_figure_canvas)
        
        # 设置默认数据记录显示面板
        self.stacked_layout.setCurrentWidget(self.data_record_figure_canvas)

    def switch_to_canvas(self, panel_name):
        """根据面板名称切换对应的canvas"""
        if panel_name == "data_record":
            self.stacked_layout.setCurrentWidget(self.data_record_figure_canvas)
        elif panel_name == "fre_sweeper":
            self.stacked_layout.setCurrentWidget(self.fre_sweeper_figure_canvas)
        elif panel_name == "fre_track":
            self.stacked_layout.setCurrentWidget(self.fre_track_figure_canvas)
        # instrument_data面板没有对应的canvas，保持当前canvas不变
        
        