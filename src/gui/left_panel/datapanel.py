from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QPushButton, QListWidget, QFileDialog

import os

class PyDataPanel(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # 创建分组框
        group_box = QGroupBox("数据文件")
        group_layout = QVBoxLayout(group_box)
        
        # 导入文件按钮
        self.import_btn = QPushButton("导入文件")
        self.import_btn.setToolTip("选择并导入数据文件（支持 .txt, .csv 格式）")
        self.import_btn.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005fa3;
            }
            QPushButton:pressed {
                background-color: #004080;
            }
        """)
        self.import_btn.clicked.connect(self.import_files_name)
        
        # 文件列表
        self.file_list = QListWidget()
        
        # 设置列表样式
        self.file_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: white;
                alternate-background-color: #f0f0f0;
                min-height: 200px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #007acc;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #e6f3ff;
            }
        """)
        
        # 添加到布局
        group_layout.addWidget(self.import_btn)
        group_layout.addWidget(self.file_list)
        
        layout.addWidget(group_box)
        layout.addStretch()  # 添加弹性空间
        
    def import_files_name(self):
        """显示文件夹中的文件"""
        
        # 弹出文件夹选择对话框
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "选择文件夹",
            "",  # 起始目录为空，使用系统默认
            QFileDialog.ShowDirsOnly
        )
        
        # 如果用户选择了文件夹
        if folder_path:
            # 清空当前列表
            self.file_list.clear()
            
            try:
                # 获取文件夹中的所有文件
                files = os.listdir(folder_path)
                
                # 过滤出文件（排除文件夹）
                file_names = [f for f in files if os.path.isfile(os.path.join(folder_path, f))]
                
                # 添加文件到列表
                for file_name in sorted(file_names):
                    self.file_list.addItem(file_name)
                    
                print(f"已导入 {len(file_names)} 个文件从文件夹: {folder_path}")
                
            except Exception as e:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self,
                    "错误",
                    f"读取文件夹时出错: {str(e)}"
                )
        