from .sr830 import SR830
from .wf1947 import WF1947
from .ppms import PPMS

import os
import json
import logging
import time
from typing import Dict, Tuple, Optional


class InstrumentsControl:
    def __init__(self):
        # 设置日志
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # 仪器配置字典：{仪器类型：[仪器地址]}
        self.instruments_config = {
                    "SR830": [],
                    "WF1947": [],
                    "PPMS": []
                }
        self.instruments_instance = {} # 仪器实例字典：{仪器地址: 仪器实例}
        
        # 配置文件路径
        self.config_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'config')
        self.config_file = os.path.join(self.config_dir, 'instruments_config.json')
        
        self.init_instruments()

    def init_instruments(self) -> Dict[str, bool]:
        """初始化仪器配置
        
        Returns:
            Dict[str, bool]: 仪器地址到连接状态的映射
        """
        try:
            # 检查并创建config文件夹
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir)
                self.logger.info(f"已创建配置文件夹: {self.config_dir}")

            # 检查并创建instruments_config.json文件
            if not os.path.exists(self.config_file):
                self.logger.warning(f"仪器配置文件不存在: {self.config_file}")
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(self.instruments_config, f, indent=2)
                self.logger.info(f"已创建仪器配置文件: {self.config_file}")
                return {}

            # 加载仪器配置
            config_status = {} # 记录仪器配置文件导入是否加载成功，{仪器地址: 导入状态}
            with open(self.config_file, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
                self.logger.info(f"已加载仪器配置: {loaded_config}")
                
                for instrument_type, instrument_addresses in loaded_config.items():
                    if instrument_type not in self.instruments_config:
                        self.logger.warning(f"未知的仪器类型: {instrument_type}")
                        continue
                        
                    for instrument_address in instrument_addresses:
                        success, error_msg = self.add_instrument(instrument_type, instrument_address)
                        config_status[instrument_address] = success
                        if not success:
                            self.logger.error(f"加载仪器失败 {instrument_address}: {error_msg}")
                        
            return config_status
            
        except json.JSONDecodeError as e:
            self.logger.error(f"配置文件格式错误: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"初始化仪器配置时发生未知错误: {e}")
            return {}

    def add_instrument(self, instrument_type: str, instrument_address: str, 
                      port: int = 5000, retry_count: int = 3) -> Tuple[bool, Optional[str]]:
        """添加仪器到列表
        
        Args:
            instrument_type: 仪器类型
            instrument_address: 仪器地址
            port: 端口号（用于PPMS）
            retry_count: 重试次数
            
        Returns:
            Tuple[bool, Optional[str]]: (成功状态, 错误信息)
        """
        if instrument_type not in self.instruments_config:
            error_msg = f"不支持的仪器类型: {instrument_type}"
            self.logger.error(error_msg)
            return False, error_msg
        
        # 检查是否已经存在
        if instrument_address in self.instruments_instance:
            self.logger.info(f"仪器 {instrument_address} 已存在")
            return True, None
        
        # 尝试连接仪器
        for attempt in range(retry_count):
            try:
                if instrument_type == "SR830":
                    instrument = SR830(instrument_address)
                elif instrument_type == "WF1947":
                    instrument = WF1947(instrument_address)
                elif instrument_type == "PPMS":
                    instrument = PPMS(instrument_address, port)
                else:
                    return False, f"不支持的仪器类型: {instrument_type}"
                
                # 连接成功
                self.instruments_instance[instrument_address] = instrument
                self.update_instrument_config(instrument_type, instrument_address)
                self.logger.info(f"成功连接仪器: {instrument_type} at {instrument_address}")
                return True, None
                
            except ConnectionError as e:
                error_msg = f"连接错误 (尝试 {attempt + 1}/{retry_count}): {e}"
                self.logger.warning(error_msg)
                if attempt < retry_count - 1:
                    time.sleep(1)  # 等待1秒后重试
                    
            except TimeoutError as e:
                error_msg = f"连接超时 (尝试 {attempt + 1}/{retry_count}): {e}"
                self.logger.warning(error_msg)
                if attempt < retry_count - 1:
                    time.sleep(2)  # 等待2秒后重试
                    
            except PermissionError as e:
                error_msg = f"权限错误: {e}"
                self.logger.error(error_msg)
                return False, error_msg  # 权限错误不重试
                
            except Exception as e:
                error_msg = f"未知错误 (尝试 {attempt + 1}/{retry_count}): {e}"
                self.logger.error(error_msg)
                if attempt < retry_count - 1:
                    time.sleep(1)
                    
        # 所有重试都失败
        final_error = f"{instrument_type}连接失败: 经过{retry_count}次尝试后仍无法连接到{instrument_address}"
        self.logger.error(final_error)
        return False, final_error
    
    def update_instrument_config(self, instrument_type: str, instrument_address: str):
        """更新连接成功的仪器配置，写入到仪器配置文件中"""
        try:
            if instrument_address not in self.instruments_config[instrument_type]:
                self.instruments_config[instrument_type].append(instrument_address)
                
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(self.instruments_config, f, indent=2, ensure_ascii=False)
                self.logger.info(f"已更新仪器配置: {instrument_type} - {instrument_address}")
                
        except Exception as e:
            self.logger.error(f"更新配置文件失败: {e}")
    
    def remove_instrument(self, instrument_address: str) -> bool:
        """移除仪器
        
        Args:
            instrument_address: 仪器地址
            
        Returns:
            bool: 移除是否成功
        """
        try:
            if instrument_address in self.instruments_instance:
                # 关闭仪器连接
                instrument = self.instruments_instance[instrument_address]
                if hasattr(instrument, 'close'):
                    instrument.close()
                
                # 从实例字典中移除
                del self.instruments_instance[instrument_address]
                
                # 从配置中移除
                for instrument_type, addresses in self.instruments_config.items():
                    if instrument_address in addresses:
                        addresses.remove(instrument_address)
                        break
                
                # 更新配置文件
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(self.instruments_config, f, indent=2, ensure_ascii=False)
                
                self.logger.info(f"已移除仪器: {instrument_address}")
                return True
            else:
                self.logger.warning(f"仪器不存在: {instrument_address}")
                return False
                
        except Exception as e:
            self.logger.error(f"移除仪器失败: {e}")
            return False

    def close_all_instruments(self) -> bool:
        """关闭所有仪器连接，用于程序退出时的清理
        
        Returns:
            bool: 清理是否成功
        """
        success = True
        instruments_to_close = list(self.instruments_instance.keys())  # 创建副本避免修改字典时出错
        
        for instrument_address in instruments_to_close:
            try:
                instrument = self.instruments_instance[instrument_address]
                if hasattr(instrument, 'close'):
                    instrument.close()
                    self.logger.info(f"已关闭仪器连接: {instrument_address}")
                else:
                    self.logger.warning(f"仪器 {instrument_address} 没有 close 方法")
                    
            except Exception as e:
                self.logger.error(f"关闭仪器 {instrument_address} 时发生错误: {e}")
                success = False
        
        # 清空实例字典
        self.instruments_instance.clear()
        
        if success:
            self.logger.info("所有仪器连接已成功关闭")
        else:
            self.logger.warning("部分仪器连接关闭时出现错误")
            
        return success