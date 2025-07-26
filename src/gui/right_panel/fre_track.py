from PySide6.QtWidgets import QWidget, QVBoxLayout, QComboBox, QStackedWidget, QLabel
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
        self.digitalPID = PyDigitalPID(self.instruments_control)
        self.analogPID = PyAnalogPID(self.instruments_control)

    def init_ui(self):
        # 主布局
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
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