from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, 
                             QPushButton, QListWidget, QListWidgetItem,
                             QHBoxLayout, QLabel, QMessageBox, QDialog,
                             QComboBox, QLineEdit, QPushButton as QPushBtn)
from PySide6.QtCore import Signal, Qt

import pyvisa


class AddInstrumentDialog(QDialog):
    """添加仪器的自定义对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加仪器")
        self.setFixedSize(650, 280)
        self.init_ui()
        self.refresh_visa_resources()
        
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 主要内容区域
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # 左侧：仪器类型选择
        left_group = QGroupBox("仪器类型")
        left_layout = QVBoxLayout(left_group)
        
        self.instrument_type_combo = QComboBox()
        self.instrument_type_combo.addItems(["SR830", "WF1947", "PPMS"])
        self.instrument_type_combo.setFixedHeight(35)
        left_layout.addWidget(self.instrument_type_combo)
        
        left_group.setFixedWidth(140)
        content_layout.addWidget(left_group)
        
        # 中间：地址输入
        middle_group = QGroupBox("设备地址")
        middle_layout = QVBoxLayout(middle_group)
        
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("输入设备地址或从右侧列表选择")
        self.address_input.setFixedHeight(35)
        middle_layout.addWidget(self.address_input)
        
        middle_group.setFixedWidth(220)
        content_layout.addWidget(middle_group)
        
        # 右侧：可用设备列表
        right_group = QGroupBox("可用设备")
        right_group.setFixedWidth(220)
        right_layout = QVBoxLayout(right_group)
        
        # 刷新按钮和设备列表的布局
        refresh_layout = QHBoxLayout()
        self.refresh_btn = QPushBtn("🔄")
        self.refresh_btn.setFixedSize(30, 30)
        self.refresh_btn.setToolTip("刷新设备列表")
        self.refresh_btn.clicked.connect(self.refresh_visa_resources)
        refresh_layout.addWidget(self.refresh_btn)
        refresh_layout.addStretch()
        
        right_layout.addLayout(refresh_layout)
        
        self.devices_list = QListWidget()
        self.devices_list.setMinimumHeight(120)
        self.devices_list.setMaximumHeight(150)
        self.devices_list.itemClicked.connect(self.on_device_selected)
        right_layout.addWidget(self.devices_list)
        
        content_layout.addWidget(right_group)
        
        layout.addLayout(content_layout)
        
        # 底部按钮
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.cancel_btn = QPushBtn("取消")
        self.cancel_btn.setFixedSize(80, 35)
        self.cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_btn)
        
        self.ok_btn = QPushBtn("确定")
        self.ok_btn.setFixedSize(80, 35)
        self.ok_btn.clicked.connect(self.accept)
        self.ok_btn.setDefault(True)
        buttons_layout.addWidget(self.ok_btn)
        
        layout.addLayout(buttons_layout)
        
        # 设置样式
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QComboBox, QLineEdit {
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 5px;
            }
            QListWidget {
                border: 1px solid #cccccc;
                border-radius: 3px;
                background-color: white;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #eeeeee;
            }
            QListWidget::item:selected {
                background-color: #007acc;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #e6f3ff;
            }
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
    
    def refresh_visa_resources(self):
        """刷新VISA资源列表"""
        self.devices_list.clear()
        try:
            rm = pyvisa.ResourceManager()
            resources = rm.list_resources()
            
            if resources:
                for resource in resources:
                    item = QListWidgetItem(resource)
                    self.devices_list.addItem(item)
            else:
                item = QListWidgetItem("未检测到设备")
                item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
                self.devices_list.addItem(item)
                
        except Exception as e:
            error_item = QListWidgetItem(f"错误: {str(e)}")
            error_item.setFlags(error_item.flags() & ~Qt.ItemIsSelectable)
            self.devices_list.addItem(error_item)
    
    def on_device_selected(self, item):
        """当选择设备时，自动填入地址输入框"""
        if item.flags() & Qt.ItemIsSelectable:
            self.address_input.setText(item.text())
    
    def get_selection(self):
        """获取用户选择的仪器类型和地址"""
        return {
            'type': self.instrument_type_combo.currentText(),
            'address': self.address_input.text().strip()
        }


class PyInstrumentsPanel(QWidget):
    # 定义信号
    instrument_added = Signal(str)  # 当添加仪器时发出信号
    instrument_removed = Signal(str)  # 当移除仪器时发出信号
    
    def __init__(self, instruments_control=None):
        super().__init__()
        self.instruments_control = instruments_control
        self.init_set()
        # 初始化时加载已有仪器
        self.load_existing_instruments()
            

    def init_set(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # 创建分组框
        group_box = QGroupBox("仪器管理")
        group_layout = QVBoxLayout(group_box)
        group_layout.setSpacing(10)
        
        # 添加仪器按钮
        self.add_instrument_btn = QPushButton("+ 添加仪器")
        self.add_instrument_btn.setFixedHeight(35)
        self.add_instrument_btn.clicked.connect(self.add_instrument_dialog)
        group_layout.addWidget(self.add_instrument_btn)
        
        # 已添加仪器列表标签
        list_label = QLabel("已连接仪器:")
        group_layout.addWidget(list_label)
        
        # 仪器列表
        self.instruments_list = QListWidget()
        self.instruments_list.setMinimumHeight(200)

        self.instruments_list.setStyleSheet("""
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
        # 允许右键菜单
        self.instruments_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.instruments_list.customContextMenuRequested.connect(self.show_context_menu)
        group_layout.addWidget(self.instruments_list)

        layout.addWidget(group_box)

    def load_existing_instruments(self):
        """加载已存在的仪器到列表中"""
        if not self.instruments_control:
            return
            
        for instrument_address, instrument_instance in self.instruments_control.instruments_instance.items():
            # 通过配置确定仪器类型
            instrument_type = None
            for inst_type, addresses in self.instruments_control.instruments_config.items():
                if instrument_address in addresses:
                    instrument_type = inst_type
                    break
            
            if instrument_type:
                self.add_instrument_to_list(instrument_type, instrument_address)

    def add_instrument_dialog(self):
        """添加仪器的对话框"""
        if not self.instruments_control:
            QMessageBox.warning(self, "错误", "仪器控制器未初始化")
            return
            
        dialog = AddInstrumentDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            selection = dialog.get_selection()
            instrument_type = selection['type']
            instrument_address = selection['address']
            
            if instrument_address.strip():
                # 使用InstrumentsControl添加仪器
                success, error_msg = self.instruments_control.add_instrument(instrument_type, instrument_address.strip())
                
                if success:
                    self.add_instrument_to_list(instrument_type, instrument_address.strip())
                    self.instrument_added.emit(f"{instrument_type}:{instrument_address.strip()}")
                    QMessageBox.information(self, "成功", f"仪器 {instrument_type} ({instrument_address.strip()}) 添加成功")
                else:
                    QMessageBox.critical(self, "错误", f"添加仪器失败:\n{error_msg}")
    
    def add_instrument_to_list(self, instrument_type, instrument_address):
        """添加仪器到列表"""
        item_text = f"{instrument_address} ({instrument_type})"
        print(f"Debug: 添加仪器 - 类型: '{instrument_type}', 地址: '{instrument_address}', 显示文本: '{item_text}'")
        
        item = QListWidgetItem(item_text)
        # 设置仪器数据，使用Qt.UserRole确保数据正确存储
        item.setData(Qt.UserRole, {"type": instrument_type, "address": instrument_address})
        self.instruments_list.addItem(item)
        
        # 验证数据是否正确存储
        stored_data = item.data(Qt.UserRole)
        print(f"Debug: 存储的数据: {stored_data}, 类型: {type(stored_data)}")
        print(f"Debug: 列表中现在有 {self.instruments_list.count()} 个仪器")
    
    def remove_instrument(self, item):
        """移除仪器"""
        if not item or not self.instruments_control:
            return
            
        data = item.data(Qt.UserRole)
        
        # 检查data的类型，如果不是字典则尝试从文本解析
        if isinstance(data, dict):
            instrument_address = data['address']
            instrument_type = data['type']
        else:
            # 如果data不是字典，从item的文本解析信息
            text = item.text()  # 格式应该是 "address (type)"
            try:
                if " (" in text and text.endswith(")"):
                    instrument_address = text.split(" (")[0]
                    instrument_type = text.split(" (")[1][:-1]
                else:
                    QMessageBox.critical(self, "错误", "无法解析仪器信息")
                    return
            except Exception as e:
                QMessageBox.critical(self, "错误", f"解析仪器信息失败: {str(e)}")
                return
        
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除仪器 '{item.text()}' 吗?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 使用InstrumentsControl移除仪器
            success = self.instruments_control.remove_instrument(instrument_address)
            
            if success:
                row = self.instruments_list.row(item)
                self.instruments_list.takeItem(row)
                self.instrument_removed.emit(f"{instrument_type}:{instrument_address}")
                QMessageBox.information(self, "成功", f"仪器 {instrument_type} ({instrument_address}) 移除成功")
            else:
                QMessageBox.critical(self, "错误", f"移除仪器失败")
    
    def show_context_menu(self, position):
        """显示右键菜单"""
        item = self.instruments_list.itemAt(position)
        if item:
            from PySide6.QtWidgets import QMenu
            menu = QMenu(self)
            
            remove_action = menu.addAction("删除仪器")
            remove_action.triggered.connect(lambda: self.remove_instrument(item))
            
            menu.exec_(self.instruments_list.mapToGlobal(position))
    
    def get_instruments(self):
        """获取所有仪器信息"""
        instruments = []
        for i in range(self.instruments_list.count()):
            item = self.instruments_list.item(i)
            data = item.data(0)
            instruments.append(data)
        return instruments