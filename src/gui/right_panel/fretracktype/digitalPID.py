from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                               QLabel, QLineEdit, QPushButton, QSpinBox, QDoubleSpinBox,
                               QCheckBox, QMessageBox, QFileDialog)
from PySide6.QtCore import Qt, QTimer
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../.."))
from src.component.PID import FrequencyTrackingThread
from datetime import datetime


class PyDigitalPID(QWidget):
    def __init__(self, instruments_control=None):
        super().__init__()
        self.instruments_control = instruments_control
        
        # 频率追踪线程
        self.tracking_thread = None
        
        # 追踪数据
        self.tracking_data = []
        self.max_display_points = 1000
        
        # 定时器用于更新显示
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        
        # 自动保存标志
        self.auto_save_enabled = True
        
        # 选中的仪器实例
        self.selected_wf1947 = None
        self.selected_sr830 = None
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("数字PID控制器")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # PID参数设置组
        pid_group = QGroupBox("PID参数设置")
        pid_layout = QVBoxLayout()
        
        # P参数
        p_layout = QHBoxLayout()
        p_layout.addWidget(QLabel("比例系数 (Kp):"))
        self.kp_spinbox = QDoubleSpinBox()
        self.kp_spinbox.setRange(0.0, 1000.0)
        self.kp_spinbox.setValue(1.0)
        self.kp_spinbox.setDecimals(3)
        p_layout.addWidget(self.kp_spinbox)
        pid_layout.addLayout(p_layout)
        
        # I参数
        i_layout = QHBoxLayout()
        i_layout.addWidget(QLabel("积分系数 (Ki):"))
        self.ki_spinbox = QDoubleSpinBox()
        self.ki_spinbox.setRange(0.0, 1000.0)
        self.ki_spinbox.setValue(0.1)
        self.ki_spinbox.setDecimals(3)
        i_layout.addWidget(self.ki_spinbox)
        pid_layout.addLayout(i_layout)
        
        # D参数
        d_layout = QHBoxLayout()
        d_layout.addWidget(QLabel("微分系数 (Kd):"))
        self.kd_spinbox = QDoubleSpinBox()
        self.kd_spinbox.setRange(0.0, 1000.0)
        self.kd_spinbox.setValue(0.01)
        self.kd_spinbox.setDecimals(3)
        d_layout.addWidget(self.kd_spinbox)
        pid_layout.addLayout(d_layout)
        
        pid_group.setLayout(pid_layout)
        layout.addWidget(pid_group)
        
        # 目标值设置组
        target_group = QGroupBox("目标设置")
        target_layout = QVBoxLayout()
        
        target_freq_layout = QHBoxLayout()
        target_freq_layout.addWidget(QLabel("目标相位(°):"))
        self.target_freq_spinbox = QDoubleSpinBox()
        self.target_freq_spinbox.setRange(-180.0, 180.0)
        self.target_freq_spinbox.setValue(0.0)
        self.target_freq_spinbox.setDecimals(2)
        target_freq_layout.addWidget(self.target_freq_spinbox)
        target_layout.addLayout(target_freq_layout)
        
        target_group.setLayout(target_layout)
        layout.addWidget(target_group)
        
        # 追踪设置组
        tracking_group = QGroupBox("追踪设置")
        tracking_layout = QVBoxLayout()
        
        # 采样间隔
        sample_layout = QHBoxLayout()
        sample_layout.addWidget(QLabel("采样间隔(s):"))
        self.sample_interval_spinbox = QDoubleSpinBox()
        self.sample_interval_spinbox.setRange(0.05, 10.0)
        self.sample_interval_spinbox.setValue(0.1)
        self.sample_interval_spinbox.setDecimals(2)
        sample_layout.addWidget(self.sample_interval_spinbox)
        tracking_layout.addLayout(sample_layout)
        
        # 自动保存选项
        self.auto_save_checkbox = QCheckBox("自动保存数据")
        self.auto_save_checkbox.setChecked(True)
        tracking_layout.addWidget(self.auto_save_checkbox)
        
        tracking_group.setLayout(tracking_layout)
        layout.addWidget(tracking_group)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("开始跟踪")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
            QPushButton:pressed {
                background-color: #229954;
            }
        """)
        
        self.stop_button = QPushButton("停止跟踪")
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        self.stop_button.setEnabled(False)
        
        self.save_button = QPushButton("手动保存")
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.save_button)
        layout.addLayout(button_layout)
        
        # 状态显示
        status_group = QGroupBox("状态信息")
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("状态: 待机")
        self.current_freq_label = QLabel("当前频率: -- Hz")
        self.current_phase_label = QLabel("当前相位: -- °")
        self.error_label = QLabel("相位误差: -- °")
        self.pid_output_label = QLabel("PID输出: -- Hz/s")
        self.data_points_label = QLabel("数据点数: 0")
        
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.current_freq_label)
        status_layout.addWidget(self.current_phase_label)
        status_layout.addWidget(self.error_label)
        status_layout.addWidget(self.pid_output_label)
        status_layout.addWidget(self.data_points_label)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # 连接信号槽
        self.start_button.clicked.connect(self.start_tracking)
        self.stop_button.clicked.connect(self.stop_tracking)
        self.save_button.clicked.connect(self.save_data_manually)
        self.auto_save_checkbox.toggled.connect(self.on_auto_save_toggled)
        
        layout.addStretch()
        self.setLayout(layout)
        
    def start_tracking(self):
        """开始数字PID跟踪"""
        try:
            # 检查是否已选择仪器
            if not self.selected_wf1947 or not self.selected_sr830:
                QMessageBox.warning(self, "错误", "请先在频率追踪面板中选择WF1947和SR830仪器")
                return
                
            # 获取PID参数
            pid_params = {
                'kp': self.kp_spinbox.value(),
                'ki': self.ki_spinbox.value(),
                'kd': self.kd_spinbox.value(),
                'setpoint': self.target_freq_spinbox.value()
            }
            
            # 创建追踪线程，直接传递选中的仪器实例
            self.tracking_thread = FrequencyTrackingThread(
                self.selected_wf1947,
                self.selected_sr830, 
                pid_params
            )
            
            # 设置追踪参数
            sample_interval = self.sample_interval_spinbox.value()
            self.tracking_thread.set_tracking_params(sample_interval)
            
            # 连接信号
            self.tracking_thread.data_updated.connect(self.on_data_updated)
            self.tracking_thread.tracking_finished.connect(self.on_tracking_finished)
            self.tracking_thread.error_occurred.connect(self.on_error_occurred)
            self.tracking_thread.status_updated.connect(self.on_status_updated)
            
            # 清空数据
            self.tracking_data = []
            
            # 开始追踪
            self.tracking_thread.start_tracking()
            
            # 更新UI状态
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.save_button.setEnabled(False)  # 追踪期间禁用手动保存
            
            # 启动显示更新定时器
            self.update_timer.start(500)  # 每500ms更新一次显示
            
            print("数字PID频率追踪开始")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动追踪失败: {e}")
            print(f"启动追踪错误: {e}")
        
    def stop_tracking(self):
        """停止数字PID跟踪"""
        try:
            if self.tracking_thread and self.tracking_thread.is_tracking:
                self.tracking_thread.stop_tracking()
                
            # 停止显示更新定时器
            self.update_timer.stop()
            
            print("数字PID频率追踪停止")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"停止追踪失败: {e}")
            print(f"停止追踪错误: {e}")
            
    def on_data_updated(self, data_point):
        """处理新的数据点"""
        self.tracking_data.append(data_point)
        
        # 限制数据点数量以节省内存
        if len(self.tracking_data) > self.max_display_points:
            self.tracking_data = self.tracking_data[-self.max_display_points:]
            
        # 发送数据到绘图组件
        self.emit_plot_data()
            
    def on_tracking_finished(self):
        """追踪完成处理"""
        # 更新UI状态
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.save_button.setEnabled(True)
        self.status_label.setText("状态: 追踪完成")
        
        # 停止显示更新定时器
        self.update_timer.stop()
        
        # 自动保存数据
        if self.auto_save_checkbox.isChecked() and self.tracking_data:
            self.save_data_automatically()
            
    def on_error_occurred(self, error_message):
        """处理错误"""
        print(f"追踪错误: {error_message}")
        QMessageBox.warning(self, "追踪错误", error_message)
        
    def on_status_updated(self, status):
        """更新状态显示"""
        self.status_label.setText(f"状态: {status}")
        
    def update_display(self):
        """更新实时显示"""
        if not self.tracking_data:
            return
            
        latest_data = self.tracking_data[-1]
        
        # 更新状态显示
        self.current_freq_label.setText(f"当前频率: {latest_data.get('frequency', 0):.2f} Hz")
        self.current_phase_label.setText(f"当前相位: {latest_data.get('phase', 0):.2f} °")
        self.error_label.setText(f"相位误差: {latest_data.get('error', 0):.2f} °")
        self.pid_output_label.setText(f"PID输出: {latest_data.get('pid_output', 0):.2f} Hz/s")
        self.data_points_label.setText(f"数据点数: {len(self.tracking_data)}")
        
    def emit_plot_data(self):
        """发送绘图数据"""
        if not self.tracking_data:
            return
            
        # 准备绘图数据
        times = [point['time'] for point in self.tracking_data]
        frequencies = [point['frequency'] for point in self.tracking_data]
        phases = [point['phase'] for point in self.tracking_data]
        
        plot_data = {
            'frequency_tracking': {
                'time': times,
                'frequency': frequencies,
                'phase': phases
            }
        }
        
        # 通知父组件更新图表（需要在父组件中实现）
        if hasattr(self.parent(), 'update_frequency_tracking_plot'):
            self.parent().update_frequency_tracking_plot(plot_data)
            
    def save_data_manually(self):
        """手动保存数据"""
        if not self.tracking_data:
            QMessageBox.information(self, "提示", "没有数据可保存")
            return
            
        # 选择保存文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"frequency_tracking_{timestamp}.dat"
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "保存追踪数据",
            os.path.join("history_data", default_filename),
            "Data files (*.dat);;All files (*.*)"
        )
        
        if filename:
            success, message = self.save_tracking_data(filename)
            if success:
                QMessageBox.information(self, "成功", message)
            else:
                QMessageBox.critical(self, "失败", message)
                
    def save_data_automatically(self):
        """自动保存数据"""
        if not self.tracking_data:
            return
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"history_data/frequency_tracking_{timestamp}.dat"
            
            success, message = self.save_tracking_data(filename)
            if success:
                print(f"数据自动保存成功: {message}")
            else:
                print(f"数据自动保存失败: {message}")
                
        except Exception as e:
            print(f"自动保存数据时出错: {e}")
            
    def save_tracking_data(self, filename):
        """保存追踪数据"""
        try:
            from src.component.datasort import DataSort
            
            # 确保history_data目录存在
            os.makedirs("history_data", exist_ok=True)
            
            success, message = DataSort.save_data_to_file(
                self.tracking_data, filename, "Frequency Tracking Data"
            )
            
            return success, message
            
        except Exception as e:
            return False, f"保存数据失败: {e}"
            
    def on_auto_save_toggled(self, checked):
        """自动保存选项切换"""
        self.auto_save_enabled = checked
        
    def set_selected_instruments(self, wf1947, sr830):
        """设置选中的仪器实例"""
        self.selected_wf1947 = wf1947
        self.selected_sr830 = sr830
        
        # 如果有仪器，显示已选择状态
        if wf1947 and sr830:
            print(f"数字PID控制器已设置仪器: WF1947={wf1947.type}, SR830={sr830.type}")
        else:
            print("数字PID控制器仪器已清除")