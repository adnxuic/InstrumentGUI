from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QSplitter, QMenuBar, QMenu, QStatusBar, QMessageBox,
    QFileDialog, QProgressBar
)
from PySide6.QtGui import QAction, QIcon, QDragEnterEvent, QDropEvent, QCloseEvent
from PySide6.QtCore import Qt

from .left_column import PyLeftColumn
from .right_column import PyRightColumn
from .left_panel.left_panel import PyLeftPanel
from .right_panel.right_panel import PyRightPanel
from .plot_widget.plot_widget import PyFigureWindow

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from instruments.instrumentscontrol import InstrumentsControl


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.current_file_path = None
        
        self.instruments_control = InstrumentsControl()

        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setGeometry(100, 100, 1400, 900)
        
        # 启用拖拽功能
        self.setAcceptDrops(True)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建中央部件
        self.create_central_widget()

        # 创建状态栏
        self.create_status_bar()

    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        # 导出数据动作
        export_stokes_action = QAction("导出参数(&S)", self)
        # export_stokes_action.setShortcut("Ctrl+S")
        # export_stokes_action.setStatusTip("导出斯托克斯参数到CSV文件")
        # export_stokes_action.triggered.connect(self.export_stokes_data)
        file_menu.addAction(export_stokes_action)
        
        export_plot_action = QAction("导出图表(&P)", self)
        # export_plot_action.setShortcut("Ctrl+P")
        # export_plot_action.setStatusTip("导出当前图表为图片")
        # export_plot_action.triggered.connect(self.export_plot)
        file_menu.addAction(export_plot_action)
        
        file_menu.addSeparator()
        
        # 退出动作
        exit_action = QAction("退出(&Q)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("退出应用程序")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        

        # 编辑菜单
        edit_menu = menubar.addMenu("编辑(&E)")
        setting_action = QAction("设置(&A)", self)
        edit_menu.addAction(setting_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        
        about_action = QAction("关于(&A)", self)
        help_menu.addAction(about_action)

    def create_central_widget(self):
        """创建中央部件"""
        # 创建水平分割器
        self.central_splitter = QSplitter()
        self.central_splitter.setOrientation(Qt.Orientation.Horizontal)
        
        # 创建各个组件
        self.left_column = PyLeftColumn()
        self.left_panel = PyLeftPanel(self.instruments_control)
        self.plot_widget = PyFigureWindow()
        self.right_panel = PyRightPanel(self.instruments_control)
        self.right_column = PyRightColumn()
        
        # 连接左侧栏信号到左侧面板
        self.left_column.panel_changed.connect(self.left_panel.switch_to_panel)
        self.left_column.panel_collapsed.connect(self.left_panel.hide_panel)
        
        # 连接右侧栏信号到右侧面板
        self.right_column.panel_changed.connect(self.right_panel.switch_to_panel)
        self.right_column.panel_changed.connect(self.plot_widget.switch_to_canvas)
        self.right_column.panel_collapsed.connect(self.right_panel.hide_panel)
        
        # 添加组件到分割器
        self.central_splitter.addWidget(self.left_column)
        self.central_splitter.addWidget(self.left_panel)
        self.central_splitter.addWidget(self.plot_widget)
        self.central_splitter.addWidget(self.right_panel)
        self.central_splitter.addWidget(self.right_column)
        
        # 设置各个面板的初始大小比例
        self.central_splitter.setSizes([100, 200, 800, 300, 100])
        
        # 设置分割器作为中央部件
        self.setCentralWidget(self.central_splitter)


    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("就绪")
        
        # 添加进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)

    def closeEvent(self, event: QCloseEvent):
        """关闭事件"""
        reply = QMessageBox.question(
            self,
            "退出",
            "确定要退出吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            # 在关闭窗口前清理所有仪器连接
            try:
                if hasattr(self, 'instruments_control'):
                    success = self.instruments_control.close_all_instruments()
                    if success:
                        self.status_bar.showMessage("所有仪器连接已关闭")
                    else:
                        self.status_bar.showMessage("部分仪器连接关闭时出现错误")
            except Exception as e:
                # 即使清理失败也要继续关闭程序，但要记录错误
                print(f"清理仪器连接时发生错误: {e}")
                self.status_bar.showMessage(f"清理时发生错误: {e}")
            
            event.accept()
        else:
            event.ignore()