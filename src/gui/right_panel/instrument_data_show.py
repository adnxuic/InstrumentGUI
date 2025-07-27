from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, 
    QGroupBox, QLabel, QFrame, QGridLayout, QPushButton,
    QDialog, QFormLayout, QLineEdit, QComboBox, QCheckBox,
    QDialogButtonBox, QMessageBox
)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont
from typing import Dict, Optional, Any
from numpy.typing import NDArray

import logging
import time

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from instruments.instrumentscontrol import InstrumentsControl
from instruments.sr830 import SR830
from instruments.ppms import PPMS
from instruments.wf1947 import WF1947

class WF1947SettingsDialog(QDialog):
    """WF1947参数设置对话框"""
    
    def __init__(self, parent=None, instrument: WF1947 = None):
        super().__init__(parent)
        self.instrument = instrument
        self.setWindowTitle("WF1947 参数设置")
        self.setModal(True)
        self.resize(400, 300)
        
        self.init_ui()
        self.load_current_values()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 创建表单布局
        form_layout = QFormLayout()
        
        # 波形选择
        self.waveform_combo = QComboBox()
        self.waveform_combo.addItems(["SIN", "SQU", "RAMP", "PULSE", "NOISE", "DC", "USER"])
        form_layout.addRow("波形:", self.waveform_combo)
        
        # 频率输入
        self.frequency_edit = QLineEdit()
        self.frequency_edit.setPlaceholderText("输入频率 (Hz)")
        form_layout.addRow("频率 (Hz):", self.frequency_edit)
        
        # 幅值输入
        self.amplitude_edit = QLineEdit()
        self.amplitude_edit.setPlaceholderText("输入幅值 (Vpp)")
        form_layout.addRow("幅值 (Vpp):", self.amplitude_edit)
        
        # 直流偏置输入
        self.offset_edit = QLineEdit()
        self.offset_edit.setPlaceholderText("输入直流偏置 (V)")
        form_layout.addRow("直流偏置 (V):", self.offset_edit)
        
        # 负载阻抗输入
        self.load_edit = QLineEdit()
        self.load_edit.setPlaceholderText("输入负载阻抗 (Ohm) 或 INF")
        form_layout.addRow("负载阻抗:", self.load_edit)
        
        # 输出状态
        self.output_checkbox = QCheckBox("输出开启")
        form_layout.addRow("输出状态:", self.output_checkbox)
        
        layout.addLayout(form_layout)
        
        # 按钮组
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept_settings)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def load_current_values(self):
        """加载当前仪器的设置值"""
        if not self.instrument:
            return
            
        try:
            # 获取当前值并填入表单
            current_waveform = self.instrument.get_waveform()
            waveform_index = self.waveform_combo.findText(current_waveform)
            if waveform_index >= 0:
                self.waveform_combo.setCurrentIndex(waveform_index)
                
            self.frequency_edit.setText(str(self.instrument.get_frequency()))
            self.amplitude_edit.setText(str(self.instrument.get_amplitude()))
            self.offset_edit.setText(str(self.instrument.get_offset()))
            self.load_edit.setText(str(self.instrument.get_load()))
            
            output_state = self.instrument.get_output()
            self.output_checkbox.setChecked(output_state == "ON")
            
        except Exception as e:
            QMessageBox.warning(self, "警告", f"读取当前设置失败: {e}")
            
    def accept_settings(self):
        """应用设置"""
        if not self.instrument:
            QMessageBox.warning(self, "错误", "没有连接的仪器")
            return
            
        try:
            # 设置波形
            waveform = self.waveform_combo.currentText()
            self.instrument.set_waveform(waveform)
            
            # 设置频率
            frequency = float(self.frequency_edit.text())
            self.instrument.set_frequency(frequency)
            
            # 设置幅值
            amplitude = float(self.amplitude_edit.text())
            self.instrument.set_amplitude(amplitude)
            
            # 设置直流偏置
            offset = float(self.offset_edit.text())
            self.instrument.set_offset(offset)
            
            # 设置负载阻抗
            load_text = self.load_edit.text().strip()
            if load_text.upper() == "INF":
                self.instrument.set_load("INF")
            else:
                load_value = int(float(load_text))  # 允许浮点数输入但转为整数
                self.instrument.set_load(load_value)
            
            # 设置输出状态
            output_state = self.output_checkbox.isChecked()
            self.instrument.set_output(output_state)
            
            QMessageBox.information(self, "成功", "参数设置成功！")
            self.accept()
            
        except ValueError as e:
            QMessageBox.warning(self, "输入错误", f"请检查输入的数值格式: {e}")
        except Exception as e:
            QMessageBox.critical(self, "设置失败", f"设置参数时发生错误: {e}")

