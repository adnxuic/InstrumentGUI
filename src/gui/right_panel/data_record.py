from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QLabel, QSpinBox, QDoubleSpinBox, QComboBox, QPushButton,
    QCheckBox, QProgressBar, QTextEdit, QGroupBox, QFormLayout,
    QMessageBox, QFileDialog, QLineEdit
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from component.datasort import DataRecordThread, DataSort

class PyDataRecord(QWidget):
    def __init__(self, instruments_control=None):
        super().__init__()
        self.instruments_control = instruments_control
        
        # 初始化数据组件
        self.data_record_thread = None
        self.data_sort = DataSort()
        
        # UI状态
        self.is_recording = False
        
        self.init_ui()
        self.connect_signals()
        
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # 创建标题
        title_label = QLabel("数据记录")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 记录设置组
        self.create_recording_settings_group(layout)
        
        # 图表设置组
        self.create_plot_settings_group(layout)
        
        # 控制按钮组
        self.create_control_buttons_group(layout)
        
        # 状态显示组
        self.create_status_group(layout)
        
        # 日志显示
        self.create_log_group(layout)
        
        layout.addStretch()
        
    def create_recording_settings_group(self, parent_layout):
        """创建记录设置组"""
        group = QGroupBox("记录设置")
        layout = QFormLayout()
        
        # 时间步长设置
        self.time_step_spinbox = QDoubleSpinBox()
        self.time_step_spinbox.setRange(0.1, 3600.0)
        self.time_step_spinbox.setValue(1.0)
        self.time_step_spinbox.setSuffix(" 秒")
        self.time_step_spinbox.setDecimals(1)
        layout.addRow("时间步长:", self.time_step_spinbox)
        
        # 记录时长设置
        duration_layout = QHBoxLayout()
        self.unlimited_checkbox = QCheckBox("无限时记录")
        self.unlimited_checkbox.setChecked(True)
        duration_layout.addWidget(self.unlimited_checkbox)
        
        self.duration_spinbox = QSpinBox()
        self.duration_spinbox.setRange(1, 86400)  # 1秒到24小时
        self.duration_spinbox.setValue(3600)  # 默认1小时
        self.duration_spinbox.setSuffix(" 秒")
        self.duration_spinbox.setEnabled(False)
        duration_layout.addWidget(self.duration_spinbox)
        
        layout.addRow("记录时长:", duration_layout)
        
        # 数据保存文件名
        self.filename_lineedit = QLineEdit()
        self.filename_lineedit.setPlaceholderText("留空将自动生成文件名")
        layout.addRow("保存文件名:", self.filename_lineedit)
        
        group.setLayout(layout)
        parent_layout.addWidget(group)
        
    def create_plot_settings_group(self, parent_layout):
        """创建图表设置组"""
        group = QGroupBox("图表设置")
        layout = QGridLayout()
        
        # 第一个图表设置
        layout.addWidget(QLabel("图表1 - X轴:"), 0, 0)
        self.plot1_x_combo = QComboBox()
        self.plot1_x_combo.addItems(["time"])
        layout.addWidget(self.plot1_x_combo, 0, 1)
        
        layout.addWidget(QLabel("图表1 - Y轴:"), 0, 2)
        self.plot1_y_combo = QComboBox()
        self.plot1_y_combo.addItems(["请先连接仪器"])
        layout.addWidget(self.plot1_y_combo, 0, 3)
        
        # 第二个图表设置
        layout.addWidget(QLabel("图表2 - X轴:"), 1, 0)
        self.plot2_x_combo = QComboBox()
        self.plot2_x_combo.addItems(["time"])
        layout.addWidget(self.plot2_x_combo, 1, 1)
        
        layout.addWidget(QLabel("图表2 - Y轴:"), 1, 2)
        self.plot2_y_combo = QComboBox()
        self.plot2_y_combo.addItems(["请先连接仪器"])
        layout.addWidget(self.plot2_y_combo, 1, 3)
        
        # 刷新数据选项按钮
        refresh_button = QPushButton("刷新数据选项")
        refresh_button.clicked.connect(self.refresh_data_options)
        layout.addWidget(refresh_button, 2, 0, 1, 4)
        
        group.setLayout(layout)
        parent_layout.addWidget(group)
        
    def create_control_buttons_group(self, parent_layout):
        """创建控制按钮组"""
        group = QGroupBox("控制")
        layout = QHBoxLayout()
        
        self.start_button = QPushButton("开始记录")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("停止记录")
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        layout.addWidget(self.stop_button)
        
        self.save_button = QPushButton("保存数据")
        self.save_button.setEnabled(False)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        layout.addWidget(self.save_button)
        
        group.setLayout(layout)
        parent_layout.addWidget(group)
        
    def create_status_group(self, parent_layout):
        """创建状态显示组"""
        group = QGroupBox("状态")
        layout = QVBoxLayout()
        
        # 记录状态
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("状态:"))
        self.status_label = QLabel("待机")
        self.status_label.setStyleSheet("QLabel { color: #666; }")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)
        
        # 记录时间
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("记录时间:"))
        self.time_label = QLabel("00:00:00")
        self.time_label.setStyleSheet("QLabel { font-family: monospace; font-size: 14px; }")
        time_layout.addWidget(self.time_label)
        time_layout.addStretch()
        layout.addLayout(time_layout)
        
        # 数据点计数
        count_layout = QHBoxLayout()
        count_layout.addWidget(QLabel("数据点数:"))
        self.count_label = QLabel("0")
        self.count_label.setStyleSheet("QLabel { font-family: monospace; font-size: 14px; }")
        count_layout.addWidget(self.count_label)
        count_layout.addStretch()
        layout.addLayout(count_layout)
        
        # 进度条（对于有限时记录）
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        group.setLayout(layout)
        parent_layout.addWidget(group)
        
    def create_log_group(self, parent_layout):
        """创建日志显示组"""
        group = QGroupBox("日志")
        layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(100)
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                font-family: monospace;
                font-size: 10px;
                background-color: #f5f5f5;
            }
        """)
        layout.addWidget(self.log_text)
        
        # 清除日志按钮
        clear_log_button = QPushButton("清除日志")
        clear_log_button.clicked.connect(self.clear_log)
        layout.addWidget(clear_log_button)
        
        group.setLayout(layout)
        parent_layout.addWidget(group)
        
    def connect_signals(self):
        """连接信号槽"""
        # 控制按钮
        self.start_button.clicked.connect(self.start_recording)
        self.stop_button.clicked.connect(self.stop_recording)
        self.save_button.clicked.connect(self.save_data)
        
        # 无限时记录复选框
        self.unlimited_checkbox.toggled.connect(self.on_unlimited_toggled)
        
        # 状态更新定时器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status_display)
        
    def set_instruments_control(self, instruments_control):
        """设置仪器控制实例"""
        self.instruments_control = instruments_control
        self.refresh_data_options()
        
    def refresh_data_options(self):
        """刷新数据选项"""
        if not self.instruments_control:
            return
            
        # 获取可用的数据列
        options = ["time"]
        
        # 添加SR830选项
        for address, instrument in self.instruments_control.instruments_instance.items():
            if hasattr(instrument, 'type') and instrument.type == "SR830":
                options.extend([
                    f"SR830_{address}_X", f"SR830_{address}_Y",
                    f"SR830_{address}_R", f"SR830_{address}_theta"
                ])
        
        # 添加PPMS选项
        for address, instrument in self.instruments_control.instruments_instance.items():
            if hasattr(instrument, 'type') and instrument.type == "PPMS":
                options.extend([
                    f"PPMS_{address}_temperature", f"PPMS_{address}_field"
                ])
        
        # 更新下拉框
        for combo in [self.plot1_x_combo, self.plot1_y_combo, 
                     self.plot2_x_combo, self.plot2_y_combo]:
            current_text = combo.currentText()
            combo.clear()
            combo.addItems(options)
            
            # 尝试恢复之前的选择
            index = combo.findText(current_text)
            if index >= 0:
                combo.setCurrentIndex(index)
        
        # 设置默认值
        if len(options) > 1:
            self.plot1_y_combo.setCurrentText(options[1])
        if len(options) > 2:
            self.plot2_y_combo.setCurrentText(options[2])
            
    def start_recording(self):
        """开始记录"""
        if not self.instruments_control:
            self.add_log("错误: 未连接仪器控制系统")
            return
            
        if not self.instruments_control.instruments_instance:
            self.add_log("错误: 没有连接的仪器")
            return
        
        try:
            # 获取记录参数
            time_step = self.time_step_spinbox.value()
            max_duration = None if self.unlimited_checkbox.isChecked() else self.duration_spinbox.value()
            
            # 创建记录线程
            self.data_record_thread = DataRecordThread(
                self.instruments_control, time_step, max_duration
            )
            
            # 连接信号
            self.data_record_thread.data_acquired.connect(self.on_data_acquired)
            self.data_record_thread.recording_finished.connect(self.on_recording_finished)
            self.data_record_thread.error_occurred.connect(self.on_error_occurred)
            self.data_record_thread.time_updated.connect(self.on_time_updated)
            
            # 开始记录
            self.data_record_thread.start_recording()
            
            # 更新UI状态
            self.is_recording = True
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.save_button.setEnabled(False)
            self.status_label.setText("记录中...")
            self.status_label.setStyleSheet("QLabel { color: #4CAF50; font-weight: bold; }")
            
            # 设置进度条
            if not self.unlimited_checkbox.isChecked():
                self.progress_bar.setVisible(True)
                self.progress_bar.setMaximum(int(max_duration))
                self.progress_bar.setValue(0)
            
            # 启动状态更新定时器
            self.status_timer.start(1000)  # 每秒更新一次
            
            # 清空数据
            self.data_sort.clear_data()
            
            self.add_log(f"开始记录 - 时间步长: {time_step}s, 最大时长: {max_duration or '无限'}s")
            
        except Exception as e:
            self.add_log(f"启动记录失败: {e}")
            QMessageBox.critical(self, "错误", f"启动记录失败:\n{e}")
            
    def stop_recording(self):
        """停止记录"""
        if self.data_record_thread and self.is_recording:
            self.data_record_thread.stop_recording()
            
    def save_data(self):
        """保存数据"""
        if not self.data_record_thread:
            return
            
        try:
            filename = self.filename_lineedit.text().strip()
            if not filename:
                filename = None
                
            success = self.data_record_thread.save_final_data(filename)
            if success:
                self.add_log("数据保存成功")
                QMessageBox.information(self, "成功", "数据已保存到 history_data 文件夹")
            else:
                self.add_log("数据保存失败")
                
        except Exception as e:
            self.add_log(f"保存数据时出错: {e}")
            QMessageBox.critical(self, "错误", f"保存数据失败:\n{e}")
            
    def on_unlimited_toggled(self, checked):
        """无限时记录复选框状态改变"""
        self.duration_spinbox.setEnabled(not checked)
        
    def on_data_acquired(self, data_point):
        """接收到新数据"""
        self.data_sort.update_data(data_point)
        
        # 更新数据点计数
        count = len(self.data_sort.current_data)
        self.count_label.setText(str(count))
        
        # 发送数据到图表 (这里需要连接到plot widget)
        # TODO: 实现图表更新信号
        
    def on_recording_finished(self):
        """记录完成"""
        self.is_recording = False
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.save_button.setEnabled(True)
        self.status_label.setText("记录完成")
        self.status_label.setStyleSheet("QLabel { color: #2196F3; font-weight: bold; }")
        
        self.progress_bar.setVisible(False)
        self.status_timer.stop()
        
        self.add_log("记录完成")
        
    def on_error_occurred(self, error_message):
        """发生错误"""
        self.add_log(f"错误: {error_message}")
        
    def on_time_updated(self, elapsed_time):
        """时间更新"""
        # 更新时间显示
        hours = int(elapsed_time // 3600)
        minutes = int((elapsed_time % 3600) // 60)
        seconds = int(elapsed_time % 60)
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.time_label.setText(time_str)
        
        # 更新进度条
        if not self.unlimited_checkbox.isChecked():
            self.progress_bar.setValue(int(elapsed_time))
            
    def update_status_display(self):
        """更新状态显示"""
        # 这个方法可以用于定期更新UI状态
        pass
        
    def add_log(self, message):
        """添加日志消息"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
        # 自动滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.End)
        self.log_text.setTextCursor(cursor)
        
    def clear_log(self):
        """清除日志"""
        self.log_text.clear()
        
    def get_plot_settings(self):
        """获取图表设置"""
        return {
            'plot1': {
                'x_axis': self.plot1_x_combo.currentText(),
                'y_axis': self.plot1_y_combo.currentText()
            },
            'plot2': {
                'x_axis': self.plot2_x_combo.currentText(),
                'y_axis': self.plot2_y_combo.currentText()
            }
        }
        
    def get_data_for_plotting(self):
        """获取用于绘图的数据"""
        if not self.data_sort.current_data:
            return None
            
        plot_settings = self.get_plot_settings()
        
        # 获取两个图表的数据
        plot1_x, plot1_y = self.data_sort.get_data_for_plotting(
            plot_settings['plot1']['x_axis'],
            plot_settings['plot1']['y_axis']
        )
        
        plot2_x, plot2_y = self.data_sort.get_data_for_plotting(
            plot_settings['plot2']['x_axis'],
            plot_settings['plot2']['y_axis']
        )
        
        return {
            'plot1': {'x': plot1_x, 'y': plot1_y},
            'plot2': {'x': plot2_x, 'y': plot2_y},
            'settings': plot_settings
        }