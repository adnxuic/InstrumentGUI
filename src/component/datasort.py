import MultiPyVu as mpv
import numpy as np
import time
import os
import json
import threading
from datetime import datetime

from PySide6.QtCore import QThread, Signal
from typing import Dict, List, Tuple, Optional

class DataRecordThread(QThread):
    """数据记录线程类，负责实时采集SR830和PPMS数据"""
    
    # 信号定义
    data_acquired = Signal(dict)  # 新数据信号
    recording_finished = Signal()  # 记录完成信号
    error_occurred = Signal(str)  # 错误信号
    time_updated = Signal(float)  # 时间更新信号
    
    def __init__(self, instruments_control, time_step=1.0, max_duration=None):
        super().__init__()
        self.instruments_control = instruments_control
        self.time_step = time_step  # 时间步长（秒）
        self.max_duration = max_duration  # 最大记录时间（秒），None表示无限制
        
        self.is_recording = False
        self.start_time = None
        self.data_points = []
        self.temp_save_interval = 300  # 5分钟保存一次临时文件
        self.last_temp_save = 0
        
        # 数据文件管理
        self.temp_dir = None
        self.temp_files = []
        
        # PPMS数据缓存机制
        self.ppms_cache = {}  # 缓存PPMS数据
        self.ppms_last_read_time = {}  # 记录每个PPMS上次读取时间
        self.ppms_read_interval = 1.0  # PPMS最小读取间隔（秒）
        self.ppms_cache_status_reported = {}  # 记录是否已报告缓存状态，避免重复日志
        
    def set_recording_params(self, time_step: float, max_duration: Optional[float] = None):
        """设置记录参数"""
        self.time_step = time_step
        self.max_duration = max_duration
        
    def start_recording(self):
        """开始记录"""
        self.is_recording = True
        self.start_time = time.time()
        self.data_points = []
        self.last_temp_save = 0
        self.temp_files = []
        
        # 清空PPMS缓存，确保新记录从头开始
        self.ppms_cache.clear()
        self.ppms_last_read_time.clear()
        self.ppms_cache_status_reported.clear()
        
        # 创建临时文件夹
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.temp_dir = os.path.join("temp_data", f"recording_{timestamp}")
        os.makedirs(self.temp_dir, exist_ok=True)
        
        self.start()
        
    def stop_recording(self):
        """停止记录"""
        self.is_recording = False
        
    def run(self):
        """线程主循环"""
        consecutive_errors = 0
        max_consecutive_errors = 10  # 允许最大连续错误次数
        
        try:
            while self.is_recording:
                current_time = time.time()
                elapsed_time = current_time - self.start_time
                
                # 检查是否超过最大记录时间
                if self.max_duration and elapsed_time >= self.max_duration:
                    self.is_recording = False
                    break
                
                try:
                    # 采集数据
                    data_point = self._collect_data(elapsed_time)
                    if data_point:
                        self.data_points.append(data_point)
                        self.data_acquired.emit(data_point)
                        self.time_updated.emit(elapsed_time)
                        consecutive_errors = 0  # 重置错误计数
                        
                        # 检查是否需要保存临时文件
                        if elapsed_time - self.last_temp_save >= self.temp_save_interval:
                            self._save_temp_file()
                            self.last_temp_save = elapsed_time
                    else:
                        consecutive_errors += 1
                        
                except Exception as data_error:
                    consecutive_errors += 1
                    self.error_occurred.emit(f"数据采集出错 (第{consecutive_errors}次): {data_error}")
                    
                    # 如果连续错误太多，停止记录
                    if consecutive_errors >= max_consecutive_errors:
                        self.error_occurred.emit(f"连续错误达到{max_consecutive_errors}次，停止记录")
                        self.is_recording = False
                        break
                
                # 等待下一个时间步长
                time.sleep(self.time_step)
                
        except Exception as e:
            self.error_occurred.emit(f"记录线程发生严重错误: {e}")
        finally:
            # 保存最后的临时文件
            if self.data_points:
                try:
                    self._save_temp_file()
                except Exception as save_error:
                    self.error_occurred.emit(f"保存最终临时文件失败: {save_error}")
            self.recording_finished.emit()
            
    def _collect_data(self, elapsed_time: float) -> Dict:
        """采集所有仪器数据"""
        data_point = {
            'time': elapsed_time,
            'timestamp': time.time()
        }
        
        try:
            # 采集SR830数据
            sr830_data = {}
            for address, instrument in self.instruments_control.instruments_instance.items():
                if hasattr(instrument, 'type') and instrument.type == "SR830":
                    try:
                        # 使用SNAP命令同时获取X, Y, R, θ, frequency
                        snap_data = instrument.getSnap(1, 2, 3, 4, 9)  # X, Y, R, θ, frequency
                        sr830_data[f"{address}_X"] = snap_data[0]
                        sr830_data[f"{address}_Y"] = snap_data[1] 
                        sr830_data[f"{address}_R"] = snap_data[2]
                        sr830_data[f"{address}_theta"] = snap_data[3]
                        sr830_data[f"{address}_frequency"] = snap_data[4]
                    except Exception as e:
                        self.error_occurred.emit(f"SR830 {address} 数据读取错误: {e}")
            
            data_point['SR830'] = sr830_data
            
            # 采集PPMS数据（使用缓存机制，最多1秒读取一次）
            ppms_data = {}
            current_time = time.time()
            
            for address, instrument in self.instruments_control.instruments_instance.items():
                if hasattr(instrument, 'type') and instrument.type == "PPMS":
                    # 检查是否需要重新读取PPMS数据
                    last_read = self.ppms_last_read_time.get(address, 0)
                    time_since_last_read = current_time - last_read
                    
                    if time_since_last_read >= self.ppms_read_interval:
                        # 需要重新读取数据
                        try:
                            T, sT, F, sF = instrument.get_temperature_field()
                            
                            # 更新缓存
                            self.ppms_cache[address] = {
                                'temperature': T,
                                'field': F,
                                'temp_status': sT,
                                'field_status': sF
                            }
                            self.ppms_last_read_time[address] = current_time
                            
                            # 首次读取时报告缓存机制启用
                            if address not in self.ppms_cache_status_reported:
                                # 缓存机制启用（内部状态，无需用户通知）
                                self.ppms_cache_status_reported[address] = True
                            
                        except Exception as e:
                            # 记录错误但继续处理其他仪器
                            error_msg = str(e)
                            if "Incorrect Message ID" in error_msg:
                                self.error_occurred.emit(f"PPMS {address} 通信错误 (使用缓存数据): Message ID 错误")
                            else:
                                self.error_occurred.emit(f"PPMS {address} 数据读取错误: {e}")
                            
                            # 如果读取失败且没有缓存数据，跳过这个仪器
                            if address not in self.ppms_cache:
                                continue
                    
                    # 使用缓存的数据（无论是刚读取的还是之前缓存的）
                    if address in self.ppms_cache:
                        cached_data = self.ppms_cache[address]
                        ppms_data[f"{address}_temperature"] = cached_data['temperature']
                        ppms_data[f"{address}_field"] = cached_data['field']
                        ppms_data[f"{address}_temp_status"] = cached_data['temp_status']
                        ppms_data[f"{address}_field_status"] = cached_data['field_status']
            
            data_point['PPMS'] = ppms_data
            
            return data_point
            
        except Exception as e:
            self.error_occurred.emit(f"数据采集错误: {e}")
            return None
            
    def _save_temp_file(self):
        """保存临时数据文件"""
        if not self.data_points:
            return
            
        try:
            temp_filename = f"temp_{len(self.temp_files):03d}.json"
            temp_filepath = os.path.join(self.temp_dir, temp_filename)
            
            with open(temp_filepath, 'w', encoding='utf-8') as f:
                json.dump(self.data_points, f, indent=2)
                
            self.temp_files.append(temp_filepath)
            self.data_points = []  # 清空已保存的数据点
            
        except Exception as e:
            self.error_occurred.emit(f"保存临时文件失败: {e}")
            
    def save_final_data(self, filename: str = None) -> Tuple[bool, str]:
        """保存最终数据文件"""
        try:
            # 确保history_data文件夹存在
            history_dir = "history_data"
            os.makedirs(history_dir, exist_ok=True)
            
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"data_record_{timestamp}.dat"
            
            filepath = os.path.join(history_dir, filename)
            
            # 合并所有临时文件和当前数据
            all_data = []
            
            # 读取所有临时文件
            for temp_file in self.temp_files:
                try:
                    with open(temp_file, 'r', encoding='utf-8') as f:
                        temp_data = json.load(f)
                        all_data.extend(temp_data)
                except Exception as e:
                    self.error_occurred.emit(f"读取临时文件失败 {temp_file}: {e}")
            
            # 添加当前数据点
            all_data.extend(self.data_points)
            
            # 使用MultiPyVu.DataFile保存
            if all_data:
                self._save_with_multipyvu(filepath, all_data)
                
                # 清理临时文件
                self._cleanup_temp_files()
                
                return True, filepath
            else:
                self.error_occurred.emit("没有数据可保存")
                return False, ""
                
        except Exception as e:
            self.error_occurred.emit(f"保存最终数据失败: {e}")
            return False, ""
            
    def _save_with_multipyvu(self, filepath: str, data: List[Dict]):
        """使用MultiPyVu.DataFile保存数据"""
        try:
            # 创建DataFile实例
            data_file = mpv.DataFile()
            
            # 准备列名和数据
            if not data:
                return
                
            # 从第一个数据点推断列结构
            sample_data = data[0]
            columns = ['Time (s)']
            
            # 添加SR830列
            for key in sample_data.get('SR830', {}):
                columns.append(f"SR830_{key}")
                
            # 添加PPMS列  
            for key in sample_data.get('PPMS', {}):
                columns.append(f"PPMS_{key}")
            
            # 添加列到DataFile
            data_file.add_multiple_columns(columns)
            
            # 创建文件和写入头部
            data_file.create_file_and_write_header(filepath, 'Instrument Data Recording')
            
            # 写入所有数据点
            for point in data:
                # 设置时间值
                data_file.set_value('Time (s)', point['time'])
                
                # 设置SR830数据
                sr830_data = point.get('SR830', {})
                for key, value in sr830_data.items():
                    data_file.set_value(f"SR830_{key}", value)
                
                # 设置PPMS数据
                ppms_data = point.get('PPMS', {})
                for key, value in ppms_data.items():
                    data_file.set_value(f"PPMS_{key}", value)
                
                # 写入这一行数据
                data_file.write_data()
            
        except Exception as e:
            # 如果MultiPyVu保存失败，使用JSON作为备选
            with open(filepath + '.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            raise e
            
    def _cleanup_temp_files(self):
        """清理临时文件"""
        try:
            for temp_file in self.temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            
            if self.temp_dir and os.path.exists(self.temp_dir):
                os.rmdir(self.temp_dir)
                
        except Exception as e:
            self.error_occurred.emit(f"清理临时文件失败: {e}")


class DataSort:
    """数据排序和管理类"""
    
    def __init__(self):
        self.current_data = []
        self.data_columns = []
        
    @staticmethod
    def save_data_to_file(data: List[Dict], filepath: str, data_source: str = "Instrument Data") -> Tuple[bool, str]:
        """
        通用数据保存方法，支持多种仪器数据格式
        
        Args:
            data: 要保存的数据列表，每个元素是一个字典
            filepath: 保存路径
            data_source: 数据源描述
            
        Returns:
            (success: bool, message: str): 成功状态和消息
        """
        try:
            if not data:
                return False, "没有数据可保存"
                
            # 确保目录存在
            directory = os.path.dirname(filepath)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            # 尝试使用MultiPyVu格式保存
            try:
                DataSort._save_with_multipyvu_format(data, filepath, data_source)
                return True, f"数据已保存到: {filepath}"
            except Exception as mpv_error:
                # MultiPyVu保存失败，尝试CSV格式
                try:
                    import pandas as pd
                    DataSort._save_as_csv(data, filepath)
                    return True, f"数据已保存为CSV格式: {filepath}"
                except ImportError:
                    # 没有pandas，使用JSON格式
                    DataSort._save_as_json(data, filepath)
                    return True, f"数据已保存为JSON格式: {filepath}"
                except Exception as csv_error:
                    # CSV也失败，使用JSON作为最后备选
                    DataSort._save_as_json(data, filepath)
                    return True, f"数据已保存为JSON格式: {filepath} (CSV保存失败: {csv_error})"
                    
        except Exception as e:
            return False, f"保存数据失败: {e}"
    
    @staticmethod
    def _save_with_multipyvu_format(data: List[Dict], filepath: str, data_source: str):
        """使用MultiPyVu格式保存数据"""
        # 创建DataFile实例
        data_file = mpv.DataFile()
        
        # 从第一个数据点推断列结构
        sample_data = data[0]
        columns = []
        
        # 分析数据结构并创建列名
        for key, value in sample_data.items():
            if isinstance(value, dict):
                # 嵌套字典（如SR830, PPMS数据）
                for sub_key in value.keys():
                    columns.append(f"{key}_{sub_key}")
            else:
                # 简单值
                columns.append(key)
        
        # 添加列到DataFile
        data_file.add_multiple_columns(columns)
        
        # 创建文件和写入头部
        data_file.create_file_and_write_header(filepath, data_source)
        
        # 写入所有数据点
        for point in data:
            # 设置所有列的值
            for key, value in point.items():
                if isinstance(value, dict):
                    # 嵌套字典数据
                    for sub_key, sub_value in value.items():
                        column_name = f"{key}_{sub_key}"
                        data_file.set_value(column_name, sub_value)
                else:
                    # 简单值
                    data_file.set_value(key, value)
            
            # 写入这一行数据
            data_file.write_data()
    
    @staticmethod 
    def _save_as_csv(data: List[Dict], filepath: str):
        """使用CSV格式保存数据（需要pandas）"""
        import pandas as pd
        
        # 展平嵌套字典
        flattened_data = []
        for point in data:
            flat_point = {}
            for key, value in point.items():
                if isinstance(value, dict):
                    # 嵌套字典数据
                    for sub_key, sub_value in value.items():
                        flat_point[f"{key}_{sub_key}"] = sub_value
                else:
                    # 简单值
                    flat_point[key] = value
            flattened_data.append(flat_point)
        
        # 转换为DataFrame并保存
        df = pd.DataFrame(flattened_data)
        
        # 确保文件扩展名为.csv
        if not filepath.endswith('.csv'):
            filepath = filepath + '.csv'
        
        df.to_csv(filepath, index=False)
    
    @staticmethod
    def _save_as_json(data: List[Dict], filepath: str):
        """使用JSON格式保存数据"""
        # 确保文件扩展名为.json
        if not filepath.endswith('.json'):
            filepath = filepath + '.json'
            
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def update_data(self, new_data_point: Dict):
        """更新当前数据"""
        self.current_data.append(new_data_point)
        
    def get_data_for_plotting(self, x_column: str, y_column: str) -> Tuple[List, List]:
        """获取用于绘图的数据"""
        if not self.current_data:
            return [], []
            
        x_data = []
        y_data = []
        
        for point in self.current_data:
            # 获取X轴数据
            x_val = self._extract_value(point, x_column)
            # 获取Y轴数据  
            y_val = self._extract_value(point, y_column)
            
            if x_val is not None and y_val is not None:
                x_data.append(x_val)
                y_data.append(y_val)
                
        return x_data, y_data
        
    def _extract_value(self, data_point: Dict, column: str):
        """从数据点中提取指定列的值"""
        if column == 'time':
            return data_point.get('time', 0)
        
        # SR830数据
        if column.startswith('SR830_'):
            sr830_key = column[6:]  # 去掉'SR830_'前缀
            return data_point.get('SR830', {}).get(sr830_key)
            
        # PPMS数据
        if column.startswith('PPMS_'):
            ppms_key = column[5:]  # 去掉'PPMS_'前缀
            return data_point.get('PPMS', {}).get(ppms_key)
            
        return None
        
    def get_available_columns(self) -> List[str]:
        """获取可用的列名"""
        if not self.current_data:
            return ['time']
            
        columns = ['time']
        sample_data = self.current_data[-1]  # 使用最新数据点
        
        # 添加SR830列
        for key in sample_data.get('SR830', {}):
            columns.append(f"SR830_{key}")
            
        # 添加PPMS列
        for key in sample_data.get('PPMS', {}):
            columns.append(f"PPMS_{key}")
            
        return columns
        
    def clear_data(self):
        """清空当前数据"""
        self.current_data = []
        self.data_columns = []