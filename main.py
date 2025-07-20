#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仪器读控一体化GUI应用程序主入口
"""

import sys
import os
from PySide6.QtWidgets import QApplication

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from gui.main_window import MainWindow


def main():
    """主函数"""
    # 创建应用程序实例
    app = QApplication(sys.argv)
    
    # 创建主窗口
    main_window = MainWindow()
    main_window.show()
    
    # 运行应用程序
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
