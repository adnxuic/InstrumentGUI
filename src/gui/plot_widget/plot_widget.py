import sys
from typing import Optional

from PySide6.QtWidgets import QFrame, QVBoxLayout, QTabWidget, QStackedLayout
from PySide6.QtCore import QTimer

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

        self.current_panel = None
        self.data_record_timer = None
        self.init_set()

    def init_set(self):
        self.data_record_figure_canvas = PyFigureCanvas()
        self.fre_sweeper_figure_canvas = PyFigureCanvas()
        self.fre_track_figure_canvas = PyFigureCanvas()

        # 设置不同canvas的图表类型
        self.data_record_figure_canvas.setup_data_record_plots()
        self.fre_sweeper_figure_canvas.setup_frequency_sweep_plot()
        self.fre_track_figure_canvas.setup_frequency_tracking_plot()
        
        # 创建堆叠布局
        self.stacked_layout = QStackedLayout(self)
        
        # 添加所有面板到堆叠布局
        self.stacked_layout.addWidget(self.data_record_figure_canvas)
        self.stacked_layout.addWidget(self.fre_sweeper_figure_canvas)
        self.stacked_layout.addWidget(self.fre_track_figure_canvas)
        
        # 设置默认数据记录显示面板
        self.stacked_layout.setCurrentWidget(self.data_record_figure_canvas)
        self.current_panel = "data_record"

    def switch_to_canvas(self, panel_name):
        """根据面板名称切换对应的canvas"""
        self.current_panel = panel_name
        
        if panel_name == "data_record":
            self.stacked_layout.setCurrentWidget(self.data_record_figure_canvas)
            # 重新设置数据记录图表
            self.data_record_figure_canvas.setup_data_record_plots()
        elif panel_name == "fre_sweeper":
            self.stacked_layout.setCurrentWidget(self.fre_sweeper_figure_canvas)
            # 重新设置频率扫描图表
            self.fre_sweeper_figure_canvas.setup_frequency_sweep_plot()
        elif panel_name == "fre_track":
            self.stacked_layout.setCurrentWidget(self.fre_track_figure_canvas)
            # 重新设置频率追踪图表
            self.fre_track_figure_canvas.setup_frequency_tracking_plot()
        # instrument_data面板不改变canvas，保持当前显示
        elif panel_name == "instrument_data":
            # 不切换canvas，保持当前状态
            pass
            
    def update_data_record_plots(self, plot_data):
        """更新数据记录图表"""
        if self.current_panel == "data_record":
            self.data_record_figure_canvas.update_data_record_plots(plot_data)
            
    def clear_data_record_plots(self):
        """清空数据记录图表"""
        self.data_record_figure_canvas.clear_data_record_plots()
        
    def start_data_record_updates(self, data_record_panel):
        """开始数据记录更新"""
        if self.data_record_timer:
            self.data_record_timer.stop()
            
        self.data_record_timer = QTimer()
        self.data_record_timer.timeout.connect(
            lambda: self._update_from_data_record(data_record_panel)
        )
        self.data_record_timer.start(1000)  # 每秒更新一次
        
    def stop_data_record_updates(self):
        """停止数据记录更新"""
        if self.data_record_timer:
            self.data_record_timer.stop()
            self.data_record_timer = None
            
    def _update_from_data_record(self, data_record_panel):
        """从数据记录面板获取数据并更新图表"""
        try:
            plot_data = data_record_panel.get_data_for_plotting()
            if plot_data:
                self.update_data_record_plots(plot_data)
        except Exception as e:
            print(f"更新图表数据时出错: {e}")
            
    def save_current_plot(self, filename):
        """保存当前图表"""
        current_canvas = self.stacked_layout.currentWidget()
        if current_canvas:
            return current_canvas.save_plot(filename)
        return False
        
    def get_current_canvas(self):
        """获取当前canvas"""
        return self.stacked_layout.currentWidget()
        
    def set_plot_settings(self, settings):
        """设置图表参数"""
        current_canvas = self.stacked_layout.currentWidget()
        if current_canvas and hasattr(current_canvas, 'set_max_points'):
            if 'max_points' in settings:
                current_canvas.set_max_points(settings['max_points'])
            if 'auto_scale' in settings:
                current_canvas.set_auto_scale(settings['auto_scale'])
        
        