class PyInstrumentDataShow(QWidget):
    def __init__(self, instruments_control: InstrumentsControl) -> None:
        super().__init__()
        
        self.instruments_control: InstrumentsControl = instruments_control
        self.instrument_groups: Dict[str, QGroupBox] = {}  # 存储仪器组件 {instrument_address: group_widget}
        self.data_labels: Dict[str, Dict[str, QLabel]] = {}  # 存储数据标签 {instrument_address: {data_name: label}}
        
        # 数据源控制
        self.use_external_data = False  # 是否使用外部数据源
        self.external_data = {}  # 外部数据缓存
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
        
        self.init_ui()
        self.setup_timer()
        
    def init_ui(self) -> None:
        """初始化UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)
        
        # 标题
        title_label = QLabel("仪器数据显示")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 数据源状态指示器
        self.data_source_label = QLabel("数据源: 直接读取")
        self.data_source_label.setStyleSheet("""
            QLabel {
                background-color: #e8f5e8;
                border: 1px solid #4caf50;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 10px;
                font-weight: bold;
                color: #2e7d32;
            }
        """)
        self.data_source_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.data_source_label)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameStyle(QFrame.Shape.NoFrame)
        
        # 滚动区域内容widget
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(5, 5, 5, 5)
        self.scroll_layout.setSpacing(10)
        
        # 添加stretch使组件向上对齐
        self.scroll_layout.addStretch()
        
        scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(scroll_area)
        
    def setup_timer(self) -> None:
        """设置定时器进行数据更新"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_all_data)
        self.update_timer.start(1000)  # 每1秒更新一次
        
    def set_instruments_control(self, instruments_control: InstrumentsControl) -> None:
        """设置仪器控制实例"""
        self.instruments_control = instruments_control
        self.refresh_instruments()
        
    def set_external_data_source(self, use_external: bool) -> None:
        """设置是否使用外部数据源（如数据记录线程）"""
        self.use_external_data = use_external
        if use_external:
            self.logger.info("切换到外部数据源模式")
            self.data_source_label.setText("数据源: 外部数据")
            self.data_source_label.setStyleSheet("""
                QLabel {
                    background-color: #ffeaea;
                    border: 1px solid #f44336;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 10px;
                    font-weight: bold;
                    color: #c62828;
                }
            """)
        else:
            self.logger.info("切换到直接数据读取模式")
            self.data_source_label.setText("数据源: 直接读取")
            self.data_source_label.setStyleSheet("""
                QLabel {
                    background-color: #e8f5e8;
                    border: 1px solid #4caf50;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 10px;
                    font-weight: bold;
                    color: #2e7d32;
                }
            """)
            
    def update_from_external_data(self, data_point: Dict) -> None:
        """从外部数据源更新数据（如DataRecordThread）"""
        if not self.use_external_data:
            return
            
        self.external_data = data_point
        self._update_display_from_external_data()
        
    def _update_display_from_external_data(self) -> None:
        """使用外部数据更新显示"""
        try:
            # 更新SR830数据
            sr830_data = self.external_data.get('SR830', {})
            for key, value in sr830_data.items():
                # key格式: "address_parameter" (如 "GPIB0::8_X")
                if '_' in key:
                    address_param = key.rsplit('_', 1)
                    if len(address_param) == 2:
                        address, param = address_param
                        if address in self.data_labels and param in self.data_labels[address]:
                            if param in ['X', 'Y', 'R']:
                                self.data_labels[address][param].setText(f"{value:.6f}")
                            elif param == 'theta':
                                self.data_labels[address][param].setText(f"{value:.3f}")
                            elif param == 'frequency':
                                self.data_labels[address][param].setText(f"{value:.3f}")
                            else:
                                self.data_labels[address][param].setText(str(value))
                            
                            # 恢复正常样式（清除错误状态）
                            self._restore_label_style(self.data_labels[address][param], param)
            
            # 更新PPMS数据
            ppms_data = self.external_data.get('PPMS', {})
            for key, value in ppms_data.items():
                # key格式: "address_parameter" (如 "127.0.0.1_temperature")
                if '_' in key:
                    address_param = key.rsplit('_', 1)
                    if len(address_param) == 2:
                        address, param = address_param
                        if address in self.data_labels and param in self.data_labels[address]:
                            if param in ['temperature', 'field']:
                                self.data_labels[address][param].setText(f"{value:.5f}")
                            else:
                                self.data_labels[address][param].setText(str(value))
                                
                            # 恢复正常样式（清除错误状态）
                            self._restore_label_style(self.data_labels[address][param], param)
                            
        except Exception as e:
            self.logger.error(f"从外部数据更新显示失败: {e}")
            
    def _restore_label_style(self, label: QLabel, param: str) -> None:
        """恢复标签的正常样式"""
        if param == "reference":
            # 参考源标签的样式需要根据值来设置，这里设置默认样式
            label.setStyleSheet("""
                QLabel {
                    background-color: #f0f8f0;
                    border: 1px solid #d0d0d0;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-family: 'Courier New', monospace;
                    min-width: 80px;
                    color: black;
                }
            """)
        elif param == "output":
            # 输出状态标签的样式需要根据值来设置，这里设置默认样式
            label.setStyleSheet("""
                QLabel {
                    background-color: #f0f8f0;
                    border: 1px solid #d0d0d0;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-family: 'Courier New', monospace;
                    min-width: 80px;
                    color: black;
                }
            """)
        else:
            # 其他标签使用默认样式
            label.setStyleSheet("""
                QLabel {
                    background-color: #f0f8f0;
                    border: 1px solid #d0d0d0;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-family: 'Courier New', monospace;
                    min-width: 80px;
                    color: black;
                }
            """)
            
    def refresh_instruments(self) -> None:
        """刷新仪器列表，创建或移除仪器组"""
        if not self.instruments_control:
            return
            
        # 获取当前连接的仪器
        current_instruments = self.instruments_control.instruments_instance
        
        # 移除不再存在的仪器组
        for address in list(self.instrument_groups.keys()):
            if address not in current_instruments:
                self.remove_instrument_group(address)
                
        # 为新仪器创建组
        for address, instrument in current_instruments.items():
            if address not in self.instrument_groups:
                self.create_instrument_group(address, instrument)
                
    def create_instrument_group(self, address: str, instrument: Any) -> None:
        """为仪器创建显示组"""
        instrument_type = getattr(instrument, 'type', 'Unknown')
        
        # 创建组框
        group_box = QGroupBox(f"{instrument_type} - {address}")
        group_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #8fbc8f;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #2f4f2f;
            }
        """)
        
        # 创建数据布局
        data_layout = QGridLayout(group_box)
        data_layout.setContentsMargins(10, 15, 10, 10)
        data_layout.setSpacing(8)
        
        # 根据仪器类型创建不同的数据标签
        if instrument_type == "SR830":
            self.create_sr830_labels(address, data_layout)
        elif instrument_type == "PPMS":
            self.create_ppms_labels(address, data_layout)
        elif instrument_type == "WF1947":
            self.create_wf1947_labels(address, data_layout)
        else:
            # 其他仪器类型的默认显示
            label = QLabel("暂不支持该仪器的数据显示")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            data_layout.addWidget(label, 0, 0, 1, 2)
            
        # 将组框添加到滚动布局中（在stretch之前）
        insert_index = self.scroll_layout.count() - 1  # stretch之前
        self.scroll_layout.insertWidget(insert_index, group_box)
        
        # 保存组件引用
        self.instrument_groups[address] = group_box
        
    def create_sr830_labels(self, address: str, layout: QGridLayout) -> None:
        """为SR830创建数据标签"""
        self.data_labels[address] = {}
        
        # 创建数据标签
        data_items = [
            ("X", "X (V):", "0.000"),
            ("Y", "Y (V):", "0.000"),
            ("R", "R (V):", "0.000"),
            ("theta", "θ (°):", "0.000"),
            ("frequency", "频率 (Hz):", "0.000"),
            ("reference", "参考源:", "Internal")
        ]
        
        for i, (key, label_text, default_value) in enumerate(data_items):
            # 参数名标签
            param_label = QLabel(label_text)
            param_label.setStyleSheet("font-weight: bold; color: #444;")
            
            # 数值标签
            value_label = QLabel(default_value)
            value_label.setStyleSheet("""
                QLabel {
                    background-color: #f0f8f0;
                    border: 1px solid #d0d0d0;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-family: 'Courier New', monospace;
                    min-width: 80px;
                }
            """)
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            layout.addWidget(param_label, i, 0)
            layout.addWidget(value_label, i, 1)
            
            self.data_labels[address][key] = value_label
            
    def create_ppms_labels(self, address: str, layout: QGridLayout) -> None:
        """为PPMS创建数据标签"""
        self.data_labels[address] = {}
        
        # 创建数据标签
        data_items = [
            ("temperature", "温度 (K):", "0.000"),
            ("field", "磁场 (Oe):", "0.000")
        ]
        
        for i, (key, label_text, default_value) in enumerate(data_items):
            # 参数名标签
            param_label = QLabel(label_text)
            param_label.setStyleSheet("font-weight: bold; color: #444;")
            
            # 数值标签
            value_label = QLabel(default_value)
            value_label.setStyleSheet("""
                QLabel {
                    background-color: #f0f8f0;
                    border: 1px solid #d0d0d0;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-family: 'Courier New', monospace;
                    min-width: 80px;
                }
            """)
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            layout.addWidget(param_label, i, 0)
            layout.addWidget(value_label, i, 1)
            
            self.data_labels[address][key] = value_label
            
    def create_wf1947_labels(self, address: str, layout: QGridLayout) -> None:
        """为WF1947创建数据标签"""
        self.data_labels[address] = {}
        
        # 创建数据标签
        data_items = [
            ("waveform", "波形:", "SIN"),
            ("frequency", "频率 (Hz):", "0.000"),
            ("amplitude", "幅值 (Vpp):", "0.000"),
            ("offset", "直流偏置 (V):", "0.000"),
            ("load", "负载阻抗:", "50 OHM"),
            ("output", "输出状态:", "OFF")
        ]
        
        for i, (key, label_text, default_value) in enumerate(data_items):
            # 参数名标签
            param_label = QLabel(label_text)
            param_label.setStyleSheet("font-weight: bold; color: #444;")
            
            # 数值标签
            value_label = QLabel(default_value)
            value_label.setStyleSheet("""
                QLabel {
                    background-color: #f0f8f0;
                    border: 1px solid #d0d0d0;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-family: 'Courier New', monospace;
                    min-width: 80px;
                }
            """)
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            layout.addWidget(param_label, i, 0)
            layout.addWidget(value_label, i, 1)
            
            self.data_labels[address][key] = value_label
            
        # 创建按钮容器
        button_layout = QHBoxLayout()
        
        # 添加设置按钮
        settings_button = QPushButton("⚙️ 参数设置")
        settings_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
                min-height: 24px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        
        # 添加重置按钮
        reset_button = QPushButton("🔄 重置")
        reset_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
                min-height: 24px;
            }
            QPushButton:hover {
                background-color: #f57c00;
            }
            QPushButton:pressed {
                background-color: #e65100;
            }
        """)
        
        # 将按钮连接到相应方法
        settings_button.clicked.connect(lambda: self.open_wf1947_settings(address))
        reset_button.clicked.connect(lambda: self.reset_wf1947(address))
        
        # 将按钮添加到水平布局
        button_layout.addWidget(settings_button)
        button_layout.addWidget(reset_button)
        
        # 创建按钮容器widget并设置布局
        button_widget = QWidget()
        button_widget.setLayout(button_layout)
        
        # 将按钮容器跨两列显示
        layout.addWidget(button_widget, len(data_items), 0, 1, 2)
        
    def open_wf1947_settings(self, address: str) -> None:
        """打开WF1947设置对话框"""
        if not self.instruments_control:
            return
            
        # 获取对应的WF1947仪器实例
        instrument = self.instruments_control.instruments_instance.get(address)
        if not instrument or getattr(instrument, 'type', None) != 'WF1947':
            QMessageBox.warning(self, "错误", "找不到对应的WF1947仪器")
            return
            
        # 创建并显示设置对话框
        dialog = WF1947SettingsDialog(self, instrument)
        dialog.exec()
        
    def reset_wf1947(self, address: str) -> None:
        """重置WF1947仪器到默认状态"""
        if not self.instruments_control:
            return
            
        # 获取对应的WF1947仪器实例
        instrument: WF1947 = self.instruments_control.instruments_instance.get(address)
        if not instrument or getattr(instrument, 'type', None) != 'WF1947':
            QMessageBox.warning(self, "错误", "找不到对应的WF1947仪器")
            return
            
        # 确认重置操作
        reply = QMessageBox.question(
            self, 
            "确认重置", 
            f"确定要重置 WF1947 ({address}) 到默认状态吗？\n\n"
            "重置后将恢复到初始设置：\n"
            "• 波形：正弦波 (SIN)\n"
            "• 频率：1kHz\n"
            "• 幅值：100mV (0.1V)\n"
            "• 直流偏置：0V\n"
            "• 输出：关闭",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 执行重置操作
                self.logger.info(f"开始重置WF1947仪器: {address}")
                instrument.reset()  # 发送*RST命令
                
                QMessageBox.information(self, "成功", f"WF1947 ({address}) 已成功重置到默认状态！")
                self.logger.info(f"WF1947仪器重置完成: {address}")
                
            except Exception as e:
                error_msg = f"重置WF1947仪器失败: {e}"
                self.logger.error(f"{error_msg} (地址: {address})")
                QMessageBox.critical(self, "重置失败", error_msg)
            
    def remove_instrument_group(self, address: str) -> None:
        """移除仪器组"""
        if address in self.instrument_groups:
            group_box = self.instrument_groups[address]
            self.scroll_layout.removeWidget(group_box)
            group_box.deleteLater()
            
            del self.instrument_groups[address]
            if address in self.data_labels:
                del self.data_labels[address]
                
    def update_all_data(self) -> None:
        """更新所有仪器的数据"""
        if not self.instruments_control:
            return
            
        # 如果正在使用外部数据源，不进行直接数据读取
        if self.use_external_data:
            # 先检查是否有新的仪器需要添加
            self.refresh_instruments()
            return
            
        # 先检查是否有新的仪器需要添加
        self.refresh_instruments()
        
        # 更新每个仪器的数据（仅在非外部数据源模式下）
        for address, instrument in self.instruments_control.instruments_instance.items():
            if address in self.data_labels:
                self.update_instrument_data(address, instrument)
                
    def update_instrument_data(self, address: str, instrument: Any) -> None:
        """更新单个仪器的数据"""
        try:
            instrument_type = getattr(instrument, 'type', 'Unknown')
            
            if instrument_type == "SR830":
                self.update_sr830_data(address, instrument)
            elif instrument_type == "PPMS":
                self.update_ppms_data(address, instrument)
            elif instrument_type == "WF1947":
                self.update_wf1947_data(address, instrument)
                
        except Exception as e:
            self.logger.error(f"更新仪器数据失败 {address}: {e}")
            # 显示错误状态
            for label in self.data_labels.get(address, {}).values():
                label.setText("Error")
                label.setStyleSheet(label.styleSheet() + "color: red;")
                
    def update_sr830_data(self, address: str, instrument: SR830) -> None:
        """更新SR830数据"""
        try:
            # 获取X, Y, R, theta和frequency数据
            xyrthfreq_data: NDArray = instrument.getSnap(1, 2, 3, 4, 9)  # 返回[X, Y, R, theta, frequency]
            
            # 参考源数据
            reference_source = instrument.getFreSou()
            
            # 更新标签
            labels = self.data_labels[address]
            labels["X"].setText(f"{xyrthfreq_data[0]:.6f}")
            labels["Y"].setText(f"{xyrthfreq_data[1]:.6f}")
            labels["R"].setText(f"{xyrthfreq_data[2]:.6f}")
            labels["theta"].setText(f"{xyrthfreq_data[3]:.3f}")
            labels["frequency"].setText(f"{xyrthfreq_data[4]:.3f}")
            labels["reference"].setText(str(reference_source))
            
            # 恢复正常样式（清除错误状态）
            for key, label in labels.items():
                if key == "reference":
                    # 参考源标签使用特殊样式
                    if reference_source == "Internal":
                        label.setStyleSheet("""
                            QLabel {
                                background-color: #e8f5e8;
                                border: 1px solid #4caf50;
                                border-radius: 4px;
                                padding: 4px 8px;
                                font-family: 'Courier New', monospace;
                                min-width: 80px;
                                color: #2e7d32;
                                font-weight: bold;
                            }
                        """)
                    else:
                        label.setStyleSheet("""
                            QLabel {
                                background-color: #e8f4f8;
                                border: 1px solid #2196f3;
                                border-radius: 4px;
                                padding: 4px 8px;
                                font-family: 'Courier New', monospace;
                                min-width: 80px;
                                color: #1976d2;
                                font-weight: bold;
                            }
                        """)
                else:
                    # 其他标签使用默认样式
                    label.setStyleSheet("""
                        QLabel {
                            background-color: #f0f8f0;
                            border: 1px solid #d0d0d0;
                            border-radius: 4px;
                            padding: 4px 8px;
                            font-family: 'Courier New', monospace;
                            min-width: 80px;
                            color: black;
                        }
                    """)
                
        except Exception as e:
            self.logger.error(f"读取SR830数据失败 {address}: {e}")
            raise
            
    def update_ppms_data(self, address: str, instrument: PPMS) -> None:
        """更新PPMS数据"""
        try:
            # 获取温度和磁场数据
            T, sT, F, sF = instrument.get_temperature_field()
            
            # 更新标签
            labels = self.data_labels[address]
            labels["temperature"].setText(f"{T:.5f}")
            labels["field"].setText(f"{F:.5f}")
            
            # 恢复正常样式（清除错误状态）
            for label in labels.values():
                label.setStyleSheet("""
                    QLabel {
                        background-color: #f0f8f0;
                        border: 1px solid #d0d0d0;
                        border-radius: 4px;
                        padding: 4px 8px;
                        font-family: 'Courier New', monospace;
                        min-width: 80px;
                        color: black;
                    }
                """)
                
        except Exception as e:
            self.logger.error(f"读取PPMS数据失败 {address}: {e}")
            raise
            
    def update_wf1947_data(self, address: str, instrument: WF1947) -> None:
        """更新WF1947数据"""
        try:
            # 获取WF1947各项数据
            waveform = instrument.get_waveform()
            frequency = instrument.get_frequency()
            amplitude = instrument.get_amplitude() 
            offset = instrument.get_offset()
            load = instrument.get_load()
            output = instrument.get_output()
            
            # 更新标签
            labels = self.data_labels[address]
            labels["waveform"].setText(str(waveform))
            labels["frequency"].setText(f"{frequency:.3f}")
            labels["amplitude"].setText(f"{amplitude:.6f}")
            labels["offset"].setText(f"{offset:.6f}")
            labels["load"].setText(str(load))
            labels["output"].setText(str(output))
            
            # 恢复正常样式（清除错误状态）
            for key, label in labels.items():
                if key == "output":
                    # 输出状态使用特殊颜色
                    if output == "ON":
                        label.setStyleSheet("""
                            QLabel {
                                background-color: #e8f5e8;
                                border: 1px solid #4caf50;
                                border-radius: 4px;
                                padding: 4px 8px;
                                font-family: 'Courier New', monospace;
                                min-width: 80px;
                                color: #2e7d32;
                                font-weight: bold;
                            }
                        """)
                    else:
                        label.setStyleSheet("""
                            QLabel {
                                background-color: #ffeaea;
                                border: 1px solid #f44336;
                                border-radius: 4px;
                                padding: 4px 8px;
                                font-family: 'Courier New', monospace;
                                min-width: 80px;
                                color: #c62828;
                                font-weight: bold;
                            }
                        """)
                else:
                    # 其他标签使用默认样式
                    label.setStyleSheet("""
                        QLabel {
                            background-color: #f0f8f0;
                            border: 1px solid #d0d0d0;
                            border-radius: 4px;
                            padding: 4px 8px;
                            font-family: 'Courier New', monospace;
                            min-width: 80px;
                            color: black;
                        }
                    """)
                
        except Exception as e:
            self.logger.error(f"读取WF1947数据失败 {address}: {e}")
            raise