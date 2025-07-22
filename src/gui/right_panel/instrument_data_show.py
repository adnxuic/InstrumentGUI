from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, 
    QGroupBox, QLabel, QFrame, QGridLayout
)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont
from typing import Dict, Optional, Any
from numpy.typing import NDArray

import logging

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from instruments.instrumentscontrol import InstrumentsControl
from instruments.sr830 import SR830
from instruments.ppms import PPMS
from instruments.wf1947 import WF1947

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