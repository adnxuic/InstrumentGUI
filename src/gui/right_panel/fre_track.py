from PySide6.QtWidgets import (QWidget, QVBoxLayout, QComboBox, QStackedWidget, QLabel,
                               QGroupBox, QFormLayout, QPushButton)
from PySide6.QtCore import Qt

from .fretracktype.digitalPID import PyDigitalPID
from .fretracktype.analogPID import PyAnalogPID

class PyFreTrack(QWidget):
    def __init__(self, instruments_control=None):
        super().__init__()
        self.instruments_control = instruments_control
        
        self.init_set()
        self.init_ui()

    def init_set(self):
        # 初始化时创建PID控制器，但不传递仪器实例
        self.digitalPID = PyDigitalPID()
        self.analogPID = PyAnalogPID()
        
        # 选中的仪器实例
        self.selected_wf1947 = None
        self.selected_sr830 = None

    def init_ui(self):
        # 主布局
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 仪器选择组
        self.create_instrument_selection_group(layout)
        
        # PID模式选择标签
        mode_label = QLabel("PID模式选择:")
        mode_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(mode_label)
        
        # PID模式选择框
        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["数字PID", "模拟PID"])
        self.mode_selector.setStyleSheet("""
            QComboBox {
                padding: 5px 10px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                min-height: 20px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #666;
                margin-right: 5px;
            }
        """)
        layout.addWidget(self.mode_selector)
        
        # 堆叠布局窗口
        self.stacked_widget = QStackedWidget()
        
        # 添加PID模式窗口到堆叠布局
        self.stacked_widget.addWidget(self.digitalPID)  # 索引0: 数字PID
        self.stacked_widget.addWidget(self.analogPID)   # 索引1: 模拟PID
        
        layout.addWidget(self.stacked_widget)
        
        # 连接信号槽
        self.mode_selector.currentIndexChanged.connect(self.switch_pid_mode)
        
        # 设置默认选择为数字PID
        self.mode_selector.setCurrentIndex(0)
        self.stacked_widget.setCurrentIndex(0)
        
        self.setLayout(layout)

    def switch_pid_mode(self, index):
        """切换PID模式"""
        self.stacked_widget.setCurrentIndex(index)
        mode_name = "数字PID" if index == 0 else "模拟PID"
        print(f"切换到{mode_name}模式")

    def get_current_pid_widget(self):
        """获取当前选中的PID控件"""
        return self.stacked_widget.currentWidget()
        
    def get_current_pid_mode(self):
        """获取当前PID模式名称"""
        return self.mode_selector.currentText()
        
    def create_instrument_selection_group(self, parent_layout):
        """创建仪器选择组"""
        group = QGroupBox("仪器选择")
        group.setStyleSheet("QGroupBox { font-weight: bold; padding-top: 8px; font-size: 12px; }")
        layout = QFormLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 信号发生器选择
        self.wf1947_combo = QComboBox()
        self.wf1947_combo.addItem("请先连接WF1947")
        self.wf1947_combo.setMinimumHeight(25)
        self.wf1947_combo.currentIndexChanged.connect(self.on_instrument_selected)
        layout.addRow("WF1947:", self.wf1947_combo)
        
        # 锁相放大器选择
        self.sr830_combo = QComboBox()
        self.sr830_combo.addItem("请先连接SR830")
        self.sr830_combo.setMinimumHeight(25)
        self.sr830_combo.currentIndexChanged.connect(self.on_instrument_selected)
        layout.addRow("SR830:", self.sr830_combo)
        
        # 刷新仪器列表按钮
        refresh_button = QPushButton("刷新仪器列表")
        refresh_button.setMaximumHeight(25)
        refresh_button.clicked.connect(self.refresh_instruments)
        refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 5px 10px;
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
        layout.addRow("", refresh_button)
        
        group.setLayout(layout)
        parent_layout.addWidget(group)
        
        # 初始刷新仪器列表
        if self.instruments_control:
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
            
        # 触发仪器选择更新
        self.on_instrument_selected()
            
    def get_selected_instruments(self):
        """获取选中的仪器"""
        wf1947_address = self.wf1947_combo.currentData()
        sr830_address = self.sr830_combo.currentData()
        
        if not wf1947_address or not sr830_address:
            return None, None
            
        wf1947 = self.instruments_control.instruments_instance.get(wf1947_address)
        sr830 = self.instruments_control.instruments_instance.get(sr830_address)
        
        return wf1947, sr830
        
    def on_instrument_selected(self):
        """当仪器被选中时更新PID控制器"""
        if not self.instruments_control:
            return
            
        # 获取选中的仪器
        self.selected_wf1947, self.selected_sr830 = self.get_selected_instruments()
        
        # 直接将选中的仪器传递给PID控制器
        if self.selected_wf1947 and self.selected_sr830:
            # 设置选中的仪器到PID控制器
            self.digitalPID.set_selected_instruments(self.selected_wf1947, self.selected_sr830)
            self.analogPID.set_selected_instruments(self.selected_wf1947, self.selected_sr830)
            
            print(f"频率追踪仪器已选择: WF1947={self.wf1947_combo.currentText()}, SR830={self.sr830_combo.currentText()}")
        else:
            # 清除仪器引用
            self.digitalPID.set_selected_instruments(None, None)
            self.analogPID.set_selected_instruments(None, None)
            
    def set_instruments_control(self, instruments_control):
        """设置仪器控制实例"""
        self.instruments_control = instruments_control
        
        # 刷新仪器列表
        self.refresh_instruments() 