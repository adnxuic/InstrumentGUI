from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QLabel, QSpinBox, QDoubleSpinBox, QComboBox, QPushButton,
    QCheckBox, QProgressBar, QTextEdit, QGroupBox, QFormLayout,
    QMessageBox, QFileDialog, QLineEdit, QSlider
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QFont, QTextCursor

import sys
import os
import time
import numpy as np
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from instruments.wf1947 import WF1947
from instruments.sr830 import SR830
from component.datasort import DataSort


class FrequencySweepThread(QThread):
    """频率扫描线程"""
    
    # 信号定义
    data_acquired = Signal(dict)  # 每次数据采集完成时发射
    sweep_finished = Signal()     # 扫描完成时发射
    error_occurred = Signal(str)  # 发生错误时发射
    progress_updated = Signal(int, int)  # 进度更新 (current, total)
    
    def __init__(self, wf1947_instrument, sr830_instrument, sweep_params):
        super().__init__()
        self.wf1947: WF1947 = wf1947_instrument
        self.sr830: SR830 = sr830_instrument
        self.sweep_params = sweep_params
        self.running = False
        self.sweep_data = []
        
    # def run(self):
    #     """执行频率扫描（使用WF1947内置扫描功能）"""
    #     try:
    #         self.running = True
    #         self.sweep_data = []
            
    #         # 获取扫描参数
    #         start_hz = self.sweep_params['start_hz']
    #         stop_hz = self.sweep_params['stop_hz']
    #         sweep_time_s = self.sweep_params['sweep_time_s']
    #         spacing = self.sweep_params['spacing']
    #         direction = self.sweep_params['direction']
    #         sample_interval = self.sweep_params['sample_interval']
            
    #         # 设置WF1947基本参数
    #         self.wf1947.set_waveform(self.sweep_params['waveform'])
    #         self.wf1947.set_amplitude(self.sweep_params['amplitude'])
    #         self.wf1947.set_offset(self.sweep_params['offset'])
            
    #         # 配置WF1947频率扫描
    #         self.wf1947.setup_frequency_sweep(
    #             start_hz=start_hz,
    #             stop_hz=stop_hz,
    #             sweep_time_s=sweep_time_s,
    #             spacing=spacing,
    #             direction=direction,
    #             load=self.sweep_params['load']
    #         )
            
    #         # 开启扫描输出
    #         self.wf1947.set_output(True)
            
    #         # 计算采样点数
    #         total_samples = int(sweep_time_s / sample_interval)
            
    #         # 在扫描过程中采样数据
    #         start_time = time.perf_counter()
    #         i = 0
    #         while time.perf_counter() - start_time < sweep_time_s and self.running and self.wf1947.get_frequency() <= stop_hz:
    #             o_time = time.perf_counter()
                
    #             # 从SR830读取数据
    #             try:
    #                 frequency_data = self.wf1947.get_frequency()
    #                 snap_data = self.sr830.getSnap(1, 2, 3, 4)
    #                 # 构建数据点
    #                 data_point = {
    #                     'frequency': frequency_data,
    #                     'X': snap_data[0],
    #                     'Y': snap_data[1], 
    #                     'R': snap_data[2],
    #                     'theta': snap_data[3],
    #                     'timestamp': time.time(),
    #                     'elapsed_time': time.perf_counter() - start_time
    #                 }
    #             except Exception as e:
    #                 # 如果读取失败，使用基于时间进度的估算作为备用
    #                 progress = (time.perf_counter() - start_time) / sweep_time_s
    #                 if spacing == 'LINear':
    #                     current_freq = start_hz + (stop_hz - start_hz) * progress
    #                 else:  # LOGarithmic
    #                     current_freq = start_hz * ((stop_hz / start_hz) ** progress)
    #                 # 构建备用数据点
    #                 data_point = {
    #                     'frequency': current_freq,
    #                     'X': 0.0,
    #                     'Y': 0.0, 
    #                     'R': 0.0,
    #                     'theta': 0.0,
    #                     'timestamp': time.time(),
    #                     'elapsed_time': time.perf_counter() - start_time
    #                 }
    #                 print(f"警告: 无法从SR830读取数据")
                
    #             self.sweep_data.append(data_point)
                
    #             # 发射数据信号
    #             self.data_acquired.emit(data_point)
    #             self.progress_updated.emit(i + 1, total_samples)
    #             i += 1
    #             # 等待采样间隔
    #             time.sleep(max(0, sample_interval-(time.perf_counter()-o_time)))
                
    #         # 关闭输出
    #         self.wf1947.set_output(False)

    #         # 重置WF1947
    #         self.wf1947.reset()
            
    #         # 发射完成信号
    #         if self.running:
    #             self.sweep_finished.emit()
                
    #     except Exception as e:
    #         self.error_occurred.emit(str(e))
    #     finally:
    #         # 确保关闭输出
    #         try:
    #             self.wf1947.set_output(False)
    #         except:
    #             pass

    def run(self):
        """执行频率扫描（程序控制WF1947）"""
        try:
            self.running = True
            self.sweep_data = []
            
            # 获取扫描参数
            start_hz = self.sweep_params['start_hz']
            stop_hz = self.sweep_params['stop_hz']
            sweep_time_s = self.sweep_params['sweep_time_s']
            spacing = self.sweep_params['spacing']
            sample_interval = 0.5 # 采样间隔固定为0.5s
            
            # 设置WF1947基本参数
            self.wf1947.set_waveform(self.sweep_params['waveform'])
            self.wf1947.set_amplitude(self.sweep_params['amplitude'])
            self.wf1947.set_offset(self.sweep_params['offset'])
            
            # 开启扫描输出
            self.wf1947.set_output(True)
            
            # 计算采样点数
            total_samples = int(sweep_time_s / sample_interval)

            # 计算频率间隔
            frequency_interval = (stop_hz - start_hz) / total_samples
            
            # 在扫描过程中采样数据
            start_time = time.perf_counter()
            for i in range(total_samples):
                
                # 设置频率
                self.wf1947.set_frequency(start_hz + i * frequency_interval)

                # 等待稳定
                time.sleep(sample_interval)
                
                # 从SR830读取数据
                try:
                    frequency_data = self.wf1947.get_frequency()
                    snap_data = self.sr830.getSnap(1, 2, 3, 4)
                    # 构建数据点
                    data_point = {
                        'frequency': frequency_data,
                        'X': snap_data[0],
                        'Y': snap_data[1], 
                        'R': snap_data[2],
                        'theta': snap_data[3],
                        'timestamp': time.time(),
                        'elapsed_time': time.perf_counter() - start_time
                    }
                except Exception as e:
                    # 如果读取失败，使用基于时间进度的估算作为备用
                    progress = (time.perf_counter() - start_time) / sweep_time_s
                    if spacing == 'LINear':
                        current_freq = start_hz + (stop_hz - start_hz) * progress
                    else:  # LOGarithmic
                        current_freq = start_hz * ((stop_hz / start_hz) ** progress)
                    # 构建备用数据点
                    data_point = {
                        'frequency': current_freq,
                        'X': 0.0,
                        'Y': 0.0, 
                        'R': 0.0,
                        'theta': 0.0,
                        'timestamp': time.time(),
                        'elapsed_time': time.perf_counter() - start_time
                    }
                    print(f"警告: 无法从SR830读取数据")
                
                self.sweep_data.append(data_point)
                
                # 发射数据信号
                self.data_acquired.emit(data_point)
                self.progress_updated.emit(i + 1, total_samples)
                
            # 关闭输出
            self.wf1947.set_output(False)

            # 重置WF1947
            self.wf1947.reset()
            
            # 发射完成信号
            if self.running:
                self.sweep_finished.emit()
                
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            # 确保关闭输出
            try:
                self.wf1947.set_output(False)
            except:
                pass
                
    def stop_sweep(self):
        """停止扫描"""
        self.running = False
        
    def get_sweep_data(self):
        """获取扫描数据"""
        return self.sweep_data.copy()


