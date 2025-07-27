import time
import threading
from typing import Optional, Callable
from PySide6.QtCore import QThread, Signal


import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from instruments.sr830 import SR830
from instruments.wf1947 import WF1947

class DigitalPID:
    """
    数字PID控制器类
    用于共振频率追踪控制
    """
    
    def __init__(self, kp: float = 1.0, ki: float = 0.1, kd: float = 0.01, 
                 setpoint: float = 0.0, sample_time: float = 0.1):
        """
        初始化PID控制器
        
        Args:
            kp: 比例系数
            ki: 积分系数  
            kd: 微分系数
            setpoint: 目标值（目标相位，单位：度）
            sample_time: 采样时间间隔（秒）
        """
        # PID参数
        self.kp = kp
        self.ki = ki
        self.kd = kd
        
        # 控制目标
        self.setpoint = setpoint
        self.sample_time = sample_time
        
        # PID内部状态
        self.last_error = 0.0
        self.integral = 0.0
        self.last_time = None
        
        # 输出限制
        self.output_min = None
        self.output_max = None
        
        # 积分限制（防止积分饱和）
        self.integral_min = None
        self.integral_max = None
        
        # 重置标志
        self.reset_flag = False
        
    def set_pid_params(self, kp: float, ki: float, kd: float):
        """设置PID参数"""
        self.kp = kp
        self.ki = ki
        self.kd = kd
        
    def set_setpoint(self, setpoint: float):
        """设置目标值"""
        self.setpoint = setpoint
        
    def set_sample_time(self, sample_time: float):
        """设置采样时间"""
        self.sample_time = sample_time
        
    def set_output_limits(self, min_val: Optional[float], max_val: Optional[float]):
        """设置输出限制"""
        self.output_min = min_val
        self.output_max = max_val
        
    def set_integral_limits(self, min_val: Optional[float], max_val: Optional[float]):
        """设置积分限制，防止积分饱和"""
        self.integral_min = min_val
        self.integral_max = max_val
        
    def reset(self):
        """重置PID控制器状态"""
        self.last_error = 0.0
        self.integral = 0.0
        self.last_time = None
        self.reset_flag = True
        
    def compute(self, measured_value: float, current_time: Optional[float] = None) -> float:
        """
        计算PID输出
        
        Args:
            measured_value: 当前测量值（当前相位，单位：度）
            current_time: 当前时间（秒），如果为None则使用系统时间
            
        Returns:
            float: PID控制输出（频率调整量，单位：Hz）
        """
        if current_time is None:
            current_time = time.time()
            
        # 首次运行或重置后的初始化
        if self.last_time is None or self.reset_flag:
            self.last_time = current_time
            self.last_error = 0.0
            self.integral = 0.0
            self.reset_flag = False
            return 0.0
            
        # 计算时间差
        dt = current_time - self.last_time
        
        # 如果时间间隔太小，跳过此次计算
        if dt < self.sample_time:
            return 0.0
            
        # 计算误差（目标相位 - 当前相位）
        error = self.setpoint - measured_value
        
        # 处理相位角度的周期性（-180°到180°）
        while error > 180:
            error -= 360
        while error < -180:
            error += 360
            
        # 比例项
        proportional = self.kp * error
        
        # 积分项
        self.integral += error * dt
        
        # 积分限制（防止积分饱和）
        if self.integral_min is not None and self.integral < self.integral_min:
            self.integral = self.integral_min
        if self.integral_max is not None and self.integral > self.integral_max:
            self.integral = self.integral_max
            
        integral_term = self.ki * self.integral
        
        # 微分项
        derivative = (error - self.last_error) / dt if dt > 0 else 0.0
        derivative_term = self.kd * derivative
        
        # PID输出
        output = proportional + integral_term + derivative_term
        
        # 输出限制
        if self.output_min is not None and output < self.output_min:
            output = self.output_min
        if self.output_max is not None and output > self.output_max:
            output = self.output_max
            
        # 更新状态
        self.last_error = error
        self.last_time = current_time
        
        return output
        
    def get_pid_terms(self, measured_value: float, current_time: Optional[float] = None) -> dict:
        """
        获取PID各项的详细信息（用于调试和监控）
        
        Returns:
            dict: 包含error, proportional, integral, derivative, output等信息
        """
        if current_time is None:
            current_time = time.time()
            
        if self.last_time is None:
            return {
                'error': 0.0,
                'proportional': 0.0, 
                'integral': 0.0,
                'derivative': 0.0,
                'output': 0.0
            }
            
        # 计算误差
        error = self.setpoint - measured_value
        while error > 180:
            error -= 360
        while error < -180:
            error += 360
            
        # 各项计算
        proportional = self.kp * error
        integral_term = self.ki * self.integral
        
        dt = current_time - self.last_time
        derivative = (error - self.last_error) / dt if dt > 0 else 0.0
        derivative_term = self.kd * derivative
        
        output = proportional + integral_term + derivative_term
        
        return {
            'error': error,
            'proportional': proportional,
            'integral': integral_term, 
            'derivative': derivative_term,
            'output': output,
            'setpoint': self.setpoint,
            'measured_value': measured_value
        }


