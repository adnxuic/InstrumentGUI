from PySide6.QtWidgets import QFrame, QVBoxLayout, QPushButton, QButtonGroup, QSizePolicy
from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
import os

current_path = os.path.dirname(os.path.abspath(__file__))
qss_path = os.path.join(current_path, "style.qss")

class PyLeftColumn(QFrame):
    # 定义信号
    panel_changed = Signal(str)  # 面板切换信号，参数为面板名称
    panel_collapsed = Signal()   # 面板折叠信号
    
    def __init__(self):
        super().__init__()

        self.setObjectName("left_column")
        with open(qss_path, "r") as f:
            self.setStyleSheet(f.read())
            
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 创建按钮组用于实现单选功能
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(False)  # 允许取消选中
        
        # 仪器面板按钮
        self.instruments_btn = QPushButton("仪器")
        self.instruments_btn.setCheckable(True)
        # 设置大小策略，让按钮可以扩展
        self.instruments_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.instruments_btn.setMinimumHeight(40)
        self.instruments_btn.setMaximumHeight(60)
        self.instruments_btn.setToolTip("切换到仪器管理面板")
        self.instruments_btn.clicked.connect(lambda: self.on_button_clicked("instruments", self.instruments_btn))
        
        # 数据面板按钮  
        self.data_btn = QPushButton("数据")
        self.data_btn.setCheckable(True)
        # 设置大小策略，让按钮可以扩展
        self.data_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.data_btn.setMinimumHeight(40)
        self.data_btn.setMaximumHeight(60)
        self.data_btn.setToolTip("切换到数据管理面板")
        self.data_btn.clicked.connect(lambda: self.on_button_clicked("data", self.data_btn))
        
        # 添加按钮到按钮组
        self.button_group.addButton(self.instruments_btn)
        self.button_group.addButton(self.data_btn)
        
        # 设置按钮样式 - 添加响应式字体大小
        button_style = """
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                color: #333;
                min-width: 50px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border-color: #007acc;
            }
            QPushButton:checked {
                background-color: #007acc;
                color: white;
                border-color: #005fa3;
            }
            QPushButton:pressed {
                background-color: #005fa3;
            }
        """
        
        self.instruments_btn.setStyleSheet(button_style)
        self.data_btn.setStyleSheet(button_style)
        
        # 添加按钮到布局
        layout.addWidget(self.instruments_btn)
        layout.addWidget(self.data_btn)
        layout.addStretch()  # 添加弹性空间推到顶部
        
        # 默认选中仪器面板
        self.instruments_btn.setChecked(True)
        self.current_panel = "instruments"
        
    def resizeEvent(self, event):
        """重写窗口大小变化事件，动态调整按钮字体大小"""
        super().resizeEvent(event)
        
        # 根据窗口宽度动态计算字体大小
        width = self.width()
        
        # 基础字体大小计算：宽度越大，字体越大，但有最小和最大限制
        if width < 80:
            font_size = 10
        elif width < 120:
            font_size = 12
        elif width < 160:
            font_size = 14
        else:
            font_size = 16
            
        # 为按钮设置新字体
        font = QFont()
        font.setPointSize(font_size)
        font.setBold(True)
        
        self.instruments_btn.setFont(font)
        self.data_btn.setFont(font)
        
        # 根据宽度调整按钮文本
        if width < 60:
            self.instruments_btn.setText("仪")
            self.data_btn.setText("数")
        elif width < 80:
            self.instruments_btn.setText("仪器")
            self.data_btn.setText("数据")
        else:
            self.instruments_btn.setText("仪器")
            self.data_btn.setText("数据")
        
    def on_button_clicked(self, panel_name, sender_button):
        """处理按钮点击事件"""
        
        # 如果点击的是当前选中的按钮，则取消选中并折叠面板
        if hasattr(self, 'current_panel') and self.current_panel == panel_name and sender_button.isChecked():
            sender_button.setChecked(False)
            self.current_panel = None
            self.panel_collapsed.emit()
        else:
            # 取消其他按钮的选中状态
            for button in self.button_group.buttons():
                if button != sender_button:
                    button.setChecked(False)
            
            # 如果按钮被选中，显示对应面板
            if sender_button.isChecked():
                self.current_panel = panel_name
                self.panel_changed.emit(panel_name)
            else:
                # 如果按钮被取消选中，折叠面板
                self.current_panel = None
                self.panel_collapsed.emit()