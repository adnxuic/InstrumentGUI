from PySide6.QtWidgets import QWidget, QScrollArea, QVBoxLayout
from PySide6.QtCore import Qt, QTimer

import matplotlib as mpl
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.backends.backend_qtagg import (
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.style import use
import matplotlib.pyplot as plt

mpl.use("QtAgg")
plt.rcParams['font.family'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


class PyFigureCanvas(QWidget):
    def __init__(self, width=8, height=6, dpi=100):
        super().__init__()

        # 创建适中大小的figure，让它能适应canvas
        self.fig = Figure(figsize=(width, height), dpi=dpi, tight_layout=True)
        self.canva = FigureCanvasQTAgg(self.fig)
        
        # 不设置固定大小，让canvas自适应
        # 设置合理的最小大小
        self.canva.setMinimumSize(400, 300)
        
        # 为数据记录创建双轴图
        self.setup_data_record_plots()

        self.init_set()

    def setup_data_record_plots(self):
        """为数据记录设置双轴图表"""
        # 清除现有的轴
        self.fig.clear()
        
        # 创建两个子图，调整间距
        self.ax1 = self.fig.add_subplot(2, 1, 1)
        self.ax2 = self.fig.add_subplot(2, 1, 2)
        
        # 设置初始标题和标签
        self.ax1.set_title("实时数据图表 1", fontsize=12, fontweight='bold')
        self.ax2.set_title("实时数据图表 2", fontsize=12, fontweight='bold')
        
        # 设置初始轴标签
        self.ax1.set_xlabel("时间 (s)")
        self.ax1.set_ylabel("数值")
        self.ax2.set_xlabel("时间 (s)")
        self.ax2.set_ylabel("数值")
        
        # 启用网格
        self.ax1.grid(True, alpha=0.3)
        self.ax2.grid(True, alpha=0.3)
        
        # 初始化线条对象
        self.line1, = self.ax1.plot([], [], 'b-', linewidth=2, label='数据1')
        self.line2, = self.ax2.plot([], [], 'r-', linewidth=2, label='数据2')
        
        # 添加图例
        self.ax1.legend(loc='upper right')
        self.ax2.legend(loc='upper right')
        
        # 设置图表间距，使用更紧凑的布局
        self.fig.subplots_adjust(left=0.12, right=0.95, top=0.92, bottom=0.12, hspace=0.45)
        
        # 数据存储
        self.plot1_data = {'x': [], 'y': []}
        self.plot2_data = {'x': [], 'y': []}
        
        # 数据窗口大小（显示最近的N个点）
        self.max_points = 1000
        
        # 自动缩放标志
        self.auto_scale = True
        
    def update_data_record_plots(self, plot_data):
        """更新数据记录图表
        
        Args:
            plot_data: 包含两个图表数据的字典
                {
                    'plot1': {'x': [...], 'y': [...]},
                    'plot2': {'x': [...], 'y': [...]},
                    'settings': {'plot1': {'x_axis': ..., 'y_axis': ...}, ...}
                }
        """
        if not plot_data:
            return
            
        try:
            # 更新图表1
            if 'plot1' in plot_data and plot_data['plot1']['x'] and plot_data['plot1']['y']:
                x1_data = plot_data['plot1']['x']
                y1_data = plot_data['plot1']['y']
                
                # 限制数据点数量
                if len(x1_data) > self.max_points:
                    x1_data = x1_data[-self.max_points:]
                    y1_data = y1_data[-self.max_points:]
                
                self.line1.set_data(x1_data, y1_data)
                
                # 更新轴范围
                if self.auto_scale and x1_data and y1_data:
                    # 处理x轴范围
                    x_min, x_max = min(x1_data), max(x1_data)
                    if x_min == x_max:
                        # 当只有一个点或所有点x值相同时，设置一个合理的范围
                        x_range = max(1.0, abs(x_min) * 0.1)  # 设置为绝对值的10%或最小1.0
                        self.ax1.set_xlim(x_min - x_range, x_max + x_range)
                    else:
                        self.ax1.set_xlim(x_min, x_max)
                    
                    # 处理y轴范围
                    y_min, y_max = min(y1_data), max(y1_data)
                    if y_min == y_max:
                        # 当所有y值相同时，设置一个合理的范围
                        y_range = max(0.1, abs(y_min) * 0.1)
                        self.ax1.set_ylim(y_min - y_range, y_max + y_range)
                    else:
                        margin = 0.1 * (y_max - y_min)
                        self.ax1.set_ylim(y_min - margin, y_max + margin)
            
            # 更新图表2
            if 'plot2' in plot_data and plot_data['plot2']['x'] and plot_data['plot2']['y']:
                x2_data = plot_data['plot2']['x']
                y2_data = plot_data['plot2']['y']
                
                # 限制数据点数量
                if len(x2_data) > self.max_points:
                    x2_data = x2_data[-self.max_points:]
                    y2_data = y2_data[-self.max_points:]
                
                self.line2.set_data(x2_data, y2_data)
                
                # 更新轴范围
                if self.auto_scale and x2_data and y2_data:
                    # 处理x轴范围
                    x_min, x_max = min(x2_data), max(x2_data)
                    if x_min == x_max:
                        # 当只有一个点或所有点x值相同时，设置一个合理的范围
                        x_range = max(1.0, abs(x_min) * 0.1)  # 设置为绝对值的10%或最小1.0
                        self.ax2.set_xlim(x_min - x_range, x_max + x_range)
                    else:
                        self.ax2.set_xlim(x_min, x_max)
                    
                    # 处理y轴范围
                    y_min, y_max = min(y2_data), max(y2_data)
                    if y_min == y_max:
                        # 当所有y值相同时，设置一个合理的范围
                        y_range = max(0.1, abs(y_min) * 0.1)
                        self.ax2.set_ylim(y_min - y_range, y_max + y_range)
                    else:
                        margin = 0.1 * (y_max - y_min)
                        self.ax2.set_ylim(y_min - margin, y_max + margin)
            
            # 更新轴标签
            if 'settings' in plot_data:
                settings = plot_data['settings']
                
                # 更新图表1轴标签
                if 'plot1' in settings:
                    self.ax1.set_xlabel(self._format_axis_label(settings['plot1']['x_axis']))
                    self.ax1.set_ylabel(self._format_axis_label(settings['plot1']['y_axis']))
                    self.line1.set_label(settings['plot1']['y_axis'])
                
                # 更新图表2轴标签
                if 'plot2' in settings:
                    self.ax2.set_xlabel(self._format_axis_label(settings['plot2']['x_axis']))
                    self.ax2.set_ylabel(self._format_axis_label(settings['plot2']['y_axis']))
                    self.line2.set_label(settings['plot2']['y_axis'])
                
                # 更新图例
                self.ax1.legend(loc='upper right')
                self.ax2.legend(loc='upper right')
            
            # 重新绘制
            self.canva.draw()
            
        except Exception as e:
            print(f"更新图表时出错: {e}")
            
    def _format_axis_label(self, column_name):
        """格式化轴标签"""
        if column_name == 'time':
            return "时间 (s)"
        elif column_name.startswith('SR830_'):
            parts = column_name.split('_')
            if len(parts) >= 3:
                instrument = parts[1]
                param = parts[2]
                param_names = {
                    'X': 'X分量 (V)',
                    'Y': 'Y分量 (V)', 
                    'R': '幅度 R (V)',
                    'theta': '相位 θ (°)',
                    'frequency': '频率 (Hz)'
                }
                return f"{instrument} - {param_names.get(param, param)}"
        elif column_name.startswith('PPMS_'):
            parts = column_name.split('_')
            if len(parts) >= 3:
                instrument = parts[1]
                param = parts[2]
                param_names = {
                    'temperature': '温度 (K)',
                    'field': '磁场 (Oe)'
                }
                return f"{instrument} - {param_names.get(param, param)}"
        
        return column_name
        
    def clear_data_record_plots(self):
        """清空数据记录图表"""
        self.line1.set_data([], [])
        self.line2.set_data([], [])
        self.plot1_data = {'x': [], 'y': []}
        self.plot2_data = {'x': [], 'y': []}
        
        # 重置轴范围
        self.ax1.set_xlim(0, 1)
        self.ax1.set_ylim(0, 1)
        self.ax2.set_xlim(0, 1)
        self.ax2.set_ylim(0, 1)
        
        self.canva.draw()
        
    def set_auto_scale(self, enabled):
        """设置自动缩放"""
        self.auto_scale = enabled
        
    def set_max_points(self, max_points):
        """设置最大显示点数"""
        self.max_points = max_points
        
    def save_plot(self, filename):
        """保存图表"""
        try:
            self.fig.savefig(filename, dpi=300, bbox_inches='tight')
            return True
        except Exception as e:
            print(f"保存图表失败: {e}")
            return False
            
    def setup_frequency_sweep_plot(self):
        """设置频率扫描图表"""
        self.fig.clear()
        
        # 创建两个子图：振幅和相位
        self.ax1 = self.fig.add_subplot(2, 1, 1)
        self.ax2 = self.fig.add_subplot(2, 1, 2)
        
        # 设置振幅响应图
        self.ax1.set_title("频率扫描 - 振幅响应", fontsize=12, fontweight='bold')
        self.ax1.set_ylabel("振幅 (V)")
        self.ax1.grid(True, alpha=0.3)
        
        # 设置相位响应图
        self.ax2.set_title("频率扫描 - 相位响应", fontsize=12, fontweight='bold')
        self.ax2.set_xlabel("频率 (Hz)")
        self.ax2.set_ylabel("相位 (°)")
        self.ax2.grid(True, alpha=0.3)
        
        # 更好的布局
        self.fig.subplots_adjust(left=0.12, right=0.95, top=0.92, bottom=0.12, hspace=0.45)
        self.canva.draw()
        
    def setup_frequency_tracking_plot(self):
        """设置共振频率追踪图表"""
        self.fig.clear()
        
        # 创建两个子图：频率和相位
        self.ax1 = self.fig.add_subplot(2, 1, 1)
        self.ax2 = self.fig.add_subplot(2, 1, 2)
        
        self.ax1.set_title("频率追踪 - 输出频率", fontsize=12, fontweight='bold')
        self.ax1.set_ylabel("频率 (Hz)")
        self.ax1.grid(True, alpha=0.3)
        
        self.ax2.set_title("频率追踪 - 相位", fontsize=12, fontweight='bold')
        self.ax2.set_xlabel("时间 (s)")
        self.ax2.set_ylabel("相位 (°)")
        self.ax2.grid(True, alpha=0.3)
        
        # 初始化线条对象
        self.freq_line, = self.ax1.plot([], [], 'b-', linewidth=2, label='WF1947频率')
        self.phase_line, = self.ax2.plot([], [], 'r-', linewidth=2, label='SR830相位')
        
        # 添加目标相位参考线（将在update时设置）
        self.setpoint_line, = self.ax2.plot([], [], 'g--', linewidth=1, label='目标相位')
        
        # 添加图例
        self.ax1.legend(loc='upper right')
        self.ax2.legend(loc='upper right')
        
        # 更好的布局
        self.fig.subplots_adjust(left=0.12, right=0.95, top=0.92, bottom=0.12, hspace=0.45)
        self.canva.draw()
        
    def update_frequency_sweep_plots(self, plot_data):
        """更新频率扫描图表
        
        Args:
            plot_data: 包含频率扫描数据的字典
                {
                    'frequency': [...],
                    'amplitude': [...],
                    'phase': [...]
                }
        """
        if not plot_data or not plot_data.get('frequency'):
            return
            
        try:
            frequencies = plot_data['frequency']
            amplitudes = plot_data['amplitude']
            phases = plot_data['phase']
            
            # 清除之前的图
            self.ax1.clear()
            self.ax2.clear()
            
            # 绘制振幅响应
            self.ax1.semilogx(frequencies, amplitudes, 'b-', linewidth=2, marker='o', markersize=3)
            self.ax1.set_title("频率扫描 - 振幅响应", fontsize=12, fontweight='bold')
            self.ax1.set_ylabel("振幅 (V)")
            self.ax1.grid(True, alpha=0.3)
            
            # 绘制相位响应
            self.ax2.semilogx(frequencies, phases, 'r-', linewidth=2, marker='s', markersize=3)
            self.ax2.set_title("频率扫描 - 相位响应", fontsize=12, fontweight='bold')
            self.ax2.set_xlabel("频率 (Hz)")
            self.ax2.set_ylabel("相位 (°)")
            self.ax2.grid(True, alpha=0.3)
            
            # 自动调整范围
            if len(frequencies) > 0:
                freq_min, freq_max = min(frequencies), max(frequencies)
                
                # 设置频率轴范围（对于对数坐标，使用乘法设置边距）
                if freq_min > 0 and freq_max > 0:  # 确保频率为正值
                    # 对于对数坐标，使用比例边距而不是绝对边距
                    freq_ratio = freq_max / freq_min if freq_min > 0 else 10
                    margin_factor = 1.1  # 10% 的边距
                    
                    freq_lower = freq_min / margin_factor
                    freq_upper = freq_max * margin_factor
                    
                    self.ax1.set_xlim(freq_lower, freq_upper)
                    self.ax2.set_xlim(freq_lower, freq_upper)
                
                # 设置振幅轴范围
                if len(amplitudes) > 0:
                    amp_min, amp_max = min(amplitudes), max(amplitudes)
                    amp_margin = 0.1 * (amp_max - amp_min)
                    if amp_margin == 0:
                        amp_margin = max(amp_max * 0.1, 1e-6)
                    self.ax1.set_ylim(amp_min - amp_margin, amp_max + amp_margin)
                
                # 设置相位轴范围
                if len(phases) > 0:
                    phase_min, phase_max = min(phases), max(phases)
                    phase_margin = 0.1 * (phase_max - phase_min)
                    if phase_margin == 0:
                        phase_margin = 10.0  # 默认10度边距
                    self.ax2.set_ylim(phase_min - phase_margin, phase_max + phase_margin)
            
            # 更好的布局
            self.fig.subplots_adjust(left=0.12, right=0.95, top=0.92, bottom=0.12, hspace=0.45)
            
            # 重新绘制
            self.canva.draw()
            
        except Exception as e:
            print(f"更新频率扫描图表时出错: {e}")
            
    def update_frequency_tracking_plots(self, plot_data):
        """更新频率追踪图表
        
        Args:
            plot_data: 包含频率追踪数据的字典
                {
                    'frequency_tracking': {
                        'time': [...],
                        'frequency': [...],
                        'phase': [...],
                        'setpoint': float (可选)
                    }
                }
        """
        if not plot_data or 'frequency_tracking' not in plot_data:
            return
            
        try:
            tracking_data = plot_data['frequency_tracking']
            times = tracking_data.get('time', [])
            frequencies = tracking_data.get('frequency', [])
            phases = tracking_data.get('phase', [])
            setpoint = tracking_data.get('setpoint', None)
            
            if not times or not frequencies or not phases:
                return
                
            # 更新频率图
            self.freq_line.set_data(times, frequencies)
            
            # 更新相位图
            self.phase_line.set_data(times, phases)
            
            # 更新目标相位参考线
            if setpoint is not None and times:
                setpoint_y = [setpoint] * len(times)
                self.setpoint_line.set_data(times, setpoint_y)
            
            # 自动调整坐标轴范围
            if len(times) > 0:
                time_min, time_max = min(times), max(times)
                time_margin = max(0.1, (time_max - time_min) * 0.05)
                
                # 频率轴范围
                if len(frequencies) > 0:
                    freq_min, freq_max = min(frequencies), max(frequencies)
                    freq_margin = max(1.0, (freq_max - freq_min) * 0.1)
                    
                    self.ax1.set_xlim(time_min - time_margin, time_max + time_margin)
                    self.ax1.set_ylim(freq_min - freq_margin, freq_max + freq_margin)
                
                # 相位轴范围
                if len(phases) > 0:
                    phase_min, phase_max = min(phases), max(phases)
                    
                    # 处理相位的特殊情况（可能需要扩展到±180度范围）
                    if setpoint is not None:
                        phase_min = min(phase_min, setpoint - 10)
                        phase_max = max(phase_max, setpoint + 10)
                    
                    phase_margin = max(5.0, (phase_max - phase_min) * 0.1)
                    
                    self.ax2.set_xlim(time_min - time_margin, time_max + time_margin)
                    self.ax2.set_ylim(phase_min - phase_margin, phase_max + phase_margin)
            
            # 重新绘制
            self.canva.draw()
            
        except Exception as e:
            print(f"更新频率追踪图表时出错: {e}")
            
    def clear_frequency_tracking_plots(self):
        """清空频率追踪图表"""
        if hasattr(self, 'freq_line'):
            self.freq_line.set_data([], [])
        if hasattr(self, 'phase_line'):
            self.phase_line.set_data([], [])
        if hasattr(self, 'setpoint_line'):
            self.setpoint_line.set_data([], [])
            
        # 重置轴范围
        self.ax1.set_xlim(0, 1)
        self.ax1.set_ylim(0, 1)
        self.ax2.set_xlim(0, 1) 
        self.ax2.set_ylim(-180, 180)
        
        self.canva.draw()

    def init_set(self):
        # 添加滚动条
        self.scroArea = QScrollArea()
        self.scroArea.setWidget(self.canva)
        self.scroArea.setAlignment(Qt.AlignCenter)
        self.scroArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        layout = QVBoxLayout()

        toolbox = NavigationToolbar(self.canva, self)

        layout.addWidget(toolbox)
        layout.addWidget(self.scroArea)

        self.setLayout(layout)
