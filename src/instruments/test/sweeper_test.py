import sys
import time
import os
# 添加上级目录到路径，以便导入WF1947类
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from wf1947 import WF1947

# --- 使用示例 ---

try:
    # 假设 fg = WF1947(...) 已经成功实例化
    resource_address = 'GPIB0::9::INSTR'
    fg: WF1947 = WF1947(resource_address)

    # 1. 调用新的方法来配置单次扫描的参数
    # fg.setup_frequency_sweep(start_hz=1000, stop_hz=10000, sweep_time_s=20)

    # # 2. 开启输出 (必须在触发前)
    # fg.set_output(True)
    # print("输出已开启，准备触发扫描...")
    # # time.sleep(1) # 短暂等待，确保设置稳定

    # # 3. 在您需要的时候，发送触发信号，开始扫描
    # print("发送触发信号，开始单次扫描...")
    # # fg.trigger()
    # print("单次扫描已启动。仪器将扫描2秒后自动停止。")

    # # 等待扫描完成
    # time.sleep(20)
    # fg.set_output(False)
    # print("扫描完成，输出已关闭。")

    for i in range(10):
        fg.set_frequency(10000+10000*i)
        print(fg.get_frequency())
        time.sleep(0.4)

    fg.reset()

    time.sleep(5)

finally:
    if 'fg' in locals():
        fg.close()