class PyFreSweeper(QWidget):
    """频率扫描面板"""
    
    # 信号定义，用于控制仪器显示面板的启停
    request_stop_display = Signal()  # 请求停止仪器显示更新
    request_start_display = Signal()  # 请求开始仪器显示更新
    
    def __init__(self, instruments_control=None):
        super().__init__()
        self.instruments_control = instruments_control
        
        # 扫描线程
        self.sweep_thread = None
        self.is_sweeping = False
        
        # 扫描数据
        self.sweep_data = []
        
        self.init_ui()
        self.connect_signals()
        
    def init_ui(self):
        """初始化用户界面"""
        # 创建滚动区域
        from PySide6.QtWidgets import QScrollArea
        
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        layout = QVBoxLayout(scroll_widget)
        layout.setSpacing(3)  # 减少间距
        layout.setContentsMargins(3, 3, 3, 3)  # 减少边距
        
        # 创建标题
        title_label = QLabel("频率扫描")
        title_font = QFont()
        title_font.setPointSize(10)  # 减小字体
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 仪器选择组
        self.create_instrument_selection_group(layout)
        
        # WF1947和扫描参数设置组（合并）
        self.create_wf1947_and_sweep_group(layout)
        
        # 数据保存设置组
        self.create_save_settings_group(layout)
        
        # 控制按钮组
        self.create_control_buttons_group(layout)
        
        # 状态显示组
        self.create_status_group(layout)
        
        # 日志显示
        self.create_log_group(layout)
        
        layout.addStretch()
        
        # 设置滚动区域
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)
        
    def create_instrument_selection_group(self, parent_layout):
        """创建仪器选择组"""
        group = QGroupBox("仪器选择")
        group.setStyleSheet("QGroupBox { font-weight: bold; padding-top: 8px; font-size: 10px; }")
        layout = QFormLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(3, 3, 3, 3)
        
        # 信号发生器选择
        self.wf1947_combo = QComboBox()
        self.wf1947_combo.addItem("请先连接WF1947")
        self.wf1947_combo.setMinimumHeight(22)
        self.wf1947_combo.setMaximumWidth(150)
        layout.addRow("WF1947:", self.wf1947_combo)
        
        # 信号接收器选择
        self.sr830_combo = QComboBox()
        self.sr830_combo.addItem("请先连接SR830")
        self.sr830_combo.setMinimumHeight(22)
        self.sr830_combo.setMaximumWidth(150)
        layout.addRow("SR830:", self.sr830_combo)
        
        # 刷新仪器列表按钮
        refresh_button = QPushButton("刷新")
        refresh_button.setMaximumHeight(22)
        refresh_button.setMaximumWidth(60)
        refresh_button.clicked.connect(self.refresh_instruments)
        layout.addRow("", refresh_button)
        
        group.setLayout(layout)
        parent_layout.addWidget(group)
        
    def create_wf1947_and_sweep_group(self, parent_layout):
        """创建WF1947和扫描参数设置组（单列垂直布局）"""
        group = QGroupBox("WF1947 扫描设置")
        group.setStyleSheet("QGroupBox { font-weight: bold; padding-top: 8px; font-size: 10px; }")
        layout = QFormLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(3, 3, 3, 3)
        
        # 基本波形参数标题
        header_label = QLabel("基本参数:")
        header_label.setStyleSheet("font-weight: bold; font-size: 9px; color: #333;")
        layout.addRow("", header_label)
        
        # 波形选择
        self.waveform_combo = QComboBox()
        self.waveform_combo.addItems(["SIN", "SQU", "RAMP", "PULSE"])
        self.waveform_combo.setCurrentText("SIN")
        self.waveform_combo.setMaximumHeight(22)
        self.waveform_combo.setMaximumWidth(100)
        layout.addRow("波形:", self.waveform_combo)
        
        # 幅度设置
        self.amplitude_spinbox = QDoubleSpinBox()
        self.amplitude_spinbox.setRange(0.001, 1.0)
        self.amplitude_spinbox.setValue(0.01)
        self.amplitude_spinbox.setSuffix(" V")
        self.amplitude_spinbox.setDecimals(3)
        self.amplitude_spinbox.setMaximumHeight(22)
        self.amplitude_spinbox.setMaximumWidth(120)
        layout.addRow("幅度:", self.amplitude_spinbox)
        
        # 偏置设置
        self.offset_spinbox = QDoubleSpinBox()
        self.offset_spinbox.setRange(-5.0, 5.0)
        self.offset_spinbox.setValue(0.0)
        self.offset_spinbox.setSuffix(" V")
        self.offset_spinbox.setDecimals(3)
        self.offset_spinbox.setMaximumHeight(22)
        self.offset_spinbox.setMaximumWidth(120)
        layout.addRow("偏置:", self.offset_spinbox)
        
        # 负载设置
        self.load_combo = QComboBox()
        self.load_combo.addItems(["50", "75", "INF"])
        self.load_combo.setCurrentText("INF")
        self.load_combo.setMaximumHeight(22)
        self.load_combo.setMaximumWidth(100)
        layout.addRow("负载:", self.load_combo)
        
        # 扫描参数标题
        sweep_header = QLabel("扫描参数:")
        sweep_header.setStyleSheet("font-weight: bold; font-size: 9px; color: #333;")
        layout.addRow("", sweep_header)
        
        # 起始频率
        self.start_freq_spinbox = QDoubleSpinBox()
        self.start_freq_spinbox.setRange(0.001, 1e6)
        self.start_freq_spinbox.setValue(100.0)
        self.start_freq_spinbox.setSuffix(" Hz")
        self.start_freq_spinbox.setDecimals(3)
        self.start_freq_spinbox.setMaximumHeight(22)
        self.start_freq_spinbox.setMaximumWidth(120)
        layout.addRow("起始频率:", self.start_freq_spinbox)
        
        # 结束频率
        self.stop_freq_spinbox = QDoubleSpinBox()
        self.stop_freq_spinbox.setRange(0.001, 1e6)
        self.stop_freq_spinbox.setValue(10000.0)
        self.stop_freq_spinbox.setSuffix(" Hz")
        self.stop_freq_spinbox.setDecimals(3)
        self.stop_freq_spinbox.setMaximumHeight(22)
        self.stop_freq_spinbox.setMaximumWidth(120)
        layout.addRow("结束频率:", self.stop_freq_spinbox)
        
        # 扫描时间
        self.sweep_time_spinbox = QDoubleSpinBox()
        self.sweep_time_spinbox.setRange(1.0, 3600.0)
        self.sweep_time_spinbox.setValue(10.0)
        self.sweep_time_spinbox.setSuffix(" s")
        self.sweep_time_spinbox.setDecimals(1)
        self.sweep_time_spinbox.setMaximumHeight(22)
        self.sweep_time_spinbox.setMaximumWidth(120)
        layout.addRow("扫描时间:", self.sweep_time_spinbox)
        
        # 频率间距
        self.spacing_combo = QComboBox()
        self.spacing_combo.addItems(["LINear", "LOGarithmic"])
        self.spacing_combo.setCurrentText("LOGarithmic")
        self.spacing_combo.setMaximumHeight(22)
        self.spacing_combo.setMaximumWidth(120)
        layout.addRow("频率间距:", self.spacing_combo)
        
        # 扫描方向
        self.direction_combo = QComboBox()
        self.direction_combo.addItems(["RAMP", "TRIangle"])
        self.direction_combo.setCurrentText("RAMP")
        self.direction_combo.setMaximumHeight(22)
        self.direction_combo.setMaximumWidth(120)
        layout.addRow("扫描方向:", self.direction_combo)
        
        # 数据采样间隔
        self.sample_interval_spinbox = QDoubleSpinBox()
        self.sample_interval_spinbox.setRange(0.1, 10.0)
        self.sample_interval_spinbox.setValue(0.2)
        self.sample_interval_spinbox.setSuffix(" s")
        self.sample_interval_spinbox.setDecimals(2)
        self.sample_interval_spinbox.setMaximumHeight(22)
        self.sample_interval_spinbox.setMaximumWidth(120)
        layout.addRow("采样间隔:", self.sample_interval_spinbox)
        
        group.setLayout(layout)
        parent_layout.addWidget(group)
        
    def create_save_settings_group(self, parent_layout):
        """创建数据保存设置组"""
        group = QGroupBox("数据保存")
        group.setStyleSheet("QGroupBox { font-weight: bold; padding-top: 8px; font-size: 10px; }")
        layout = QFormLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(3, 3, 3, 3)
        
        # 文件名设置
        self.filename_lineedit = QLineEdit()
        self.filename_lineedit.setPlaceholderText("留空将自动生成文件名")
        self.filename_lineedit.setMaximumHeight(22)
        self.filename_lineedit.setMaximumWidth(180)
        layout.addRow("保存文件名:", self.filename_lineedit)
        
        # 自动保存复选框
        self.auto_save_checkbox = QCheckBox("扫描完成后自动保存")
        self.auto_save_checkbox.setChecked(True)
        layout.addRow("", self.auto_save_checkbox)
        
        group.setLayout(layout)
        parent_layout.addWidget(group)
        
    def create_control_buttons_group(self, parent_layout):
        """创建控制按钮组"""
        group = QGroupBox("控制")
        group.setStyleSheet("QGroupBox { font-weight: bold; padding-top: 8px; font-size: 10px; }")
        layout = QHBoxLayout()
        layout.setSpacing(3)
        layout.setContentsMargins(3, 3, 3, 3)
        
        self.start_button = QPushButton("开始扫描")
        self.start_button.setMaximumHeight(25)
        self.start_button.setMaximumWidth(70)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 3px;
                font-weight: bold;
                font-size: 9px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("停止扫描")
        self.stop_button.setEnabled(False)
        self.stop_button.setMaximumHeight(25)
        self.stop_button.setMaximumWidth(70)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 3px;
                font-weight: bold;
                font-size: 9px;
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
        self.save_button.setMaximumHeight(25)
        self.save_button.setMaximumWidth(70)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 3px;
                font-weight: bold;
                font-size: 9px;
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
        group.setStyleSheet("QGroupBox { font-weight: bold; padding-top: 8px; font-size: 10px; }")
        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(3, 3, 3, 3)
        
        # 扫描状态
        status_layout = QHBoxLayout()
        status_label_text = QLabel("状态:")
        status_label_text.setStyleSheet("font-size: 9px;")
        status_layout.addWidget(status_label_text)
        self.status_label = QLabel("待机")
        self.status_label.setStyleSheet("QLabel { color: #666; font-size: 9px; }")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)
        
        # 进度显示
        progress_layout = QVBoxLayout()
        progress_info_layout = QHBoxLayout()
        progress_text = QLabel("进度:")
        progress_text.setStyleSheet("font-size: 9px;")
        progress_info_layout.addWidget(progress_text)
        self.progress_label = QLabel("0/0")
        self.progress_label.setStyleSheet("QLabel { font-family: monospace; font-size: 9px; }")
        progress_info_layout.addWidget(self.progress_label)
        progress_info_layout.addStretch()
        progress_layout.addLayout(progress_info_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumHeight(15)
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        layout.addLayout(progress_layout)
        
        # 当前频率显示
        freq_layout = QHBoxLayout()
        freq_text = QLabel("当前频率:")
        freq_text.setStyleSheet("font-size: 9px;")
        freq_layout.addWidget(freq_text)
        self.current_freq_label = QLabel("-- Hz")
        self.current_freq_label.setStyleSheet("QLabel { font-family: monospace; font-size: 9px; }")
        freq_layout.addWidget(self.current_freq_label)
        freq_layout.addStretch()
        layout.addLayout(freq_layout)
        
        group.setLayout(layout)
        parent_layout.addWidget(group)
        
    def create_log_group(self, parent_layout):
        """创建日志显示组"""
        group = QGroupBox("日志")
        group.setStyleSheet("QGroupBox { font-weight: bold; padding-top: 8px; font-size: 10px; }")
        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(3, 3, 3, 3)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(60)
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                font-family: monospace;
                font-size: 8px;
                background-color: #f5f5f5;
            }
        """)
        layout.addWidget(self.log_text)
        
        # 清除日志按钮
        clear_log_button = QPushButton("清除日志")
        clear_log_button.setMaximumHeight(20)
        clear_log_button.setMaximumWidth(80)
        clear_log_button.clicked.connect(self.clear_log)
        layout.addWidget(clear_log_button)
        
        group.setLayout(layout)
        parent_layout.addWidget(group)
        
    def connect_signals(self):
        """连接信号槽"""
        # 控制按钮
        self.start_button.clicked.connect(self.start_sweep)
        self.stop_button.clicked.connect(self.stop_sweep)
        self.save_button.clicked.connect(self.save_data)
        
    def set_instruments_control(self, instruments_control):
        """设置仪器控制实例"""
        self.instruments_control = instruments_control
        self.refresh_instruments()
        
    def refresh_instruments(self):
        """刷新仪器列表"""
        if not self.instruments_control:
            return
            
        # 清空并重新填充WF1947列表
        self.wf1947_combo.clear()
        wf1947_found = False
        for address, instrument in self.instruments_control.instruments_instance.items():
            if hasattr(instrument, 'type') and instrument.type == "WF1947":
                self.wf1947_combo.addItem(f"WF1947 - {address}", address)
                wf1947_found = True
        
        if not wf1947_found:
            self.wf1947_combo.addItem("未找到WF1947")
            
        # 清空并重新填充SR830列表
        self.sr830_combo.clear()
        sr830_found = False
        for address, instrument in self.instruments_control.instruments_instance.items():
            if hasattr(instrument, 'type') and instrument.type == "SR830":
                self.sr830_combo.addItem(f"SR830 - {address}", address)
                sr830_found = True
                
        if not sr830_found:
            self.sr830_combo.addItem("未找到SR830")
            
    def get_selected_instruments(self):
        """获取选中的仪器"""
        wf1947_address = self.wf1947_combo.currentData()
        sr830_address = self.sr830_combo.currentData()
        
        if not wf1947_address or not sr830_address:
            return None, None
            
        wf1947 = self.instruments_control.instruments_instance.get(wf1947_address)
        sr830 = self.instruments_control.instruments_instance.get(sr830_address)
        
        return wf1947, sr830
        
    def get_sweep_parameters(self):
        """获取扫描参数（严格按照WF1947 setup_frequency_sweep方法）"""
        load_value = self.load_combo.currentText()
        if load_value == "INF":
            load_value = "INF"
        else:
            load_value = int(load_value)
            
        return {
            # WF1947基本参数
            'waveform': self.waveform_combo.currentText(),
            'amplitude': self.amplitude_spinbox.value(),
            'offset': self.offset_spinbox.value(),
            'load': load_value,
            
            # WF1947 setup_frequency_sweep 参数
            'start_hz': self.start_freq_spinbox.value(),
            'stop_hz': self.stop_freq_spinbox.value(),
            'sweep_time_s': self.sweep_time_spinbox.value(),
            'spacing': self.spacing_combo.currentText(),
            'direction': self.direction_combo.currentText(),
            
            # 数据采样参数
            'sample_interval': self.sample_interval_spinbox.value()
        }
        
    def start_sweep(self):
        """开始频率扫描"""
        if not self.instruments_control:
            self.add_log("错误: 未连接仪器控制系统")
            return
            
        # 获取选中的仪器
        wf1947, sr830 = self.get_selected_instruments()
        if not wf1947 or not sr830:
            self.add_log("错误: 请选择有效的WF1947和SR830仪器")
            return
            
        try:
            # 获取扫描参数
            sweep_params = self.get_sweep_parameters()
            
            # 验证参数
            if sweep_params['start_hz'] >= sweep_params['stop_hz']:
                self.add_log("错误: 起始频率必须小于结束频率")
                return
                
            # 创建扫描线程
            self.sweep_thread = FrequencySweepThread(wf1947, sr830, sweep_params)
            
            # 连接信号
            self.sweep_thread.data_acquired.connect(self.on_data_acquired)
            self.sweep_thread.sweep_finished.connect(self.on_sweep_finished)
            self.sweep_thread.error_occurred.connect(self.on_error_occurred)
            self.sweep_thread.progress_updated.connect(self.on_progress_updated)
            
            # 清空之前的数据
            self.sweep_data = []
            
            # 开始扫描
            self.sweep_thread.start()
            
            # 请求停止仪器显示面板更新，避免数据读取冲突
            self.request_stop_display.emit()
            
            # 更新UI状态
            self.is_sweeping = True
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.save_button.setEnabled(False)
            self.status_label.setText("扫描中...")
            self.status_label.setStyleSheet("QLabel { color: #4CAF50; font-weight: bold; }")
            
            # 显示进度条
            self.progress_bar.setVisible(True)
            total_samples = int(sweep_params['sweep_time_s'] / sweep_params['sample_interval'])
            self.progress_bar.setMaximum(total_samples)
            self.progress_bar.setValue(0)
            self.progress_label.setText(f"0/{total_samples}")
            
            self.add_log(f"开始频率扫描: {sweep_params['start_hz']:.3f} Hz → {sweep_params['stop_hz']:.3f} Hz, {sweep_params['sweep_time_s']:.1f}s")
            self.add_log("已暂停仪器显示更新，避免数据读取冲突")
            
        except Exception as e:
            self.add_log(f"启动扫描失败: {e}")
            QMessageBox.critical(self, "错误", f"启动频率扫描失败:\n{e}")
            
    def stop_sweep(self):
        """停止频率扫描"""
        if self.sweep_thread and self.is_sweeping:
            self.sweep_thread.stop_sweep()
            self.add_log("正在停止扫描...")
            
            # 更新UI状态
            self.is_sweeping = False
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.progress_bar.setVisible(False)
            self.status_label.setText("已停止")
            self.status_label.setStyleSheet("QLabel { color: #ff9800; font-weight: bold; }")
            
            # 请求重新开始仪器显示面板更新
            self.request_start_display.emit()
            
            self.add_log("扫描已停止")
            self.add_log("已恢复仪器显示更新")
            
            # 如果有数据，允许保存
            if self.sweep_data:
                self.save_button.setEnabled(True)
            
    def save_data(self):
        """保存扫描数据"""
        if not self.sweep_data:
            self.add_log("没有数据可保存")
            return
            
        try:
            # 生成文件名
            filename = self.filename_lineedit.text().strip()
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"frequency_sweep_{timestamp}"
                
            # 确保保存到history_data文件夹
            save_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'history_data')
            filepath = os.path.join(save_dir, filename)
            
            # 使用统一的数据保存方法
            success, message = DataSort.save_data_to_file(
                self.sweep_data, 
                filepath, 
                "Frequency Sweep Data"
            )
            
            if success:
                self.add_log(f"数据保存成功: {message}")
                QMessageBox.information(self, "成功", message)
                self.save_button.setEnabled(False)
            else:
                self.add_log(f"保存数据失败: {message}")
                QMessageBox.critical(self, "错误", f"保存数据失败:\n{message}")
            
        except Exception as e:
            self.add_log(f"保存数据失败: {e}")
            QMessageBox.critical(self, "错误", f"保存数据失败:\n{e}")
            
    def _auto_save_data(self):
        """自动保存数据（无弹窗）"""
        if not self.sweep_data:
            return False
            
        try:
            # 生成文件名
            filename = self.filename_lineedit.text().strip()
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"frequency_sweep_{timestamp}"
                
            # 确保保存到history_data文件夹
            save_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'history_data')
            filepath = os.path.join(save_dir, filename)
            
            # 使用统一的数据保存方法
            success, message = DataSort.save_data_to_file(
                self.sweep_data, 
                filepath, 
                "Frequency Sweep Data (Auto-saved)"
            )
            
            if success:
                self.add_log(f"数据自动保存成功: {message}")
                return True
            else:
                self.add_log(f"自动保存数据失败: {message}")
                return False
            
        except Exception as e:
            self.add_log(f"自动保存数据失败: {e}")
            return False
            
    def on_data_acquired(self, data_point):
        """接收到新数据"""
        self.sweep_data.append(data_point)
        
        # 更新当前频率显示
        freq = data_point['frequency']
        if freq >= 1000:
            freq_str = f"{freq/1000:.2f} kHz"
        else:
            freq_str = f"{freq:.2f} Hz"
        self.current_freq_label.setText(freq_str)
        
    def on_progress_updated(self, current, total):
        """更新进度"""
        self.progress_bar.setValue(current)
        self.progress_label.setText(f"{current}/{total}")
        
    def on_sweep_finished(self):
        """扫描完成"""
        self.is_sweeping = False
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        self.progress_bar.setVisible(False)
        self.status_label.setText("扫描完成")
        self.status_label.setStyleSheet("QLabel { color: #4CAF50; font-weight: bold; }")
        
        # 请求重新开始仪器显示面板更新
        self.request_start_display.emit()
        
        self.add_log(f"频率扫描完成，共采集 {len(self.sweep_data)} 个数据点")
        self.add_log("已恢复仪器显示更新")
        
        # 自动保存数据
        if self.auto_save_checkbox.isChecked():
            self.add_log("正在自动保存数据...")
            success = self._auto_save_data()
            if not success:
                self.save_button.setEnabled(True)
        else:
            self.save_button.setEnabled(True)
            
    def on_error_occurred(self, error_message):
        """发生错误"""
        self.is_sweeping = False
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        self.status_label.setText("错误")
        self.status_label.setStyleSheet("QLabel { color: #f44336; font-weight: bold; }")
        
        # 请求重新开始仪器显示面板更新
        self.request_start_display.emit()
        
        self.add_log(f"扫描错误: {error_message}")
        self.add_log("已恢复仪器显示更新")
        QMessageBox.critical(self, "扫描错误", f"频率扫描时发生错误:\n{error_message}")
        
        # 如果有数据，允许保存
        if self.sweep_data:
            self.save_button.setEnabled(True)
            
    def add_log(self, message):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
        # 自动滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)
        
    def clear_log(self):
        """清除日志"""
        self.log_text.clear()
        
    def get_data_for_plotting(self):
        """获取用于绘图的数据"""
        if not self.sweep_data:
            return None
            
        frequencies = [point['frequency'] for point in self.sweep_data]
        amplitudes = [point['R'] for point in self.sweep_data]
        phases = [point['theta'] for point in self.sweep_data]
        
        return {
            'frequency': frequencies,
            'amplitude': amplitudes,
            'phase': phases
        }