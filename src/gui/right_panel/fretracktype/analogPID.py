from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                               QLabel, QLineEdit, QPushButton, QSpinBox, QDoubleSpinBox, QSlider)
from PySide6.QtCore import Qt


class PyAnalogPID(QWidget):
    def __init__(self, instruments_control=None):
        super().__init__()
        self.instruments_control = instruments_control
        
        # 选中的仪器实例
        self.selected_wf1947 = None
        self.selected_sr830 = None
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("模拟PID控制器")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #8e44ad;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 模拟参数设置组
        analog_group = QGroupBox("模拟参数设置")
        analog_layout = QVBoxLayout()
        
        # 增益设置
        gain_layout = QHBoxLayout()
        gain_layout.addWidget(QLabel("增益 (Gain):"))
        self.gain_spinbox = QDoubleSpinBox()
        self.gain_spinbox.setRange(0.1, 100.0)
        self.gain_spinbox.setValue(10.0)
        self.gain_spinbox.setDecimals(2)
        gain_layout.addWidget(self.gain_spinbox)
        analog_layout.addLayout(gain_layout)
        
        # 时间常数
        time_const_layout = QHBoxLayout()
        time_const_layout.addWidget(QLabel("时间常数 (τ):"))
        self.time_const_spinbox = QDoubleSpinBox()
        self.time_const_spinbox.setRange(0.001, 10.0)
        self.time_const_spinbox.setValue(0.1)
        self.time_const_spinbox.setDecimals(3)
        self.time_const_spinbox.setSuffix(" s")
        time_const_layout.addWidget(self.time_const_spinbox)
        analog_layout.addLayout(time_const_layout)
        
        # 带宽设置
        bandwidth_layout = QHBoxLayout()
        bandwidth_layout.addWidget(QLabel("带宽 (Hz):"))
        self.bandwidth_spinbox = QDoubleSpinBox()
        self.bandwidth_spinbox.setRange(1.0, 10000.0)
        self.bandwidth_spinbox.setValue(100.0)
        self.bandwidth_spinbox.setDecimals(1)
        bandwidth_layout.addWidget(self.bandwidth_spinbox)
        analog_layout.addLayout(bandwidth_layout)
        
        analog_group.setLayout(analog_layout)
        layout.addWidget(analog_group)
        
        # 滤波器设置组
        filter_group = QGroupBox("滤波器设置")
        filter_layout = QVBoxLayout()
        
        # 低通滤波器截止频率
        lpf_layout = QHBoxLayout()
        lpf_layout.addWidget(QLabel("低通滤波器截止频率:"))
        self.lpf_freq_spinbox = QDoubleSpinBox()
        self.lpf_freq_spinbox.setRange(1.0, 1000.0)
        self.lpf_freq_spinbox.setValue(50.0)
        self.lpf_freq_spinbox.setDecimals(1)
        self.lpf_freq_spinbox.setSuffix(" Hz")
        lpf_layout.addWidget(self.lpf_freq_spinbox)
        filter_layout.addLayout(lpf_layout)
        
        # 相位补偿滑块
        phase_layout = QVBoxLayout()
        phase_layout.addWidget(QLabel("相位补偿:"))
        self.phase_slider = QSlider(Qt.Orientation.Horizontal)
        self.phase_slider.setRange(-180, 180)
        self.phase_slider.setValue(0)
        self.phase_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.phase_slider.setTickInterval(30)
        
        self.phase_value_label = QLabel("0°")
        self.phase_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.phase_slider.valueChanged.connect(lambda v: self.phase_value_label.setText(f"{v}°"))
        
        phase_layout.addWidget(self.phase_slider)
        phase_layout.addWidget(self.phase_value_label)
        filter_layout.addLayout(phase_layout)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # 目标设置组
        target_group = QGroupBox("目标设置")
        target_layout = QVBoxLayout()
        
        target_freq_layout = QHBoxLayout()
        target_freq_layout.addWidget(QLabel("目标频率 (Hz):"))
        self.target_freq_spinbox = QDoubleSpinBox()
        self.target_freq_spinbox.setRange(0.0, 1000000.0)
        self.target_freq_spinbox.setValue(1000.0)
        self.target_freq_spinbox.setDecimals(1)
        target_freq_layout.addWidget(self.target_freq_spinbox)
        target_layout.addLayout(target_freq_layout)
        
        # 容差设置
        tolerance_layout = QHBoxLayout()
        tolerance_layout.addWidget(QLabel("频率容差:"))
        self.tolerance_spinbox = QDoubleSpinBox()
        self.tolerance_spinbox.setRange(0.1, 100.0)
        self.tolerance_spinbox.setValue(1.0)
        self.tolerance_spinbox.setDecimals(2)
        self.tolerance_spinbox.setSuffix(" Hz")
        tolerance_layout.addWidget(self.tolerance_spinbox)
        target_layout.addLayout(tolerance_layout)
        
        target_group.setLayout(target_layout)
        layout.addWidget(target_group)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("启动模拟PID")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:pressed {
                background-color: #7d3c98;
            }
        """)
        
        self.stop_button = QPushButton("停止控制")
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
            QPushButton:pressed {
                background-color: #ba4a00;
            }
        """)
        self.stop_button.setEnabled(False)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        layout.addLayout(button_layout)
        
        # 状态显示
        status_group = QGroupBox("实时状态")
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("状态: 待机")
        self.current_freq_label = QLabel("当前频率: -- Hz")
        self.phase_error_label = QLabel("相位误差: -- °")
        self.output_voltage_label = QLabel("输出电压: -- V")
        
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.current_freq_label)
        status_layout.addWidget(self.phase_error_label)
        status_layout.addWidget(self.output_voltage_label)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # 连接信号槽
        self.start_button.clicked.connect(self.start_analog_control)
        self.stop_button.clicked.connect(self.stop_analog_control)
        
        layout.addStretch()
        self.setLayout(layout)
        
    def start_analog_control(self):
        """开始模拟PID控制"""
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_label.setText("状态: 模拟PID控制中...")
        print("模拟PID控制开始")
        
    def stop_analog_control(self):
        """停止模拟PID控制"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("状态: 待机")
        print("模拟PID控制停止")
        
    def set_selected_instruments(self, wf1947, sr830):
        """设置选中的仪器实例"""
        self.selected_wf1947 = wf1947
        self.selected_sr830 = sr830
        
        # 如果有仪器，显示已选择状态
        if wf1947 and sr830:
            print(f"模拟PID控制器已设置仪器: WF1947={wf1947.type}, SR830={sr830.type}")
        else:
            print("模拟PID控制器仪器已清除")