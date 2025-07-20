from PySide6.QtWidgets import QFrame, QVBoxLayout, QPushButton, QButtonGroup, QSizePolicy
from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
import os

current_path = os.path.dirname(os.path.abspath(__file__))
qss_path = os.path.join(current_path, "style.qss")

class PyRightColumn(QFrame):
    # 定义信号
    panel_changed = Signal(str)  # 面板切换信号，参数为面板名称
    panel_collapsed = Signal()   # 面板折叠信号
    
    def __init__(self):
        super().__init__()

        self.setObjectName("right_column")
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
        
        # 仪器数据显示按钮
        self.instrument_data_btn = QPushButton("数据")
        self.instrument_data_btn.setCheckable(True)
        self.instrument_data_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.instrument_data_btn.setMinimumHeight(40)
        self.instrument_data_btn.setMaximumHeight(60)
        self.instrument_data_btn.setToolTip("切换到仪器数据显示面板")
        self.instrument_data_btn.clicked.connect(lambda: self.on_button_clicked("instrument_data", self.instrument_data_btn))
        
        # 数据记录按钮  
        self.data_record_btn = QPushButton("记录")
        self.data_record_btn.setCheckable(True)
        self.data_record_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.data_record_btn.setMinimumHeight(40)
        self.data_record_btn.setMaximumHeight(60)
        self.data_record_btn.setToolTip("切换到数据记录面板")
        self.data_record_btn.clicked.connect(lambda: self.on_button_clicked("data_record", self.data_record_btn))
        
        # 频率追踪按钮
        self.fre_track_btn = QPushButton("追踪")
        self.fre_track_btn.setCheckable(True)
        self.fre_track_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.fre_track_btn.setMinimumHeight(40)
        self.fre_track_btn.setMaximumHeight(60)
        self.fre_track_btn.setToolTip("切换到频率追踪面板")
        self.fre_track_btn.clicked.connect(lambda: self.on_button_clicked("fre_track", self.fre_track_btn))
        
        # 扫频按钮
        self.fre_sweeper_btn = QPushButton("扫频")
        self.fre_sweeper_btn.setCheckable(True)
        self.fre_sweeper_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.fre_sweeper_btn.setMinimumHeight(40)
        self.fre_sweeper_btn.setMaximumHeight(60)
        self.fre_sweeper_btn.setToolTip("切换到扫频面板")
        self.fre_sweeper_btn.clicked.connect(lambda: self.on_button_clicked("fre_sweeper", self.fre_sweeper_btn))
        
        # 添加按钮到按钮组
        self.button_group.addButton(self.instrument_data_btn)
        self.button_group.addButton(self.data_record_btn)
        self.button_group.addButton(self.fre_track_btn)
        self.button_group.addButton(self.fre_sweeper_btn)
        
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
        
        self.instrument_data_btn.setStyleSheet(button_style)
        self.data_record_btn.setStyleSheet(button_style)
        self.fre_track_btn.setStyleSheet(button_style)
        self.fre_sweeper_btn.setStyleSheet(button_style)
        
        # 添加按钮到布局
        layout.addWidget(self.instrument_data_btn)
        layout.addWidget(self.data_record_btn)
        layout.addWidget(self.fre_track_btn)
        layout.addWidget(self.fre_sweeper_btn)
        layout.addStretch()  # 添加弹性空间推到顶部
        
        # 默认选中仪器数据显示面板
        self.instrument_data_btn.setChecked(True)
        self.current_panel = "instrument_data"
        
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
        
        self.instrument_data_btn.setFont(font)
        self.data_record_btn.setFont(font)
        self.fre_track_btn.setFont(font)
        self.fre_sweeper_btn.setFont(font)
        
        # 根据宽度调整按钮文本
        if width < 60:
            self.instrument_data_btn.setText("数")
            self.data_record_btn.setText("录")
            self.fre_track_btn.setText("追")
            self.fre_sweeper_btn.setText("扫")
        elif width < 80:
            self.instrument_data_btn.setText("数据")
            self.data_record_btn.setText("记录")
            self.fre_track_btn.setText("追踪")
            self.fre_sweeper_btn.setText("扫频")
        else:
            self.instrument_data_btn.setText("数据")
            self.data_record_btn.setText("记录")
            self.fre_track_btn.setText("追踪")
            self.fre_sweeper_btn.setText("扫频")
        
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
