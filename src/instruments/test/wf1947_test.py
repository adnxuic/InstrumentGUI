#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WF1947仪器读取命令测试脚本
测试以下读取功能：
- get_waveform(): 获取当前波形
- get_frequency(): 获取当前频率
- get_amplitude(): 获取当前幅度
- get_offset(): 获取当前直流偏置
- get_load(): 获取当前负载阻抗
- get_output(): 获取当前输出状态
"""

import sys
import time
import os
# 添加上级目录到路径，以便导入WF1947类
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from wf1947 import WF1947

def test_wf1947_read_commands():
    """测试WF1947的所有读取命令"""
    

    resource_address = 'GPIB0::9::INSTR'  # 请根据实际情况修改
    channel = 1  # 使用通道1
    
    print("=" * 50)
    print("WF1947 读取命令测试")
    print("=" * 50)
    
    try:
        # 初始化WF1947设备
        print(f"正在连接WF1947设备...")
        print(f"地址: {resource_address}")
        print(f"通道: {channel}")
        
        instrument = WF1947(resource_address, channel)
        print("✓ 设备连接成功！\n")
        
        # 等待设备稳定
        time.sleep(1)
        
        print("-" * 30)
        print("开始测试读取命令...")
        print("-" * 30)
        
        # 测试各个读取命令
        test_commands = [
            ("获取波形", "get_waveform"),
            ("获取频率", "get_frequency"), 
            ("获取幅度", "get_amplitude"),
            ("获取直流偏置", "get_offset"),
            ("获取负载阻抗", "get_load"),
            ("获取输出状态", "get_output")
        ]
        
        results = {}
        
        for description, method_name in test_commands:
            try:
                print(f"测试 {description} ({method_name})...")
                method = getattr(instrument, method_name)
                result = method()
                results[method_name] = result
                
                # 格式化输出结果
                if method_name == "get_frequency":
                    print(f"  结果: {result} Hz")
                elif method_name == "get_amplitude":
                    print(f"  结果: {result} V (Vp-p)")
                elif method_name == "get_offset":
                    print(f"  结果: {result} V")
                elif method_name == "get_load":
                    print(f"  结果: {result}")
                else:
                    print(f"  结果: {result}")
                    
                print("  ✓ 成功\n")
                time.sleep(0.5)  # 稍作延时
                
            except Exception as e:
                print(f"  ✗ 失败: {e}\n")
                results[method_name] = f"错误: {e}"
        
        # 汇总测试结果
        print("=" * 50)
        print("测试结果汇总:")
        print("=" * 50)
        
        for description, method_name in test_commands:
            result = results.get(method_name, "未测试")
            status = "✓" if not str(result).startswith("错误") else "✗"
            print(f"{status} {description:12} | {result}")
        
        print("\n" + "=" * 50)
        
        
        # 关闭设备连接
        print("\n正在关闭设备连接...")
        instrument.close()
        print("✓ 设备连接已关闭")
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        print("\n可能的问题:")
        print("1. 检查设备是否正确连接")
        print("2. 检查VISA驱动是否正确安装")
        print("3. 检查设备地址是否正确")
        print("4. 检查设备是否被其他程序占用")


if __name__ == "__main__":
    
    test_wf1947_read_commands()
