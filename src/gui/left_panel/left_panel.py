from PySide6.QtWidgets import QFrame, QStackedLayout
from PySide6.QtCore import QPropertyAnimation, QEasingCurve

from .datapanel import PyDataPanel
from .instrumentspanel import PyInstrumentsPanel

import os

current_path = os.path.dirname(os.path.abspath(__file__))
qss_path = os.path.join(current_path, "style.qss")

class PyLeftPanel(QFrame):
    def __init__(self, instruments_control=None):
        super().__init__()
        self.instruments_control = instruments_control

        self.setObjectName("left_panel")
        with open(qss_path, "r") as f:
            self.setStyleSheet(f.read())

        self.init_set()

    def init_set(self):
        self.instruments_panel = PyInstrumentsPanel(self.instruments_control)
        self.data_panel = PyDataPanel()
        
        # 创建堆叠布局
        self.stacked_layout = QStackedLayout(self)
        
        self.stacked_layout.addWidget(self.instruments_panel)
        self.stacked_layout.addWidget(self.data_panel)
        
        # 设置默认显示仪器面板
        self.stacked_layout.setCurrentWidget(self.instruments_panel)
        
        # 保存原始宽度
        self.original_width = 200
        self.setFixedWidth(self.original_width)
        
    def switch_to_panel(self, panel_name):
        """切换到指定面板"""
        if panel_name == "instruments":
            self.stacked_layout.setCurrentWidget(self.instruments_panel)
        elif panel_name == "data":
            self.stacked_layout.setCurrentWidget(self.data_panel)
        
        # 如果面板当前是隐藏的，显示它
        if not self.isVisible():
            self.show_panel()
            
    def show_panel(self):
        """显示面板"""
        self.setVisible(True)
        self.setFixedWidth(self.original_width)
        
    def hide_panel(self):
        """隐藏面板"""
        self.setVisible(False)
        self.setFixedWidth(0)