class FrequencyTrackingThread(QThread):
    """频率追踪线程，使用数字PID控制WF1947频率"""
    
    # 信号定义
    data_updated = Signal(dict)  # 数据更新信号
    tracking_finished = Signal()  # 追踪完成信号
    error_occurred = Signal(str)  # 错误信号
    status_updated = Signal(str)  # 状态更新信号
    
    def __init__(self, wf1947_instrument, sr830_instrument, pid_params=None, initial_frequency=None):
        super().__init__()
        # 直接使用传入的仪器实例
        self.wf1947: WF1947 = wf1947_instrument
        self.sr830: SR830 = sr830_instrument
        
        # 初始频率
        self.initial_frequency = initial_frequency
        
        # PID控制器
        if pid_params is None:
            pid_params = {'kp': 1.0, 'ki': 0.1, 'kd': 0.01, 'setpoint': 0.0}
        
        self.pid = DigitalPID(
            kp=pid_params['kp'],
            ki=pid_params['ki'], 
            kd=pid_params['kd'],
            setpoint=pid_params['setpoint'],
            sample_time=0.1  # 100ms采样时间
        )
        
        # 设置合理的输出限制（频率调整范围）
        self.pid.set_output_limits(-1000, 1000)  # ±1000 Hz/s的调整速度
        self.pid.set_integral_limits(-5000, 5000)  # 积分限制
        
        # 控制参数
        self.is_tracking = False
        self.sample_interval = 0.1  # 采样间隔（秒）
        self.max_duration = None  # 最大追踪时间
        
        # 数据存储
        self.tracking_data = []
        self.start_time = None
        
    def set_pid_params(self, kp: float, ki: float, kd: float, setpoint: float):
        """更新PID参数"""
        self.pid.set_pid_params(kp, ki, kd)
        self.pid.set_setpoint(setpoint)
        
    def set_tracking_params(self, sample_interval: float, max_duration: Optional[float] = None):
        """设置追踪参数"""
        self.sample_interval = sample_interval
        self.max_duration = max_duration
        self.pid.set_sample_time(sample_interval)
        
    def start_tracking(self):
        """开始频率追踪"""
        # 检查仪器实例是否有效
        if not self.wf1947 or not self.sr830:
            raise Exception("无效的仪器实例")
            
        self.is_tracking = True
        self.start_time = time.time()
        self.tracking_data = []
        self.pid.reset()
        
        self.start()
        
    def stop_tracking(self):
        """停止频率追踪"""
        self.is_tracking = False
        # 关闭输出
        self.wf1947.set_output(False)
        # 重置WF1947
        self.wf1947.reset()
            
    def run(self):
        """线程主循环"""
        try:
            self.status_updated.emit("正在初始化频率追踪...")
            
            # 使用传入的初始频率，如果没有则从WF1947读取
            if self.initial_frequency is not None:
                current_frequency = self.initial_frequency
                print(f"使用设定的初始频率: {current_frequency} Hz")
            else:
                current_frequency = self.wf1947.get_frequency()
                print(f"从WF1947读取初始频率: {current_frequency} Hz")
            
            self.status_updated.emit("数字PID频率追踪已启动")
            
            while self.is_tracking:
                current_time = time.time()
                elapsed_time = current_time - self.start_time
                
                # 检查最大持续时间
                if self.max_duration and elapsed_time >= self.max_duration:
                    self.is_tracking = False
                    break
                    
                try:
                    # 读取当前相位
                    phase_data = self.sr830.getOut(4)  # 获取相位
                    current_phase = phase_data[0] if isinstance(phase_data, (list, tuple)) else phase_data
                    
                    # PID计算
                    frequency_correction = self.pid.compute(current_phase, current_time)
                    
                    # 更新频率
                    new_frequency = current_frequency + frequency_correction * self.sample_interval
                    
                    # 限制频率范围（根据WF1947规格）
                    new_frequency = max(0.1, min(new_frequency, 30e6))  # 0.1Hz到30MHz
                    
                    # 设置新频率
                    self.wf1947.set_frequency(new_frequency)
                    current_frequency = new_frequency
                    
                    # 获取PID详细信息
                    pid_info = self.pid.get_pid_terms(current_phase, current_time)
                    
                    # 保存数据
                    data_point = {
                        'time': elapsed_time,
                        'timestamp': current_time,
                        'frequency': current_frequency,
                        'phase': current_phase,
                        'setpoint': self.pid.setpoint,
                        'error': pid_info['error'],
                        'pid_output': frequency_correction,
                        'proportional': pid_info['proportional'],
                        'integral': pid_info['integral'],
                        'derivative': pid_info['derivative']
                    }
                    
                    self.tracking_data.append(data_point)
                    self.data_updated.emit(data_point)
                    
                except Exception as e:
                    self.error_occurred.emit(f"追踪过程出错: {e}")
                    self.stop_tracking()
                    
                # 等待下一个采样周期
                time.sleep(self.sample_interval)
                
        except Exception as e:
            self.error_occurred.emit(f"频率追踪线程错误: {e}")
        finally:
            self.tracking_finished.emit()
            
    def get_tracking_data(self) -> list:
        """获取追踪数据"""
        return self.tracking_data.copy()
        
    def save_tracking_data(self, filename: str = None):
        """保存追踪数据"""
        if not self.tracking_data:
            return False, "没有数据可保存"
            
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from datasort import DataSort
            
            if filename is None:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"frequency_tracking_{timestamp}.dat"
            
            filepath = f"history_data/{filename}"
            success, message = DataSort.save_data_to_file(
                self.tracking_data, filepath, "Frequency Tracking Data"
            )
            
            return success, message
            
        except Exception as e:
            return False, f"保存数据失败: {e}"
