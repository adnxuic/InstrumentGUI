from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                               QLabel, QLineEdit, QPushButton, QSpinBox, QDoubleSpinBox)
from PySide6.QtCore import Qt


class PyDigitalPID(QWidget):
    def __init__(self, instruments_control=None):
        super().__init__()
        self.instruments_control = instruments_control
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
        target_freq_layout.addWidget(QLabel("目标频率 (Hz):"))
        self.target_freq_spinbox = QDoubleSpinBox()
        self.target_freq_spinbox.setRange(0.0, 1000000.0)
        self.target_freq_spinbox.setValue(1000.0)
        self.target_freq_spinbox.setDecimals(1)
        target_freq_layout.addWidget(self.target_freq_spinbox)
        target_layout.addLayout(target_freq_layout)
        
        target_group.setLayout(target_layout)
        layout.addWidget(target_group)
        
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
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        layout.addLayout(button_layout)
        
        # 状态显示
        status_group = QGroupBox("状态信息")
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("状态: 待机")
        self.current_freq_label = QLabel("当前频率: -- Hz")
        self.error_label = QLabel("误差: -- Hz")
        
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.current_freq_label)
        status_layout.addWidget(self.error_label)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # 连接信号槽
        self.start_button.clicked.connect(self.start_tracking)
        self.stop_button.clicked.connect(self.stop_tracking)
        
        layout.addStretch()
        self.setLayout(layout)
        
    def start_tracking(self):
        """开始数字PID跟踪"""
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_label.setText("状态: 数字PID跟踪中...")
        print("数字PID跟踪开始")
        
    def stop_tracking(self):
        """停止数字PID跟踪"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("状态: 待机")
        print("数字PID跟踪停止")