from PySide6.QtWidgets import QFrame, QStackedLayout
import os

from .instrument_data_show import PyInstrumentDataShow
from .data_record import PyDataRecord
from .fre_track import PyFreTrack
from .fre_sweeper import PyFreSweeper

current_path = os.path.dirname(os.path.abspath(__file__))
qss_path = os.path.join(current_path, "style.qss")

class PyRightPanel(QFrame):
    def __init__(self, instruments_control=None):
        super().__init__()

        self.setObjectName("right_panel")
        with open(qss_path, "r") as f:
            self.setStyleSheet(f.read())

        self.instruments_control = instruments_control
        self.init_set()

    def init_set(self):
        # 传递instruments_control到各个组件
        self.instrument_data_show = PyInstrumentDataShow(self.instruments_control)
        self.data_record = PyDataRecord(self.instruments_control)
        self.fre_sweeper = PyFreSweeper(self.instruments_control)
        self.fre_track = PyFreTrack(self.instruments_control)

        # 创建堆叠布局
        self.stacked_layout = QStackedLayout(self)
        
        # 添加所有面板到堆叠布局
        self.stacked_layout.addWidget(self.instrument_data_show)
        self.stacked_layout.addWidget(self.data_record)
        self.stacked_layout.addWidget(self.fre_sweeper)
        self.stacked_layout.addWidget(self.fre_track)
        
        # 设置默认显示仪器数据显示面板
        self.stacked_layout.setCurrentWidget(self.instrument_data_show)
        
        # 保存原始宽度
        self.original_width = 300
        self.setFixedWidth(self.original_width)
        
    def set_instruments_control(self, instruments_control):
        """设置仪器控制实例"""
        self.instruments_control = instruments_control
        
        # 传递给各个子组件
        if hasattr(self.instrument_data_show, 'set_instruments_control'):
            self.instrument_data_show.set_instruments_control(instruments_control)
        if hasattr(self.data_record, 'set_instruments_control'):
            self.data_record.set_instruments_control(instruments_control)
        if hasattr(self.fre_sweeper, 'set_instruments_control'):
            self.fre_sweeper.set_instruments_control(instruments_control)
        if hasattr(self.fre_track, 'set_instruments_control'):
            self.fre_track.set_instruments_control(instruments_control)
        
    def switch_to_panel(self, panel_name):
        """根据面板名称切换到对应面板"""
        if panel_name == "instrument_data":
            self.stacked_layout.setCurrentWidget(self.instrument_data_show)
        elif panel_name == "data_record":
            self.stacked_layout.setCurrentWidget(self.data_record)
        elif panel_name == "fre_sweeper":
            self.stacked_layout.setCurrentWidget(self.fre_sweeper)
        elif panel_name == "fre_track":
            self.stacked_layout.setCurrentWidget(self.fre_track)

        # 如果面板当前是隐藏的，显示它
        if not self.isVisible():
            self.show_panel()
            
    def hide_panel(self):
        """隐藏面板"""
        self.setVisible(False)
        self.setFixedWidth(0)
        
    def show_panel(self):
        """显示面板"""
        self.setVisible(True)
        self.setFixedWidth(self.original_width)
        
    def get_current_panel(self):
        """获取当前面板"""
        current_widget = self.stacked_layout.currentWidget()
        if current_widget == self.instrument_data_show:
            return "instrument_data", self.instrument_data_show
        elif current_widget == self.data_record:
            return "data_record", self.data_record
        elif current_widget == self.fre_sweeper:
            return "fre_sweeper", self.fre_sweeper
        elif current_widget == self.fre_track:
            return "fre_track", self.fre_track
        return None, None
        
