#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频震动控制GUI界面
提供直观的参数配置和实时监控界面
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import json
import os
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

class AudioVibrationGUI:
    def __init__(self, audio_processor, vibration_mapper, controller_manager):
        """初始化GUI界面"""
        self.audio_processor = audio_processor
        self.vibration_mapper = vibration_mapper
        self.controller_manager = controller_manager
        
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("声音转手柄震动控制器")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        
        # 界面状态
        self.is_running = False
        self.monitoring_thread = None
        
        # 实时数据存储 - 减小缓冲区以节省内存和提高性能
        self.audio_data_buffer = []
        self.vibration_data_buffer = []
        self.max_buffer_size = 100  # 减小缓冲区大小
        
        # 配置文件路径
        self.config_file = "audio_vibration_config.json"
        
        self.setup_gui()
        self.load_configuration()
        
        # 启动实时监控
        self.start_monitoring()
    
    def setup_gui(self):
        """设置GUI布局"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # 左侧控制面板
        self.setup_control_panel(main_frame)
        
        # 右侧监控面板
        self.setup_monitor_panel(main_frame)
        
        # 底部状态栏
        self.setup_status_bar()
    
    def setup_control_panel(self, parent):
        """设置左侧控制面板"""
        control_frame = ttk.LabelFrame(parent, text="控制面板", padding="10")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        row = 0
        
        # 设备选择区域
        device_frame = ttk.LabelFrame(control_frame, text="设备设置", padding="5")
        device_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        row += 1
        
        # 音频设备选择
        ttk.Label(device_frame, text="音频输入设备:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.audio_device_var = tk.StringVar()
        self.audio_device_combo = ttk.Combobox(device_frame, textvariable=self.audio_device_var, state="readonly")
        self.audio_device_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=2)
        self.audio_device_combo.bind("<<ComboboxSelected>>", self.on_device_changed)
        device_frame.columnconfigure(1, weight=1)
        
        # 刷新设备按钮
        ttk.Button(device_frame, text="刷新设备", command=self.refresh_devices).grid(row=0, column=2, padx=(5, 0), pady=2)
        
        # 系统音频帮助按钮
        ttk.Button(device_frame, text="系统音频帮助", command=self._show_system_audio_help).grid(row=0, column=3, padx=(5, 0), pady=2)
        
        # 控制器信息
        controller_info = self.controller_manager.get_controller_info()
        controller_text = f"控制器: {controller_info['controller_count']}个连接" if controller_info else "控制器: 未连接"
        ttk.Label(device_frame, text=controller_text).grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=2)
        
        # 启动/停止控制
        control_buttons_frame = ttk.Frame(control_frame)
        control_buttons_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        row += 1
        
        self.start_button = ttk.Button(control_buttons_frame, text="开始转换", command=self.toggle_conversion)
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(control_buttons_frame, text="紧急停止", command=self.emergency_stop).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_buttons_frame, text="测试震动", command=self.test_vibration).pack(side=tk.LEFT)
        
        # 预设配置区域
        preset_frame = ttk.LabelFrame(control_frame, text="预设配置", padding="5")
        preset_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        row += 1
        
        # 预设选择
        ttk.Label(preset_frame, text="选择预设:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.preset_var = tk.StringVar(value="balanced")
        preset_combo = ttk.Combobox(preset_frame, textvariable=self.preset_var, 
                                   values=list(self.vibration_mapper.presets.keys()), 
                                   state="readonly")
        preset_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=2)
        preset_combo.bind("<<ComboboxSelected>>", self.apply_preset)
        
        ttk.Button(preset_frame, text="应用预设", command=self.apply_preset).grid(row=0, column=2, padx=(5, 0), pady=2)
        preset_frame.columnconfigure(1, weight=1)
        
        # 基础参数区域
        basic_frame = ttk.LabelFrame(control_frame, text="基础参数", padding="5")
        basic_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        row += 1
        
        # 参数滑块
        self.create_parameter_slider(basic_frame, "整体强度", "overall_intensity", 0, 2.0, 0.01, 0, self.vibration_mapper.overall_intensity)
        self.create_parameter_slider(basic_frame, "低频敏感度", "low_freq_sensitivity", 0, 3.0, 0.01, 1, self.vibration_mapper.low_freq_sensitivity)
        self.create_parameter_slider(basic_frame, "高频敏感度", "high_freq_sensitivity", 0, 3.0, 0.01, 2, self.vibration_mapper.high_freq_sensitivity)
        self.create_parameter_slider(basic_frame, "平滑度", "smoothing_factor", 0, 1.0, 0.01, 3, self.vibration_mapper.smoothing_factor)
        
        # 高级参数区域
        advanced_frame = ttk.LabelFrame(control_frame, text="高级参数", padding="5")
        advanced_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        row += 1
        
        self.create_parameter_slider(advanced_frame, "频率分离点(Hz)", "frequency_cutoff", 100, 1000, 10, 0, self.vibration_mapper.frequency_cutoff)
        self.create_parameter_slider(advanced_frame, "最小音量阈值", "min_volume_threshold", 0, 0.1, 0.001, 1, self.vibration_mapper.min_volume_threshold)
        self.create_parameter_slider(advanced_frame, "最大音量阈值", "max_volume_threshold", 0.1, 2.0, 0.01, 2, self.vibration_mapper.max_volume_threshold)
        self.create_parameter_slider(advanced_frame, "攻击时间(秒)", "attack_time", 0.01, 1.0, 0.01, 3, self.vibration_mapper.attack_time)
        self.create_parameter_slider(advanced_frame, "衰减时间(秒)", "decay_time", 0.1, 3.0, 0.1, 4, self.vibration_mapper.decay_time)
        
        # 配置保存/加载
        config_frame = ttk.Frame(control_frame)
        config_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        row += 1
        
        ttk.Button(config_frame, text="保存配置", command=self.save_configuration).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(config_frame, text="加载配置", command=self.load_configuration_dialog).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(config_frame, text="重置默认", command=self.reset_to_defaults).pack(side=tk.LEFT)
    
    def setup_monitor_panel(self, parent):
        """设置右侧监控面板"""
        monitor_frame = ttk.LabelFrame(parent, text="实时监控", padding="10")
        monitor_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        monitor_frame.columnconfigure(0, weight=1)
        monitor_frame.rowconfigure(1, weight=1)
        
        # 实时数据显示
        data_frame = ttk.Frame(monitor_frame)
        data_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        data_frame.columnconfigure(1, weight=1)
        data_frame.columnconfigure(3, weight=1)
        
        # 音频数据
        ttk.Label(data_frame, text="低频音量:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.low_freq_label = ttk.Label(data_frame, text="0.000", font=("Consolas", 10))
        self.low_freq_label.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(data_frame, text="高频音量:").grid(row=0, column=2, sticky=tk.W, padx=(10, 5))
        self.high_freq_label = ttk.Label(data_frame, text="0.000", font=("Consolas", 10))
        self.high_freq_label.grid(row=0, column=3, sticky=tk.W)
        
        # 震动数据
        ttk.Label(data_frame, text="左马达:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.left_motor_label = ttk.Label(data_frame, text="0 (0.0%)", font=("Consolas", 10))
        self.left_motor_label.grid(row=1, column=1, sticky=tk.W)
        
        ttk.Label(data_frame, text="右马达:").grid(row=1, column=2, sticky=tk.W, padx=(10, 5))
        self.right_motor_label = ttk.Label(data_frame, text="0 (0.0%)", font=("Consolas", 10))
        self.right_motor_label.grid(row=1, column=3, sticky=tk.W)
        
        # 图表显示
        self.setup_charts(monitor_frame)
    
    def setup_charts(self, parent):
        """设置图表显示"""
        # 创建matplotlib图表
        self.fig = Figure(figsize=(8, 6), dpi=80)
        
        # 音频波形图
        self.audio_ax = self.fig.add_subplot(2, 1, 1)
        self.audio_ax.set_title("音频频谱分析")
        self.audio_ax.set_ylabel("幅度")
        self.audio_ax.grid(True, alpha=0.3)
        
        # 震动强度图
        self.vibration_ax = self.fig.add_subplot(2, 1, 2)
        self.vibration_ax.set_title("震动强度")
        self.vibration_ax.set_xlabel("时间")
        self.vibration_ax.set_ylabel("强度")
        self.vibration_ax.grid(True, alpha=0.3)
        
        self.fig.tight_layout()
        
        # 嵌入到tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, parent)
        self.canvas.get_tk_widget().grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 初始化图表数据
        self.audio_line_low, = self.audio_ax.plot([], [], 'b-', label='低频', linewidth=2)
        self.audio_line_high, = self.audio_ax.plot([], [], 'r-', label='高频', linewidth=2)
        self.audio_ax.legend()
        
        self.vibration_line_left, = self.vibration_ax.plot([], [], 'b-', label='左马达', linewidth=2)
        self.vibration_line_right, = self.vibration_ax.plot([], [], 'r-', label='右马达', linewidth=2)
        self.vibration_ax.legend()
        
        # 设置初始范围
        self.audio_ax.set_xlim(0, self.max_buffer_size)
        self.audio_ax.set_ylim(0, 1)
        self.vibration_ax.set_xlim(0, self.max_buffer_size)
        self.vibration_ax.set_ylim(0, 1)
    
    def setup_status_bar(self):
        """设置状态栏"""
        status_frame = ttk.Frame(self.root)
        status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=10, pady=(5, 10))
        
        self.status_label = ttk.Label(status_frame, text="就绪")
        self.status_label.pack(side=tk.LEFT)
        
        self.fps_label = ttk.Label(status_frame, text="FPS: 0")
        self.fps_label.pack(side=tk.RIGHT)
    
    def create_parameter_slider(self, parent, label, param_name, min_val, max_val, resolution, row, initial_value):
        """创建参数滑块"""
        ttk.Label(parent, text=f"{label}:").grid(row=row, column=0, sticky=tk.W, pady=2)
        
        var = tk.DoubleVar(value=initial_value)
        slider = ttk.Scale(parent, from_=min_val, to=max_val, variable=var, 
                          orient=tk.HORIZONTAL, length=200)
        slider.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=2)
        
        value_label = ttk.Label(parent, text=f"{initial_value:.3f}")
        value_label.grid(row=row, column=2, sticky=tk.W, pady=2)
        
        # 绑定更新事件
        def update_param(*args):
            value = var.get()
            value_label.config(text=f"{value:.3f}")
            setattr(self.vibration_mapper, param_name, value)
            
            # 特殊处理频率分离点参数
            if param_name == 'frequency_cutoff':
                self.audio_processor.set_filter_cutoff_frequency(value)
        
        var.trace('w', update_param)
        parent.columnconfigure(1, weight=1)
        
        # 保存引用
        setattr(self, f"{param_name}_var", var)
    
    def refresh_devices(self):
        """刷新音频设备列表"""
        try:
            devices = self.audio_processor.get_audio_devices()
            
            # 创建设备显示名称，区分系统音频和麦克风
            device_names = []
            system_audio_count = 0
            for d in devices:
                device_type_indicator = ""
                if d['is_system_audio']:
                    device_type_indicator = " [系统音频]"
                    system_audio_count += 1
                elif d['type'] == 'microphone':
                    device_type_indicator = " [麦克风]"
                else:
                    device_type_indicator = " [输入设备]"
                
                device_names.append(f"{d['index']}: {d['name']}{device_type_indicator}")
            
            self.audio_device_combo['values'] = device_names
            
            # 优先选择系统音频设备
            if device_names:
                default_index = 0
                # 查找第一个系统音频设备
                for i, device in enumerate(devices):
                    if device['is_system_audio']:
                        default_index = i
                        break
                
                self.audio_device_combo.current(default_index)
                # 更新音频处理器的设备
                self.audio_processor.device_index = devices[default_index]['index']
            
            status_msg = f"发现 {len(devices)} 个音频设备"
            if system_audio_count > 0:
                status_msg += f"，其中 {system_audio_count} 个系统音频设备"
            else:
                status_msg += " [注意：未发现系统音频设备，请启用立体声混音]"
            
            self.update_status(status_msg)
            
            # 如果没有系统音频设备，显示帮助信息
            if system_audio_count == 0:
                self._show_system_audio_help()
                
        except Exception as e:
            messagebox.showerror("错误", f"刷新设备失败: {e}")
    
    def _show_system_audio_help(self):
        """显示系统音频设置帮助"""
        help_msg = """
要捕获系统播放的音频（如音乐、游戏声音），需要启用系统音频设备：

Windows 10/11:
1. 右键点击系统托盘的音量图标
2. 选择"打开声音设置"
3. 点击"声音控制面板"
4. 切换到"录制"选项卡
5. 右键空白处，选择"显示禁用的设备"
6. 找到"立体声混音"设备，右键启用
7. 设置为默认录制设备（可选）

替代方案:
- 使用虚拟音频线缆 (VB-Cable)
- 使用OBS虚拟音频输出
- 使用专业音频软件的路由功能

启用后请重新刷新设备列表。
        """
        
        result = messagebox.showinfo("系统音频捕获帮助", help_msg)
        
        # 提供快速打开声音设置的按钮
        if messagebox.askyesno("快速设置", "是否打开Windows声音设置？"):
            try:
                import subprocess
                subprocess.run("ms-settings:sound", shell=True)
            except:
                try:
                    subprocess.run("control mmsys.cpl", shell=True)
                except:
                    pass  # 如果无法打开设置，忽略错误
    
    def on_device_changed(self, event=None):
        """音频设备改变时的处理"""
        try:
            selected_index = self.audio_device_combo.current()
            if selected_index >= 0:
                devices = self.audio_processor.get_audio_devices()
                if selected_index < len(devices):
                    selected_device = devices[selected_index]
                    self.audio_processor.device_index = selected_device['index']
                    
                    # 显示设备类型信息
                    if selected_device['is_system_audio']:
                        self.update_status(f"已选择系统音频设备: {selected_device['name']}")
                    else:
                        self.update_status(f"已选择输入设备: {selected_device['name']}")
        except Exception as e:
            print(f"设备切换错误: {e}")
    
    def toggle_conversion(self):
        """切换音频转换状态"""
        if not self.is_running:
            self.start_conversion()
        else:
            self.stop_conversion()
    
    def start_conversion(self):
        """开始音频转换"""
        try:
            # 启动音频录制
            if not self.audio_processor.start_recording():
                messagebox.showerror("错误", "无法启动音频录制，请检查音频设备")
                return
            
            self.is_running = True
            self.start_button.config(text="停止转换")
            self.update_status("正在运行音频转震动转换...")
            
            # 启动处理线程
            self.processing_thread = threading.Thread(target=self.audio_processing_loop, daemon=True)
            self.processing_thread.start()
            
        except Exception as e:
            messagebox.showerror("错误", f"启动转换失败: {e}")
            self.stop_conversion()
    
    def stop_conversion(self):
        """停止音频转换"""
        self.is_running = False
        self.start_button.config(text="开始转换")
        self.update_status("已停止")
        
        # 停止音频录制
        self.audio_processor.stop_recording()
        
        # 停止震动
        self.vibration_mapper.stop_vibration()
    
    def audio_processing_loop(self):
        """音频处理主循环"""
        fps_counter = 0
        fps_start_time = time.time()
        last_fps_update = fps_start_time
        
        while self.is_running:
            try:
                # 获取音频数据 - 减少timeout时间提高响应性
                audio_data = self.audio_processor.get_latest_audio_data(timeout=0.005)
                if audio_data is None:
                    # 没有数据时短暂休眠，避免空转占用CPU
                    time.sleep(0.001)
                    continue
                
                # 分析音频
                volume_analysis = self.audio_processor.get_volume_analysis(audio_data)
                
                # 映射到震动（传递音频处理器和数据用于高级分析）
                vibration_status = self.vibration_mapper.process_audio_frame(
                    volume_analysis, 
                    self.audio_processor, 
                    audio_data
                )
                
                # 更新数据缓冲区
                self.update_data_buffers(volume_analysis, vibration_status)
                
                # 优化FPS计算 - 每秒更新一次而不是每30帧
                fps_counter += 1
                current_time = time.time()
                if current_time - last_fps_update >= 1.0:  # 每秒更新一次FPS
                    fps = fps_counter / (current_time - fps_start_time)
                    self.root.after_idle(lambda f=fps: self.fps_label.config(text=f"FPS: {f:.1f}"))
                    fps_counter = 0
                    fps_start_time = current_time
                    last_fps_update = current_time
                
                # 移除固定延迟，让处理尽可能快
                # time.sleep(0.01) - 移除这个延迟
                
            except Exception as e:
                print(f"音频处理循环错误: {e}")
                time.sleep(0.001)  # 减少错误时的延迟
    
    def update_data_buffers(self, volume_analysis, vibration_status):
        """更新数据缓冲区"""
        # 音频数据
        audio_data = {
            'low_freq': volume_analysis.get('smoothed_low_rms', 0),
            'high_freq': volume_analysis.get('smoothed_high_rms', 0)
        }
        
        self.audio_data_buffer.append(audio_data)
        if len(self.audio_data_buffer) > self.max_buffer_size:
            self.audio_data_buffer.pop(0)
        
        # 震动数据（保存完整的状态信息用于显示）
        self.vibration_data_buffer.append(vibration_status)
        if len(self.vibration_data_buffer) > self.max_buffer_size:
            self.vibration_data_buffer.pop(0)
    
    def start_monitoring(self):
        """启动实时监控"""
        self.monitoring_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        self.monitoring_thread.start()
    
    def monitoring_loop(self):
        """监控循环，更新GUI显示"""
        last_display_update = 0
        last_chart_update = 0
        display_update_interval = 1/30  # 30Hz数字显示更新
        chart_update_interval = 1/15    # 15Hz图表更新（图表更新消耗更多资源）
        
        while True:
            try:
                if self.is_running and len(self.audio_data_buffer) > 0:
                    current_time = time.time()
                    
                    # 更频繁地更新数字显示
                    if current_time - last_display_update >= display_update_interval:
                        latest_audio = self.audio_data_buffer[-1]
                        latest_vibration = self.vibration_data_buffer[-1]
                        # 使用after_idle减少GUI阻塞
                        self.root.after_idle(lambda a=latest_audio, v=latest_vibration: 
                                           self.update_realtime_display(a, v))
                        last_display_update = current_time
                    
                    # 适中频率更新图表
                    if current_time - last_chart_update >= chart_update_interval:
                        self.root.after_idle(self.update_charts)
                        last_chart_update = current_time
                
                time.sleep(0.016)  # 约60Hz检查频率，比原来的10Hz快得多
                
            except Exception as e:
                print(f"监控循环错误: {e}")
                time.sleep(0.1)
    
    def update_realtime_display(self, audio_data, vibration_data):
        """更新实时数据显示"""
        # 更新音频数据标签
        self.low_freq_label.config(text=f"{audio_data['low_freq']:.3f}")
        self.high_freq_label.config(text=f"{audio_data['high_freq']:.3f}")
        
        # 更新震动数据标签
        left_motor_value = int(vibration_data['left_intensity'] * 65535)
        right_motor_value = int(vibration_data['right_intensity'] * 65535)
        
        self.left_motor_label.config(text=f"{left_motor_value} ({vibration_data['left_intensity']*100:.1f}%)")
        self.right_motor_label.config(text=f"{right_motor_value} ({vibration_data['right_intensity']*100:.1f}%)")
    
    def update_charts(self):
        """更新图表显示"""
        if len(self.audio_data_buffer) < 2:
            return
        
        try:
            # 为了性能，只使用最近的数据点进行绘制
            max_points = min(self.max_buffer_size, len(self.audio_data_buffer))
            
            # 准备数据
            x_data = list(range(max_points))
            low_freq_data = [d['low_freq'] for d in self.audio_data_buffer[-max_points:]]
            high_freq_data = [d['high_freq'] for d in self.audio_data_buffer[-max_points:]]
            
            left_vibration_data = [d['left_intensity'] for d in self.vibration_data_buffer[-max_points:]]
            right_vibration_data = [d['right_intensity'] for d in self.vibration_data_buffer[-max_points:]]
            
            # 更新音频图表
            self.audio_line_low.set_data(x_data, low_freq_data)
            self.audio_line_high.set_data(x_data, high_freq_data)
            
            # 更新震动图表
            self.vibration_line_left.set_data(x_data, left_vibration_data)
            self.vibration_line_right.set_data(x_data, right_vibration_data)
            
            # 优化Y轴调整 - 不要每次都重新计算范围
            if hasattr(self, '_last_axis_update') and time.time() - self._last_axis_update < 1.0:
                # 1秒内不重新调整轴范围，减少计算开销
                pass
            else:
                # 自动调整Y轴范围
                if low_freq_data or high_freq_data:
                    max_audio = max(max(low_freq_data), max(high_freq_data))
                    self.audio_ax.set_ylim(0, max(0.1, max_audio * 1.1))
                
                if left_vibration_data or right_vibration_data:
                    max_vibration = max(max(left_vibration_data), max(right_vibration_data))
                    self.vibration_ax.set_ylim(0, max(0.1, max_vibration * 1.1))
                
                # 调整X轴范围
                self.audio_ax.set_xlim(0, max_points)
                self.vibration_ax.set_xlim(0, max_points)
                
                self._last_axis_update = time.time()
            
            # 使用draw_idle而不是draw以提高性能
            self.canvas.draw_idle()
            
        except Exception as e:
            print(f"更新图表错误: {e}")
    
    def apply_preset(self, event=None):
        """应用预设配置"""
        preset_name = self.preset_var.get()
        if self.vibration_mapper.apply_preset(preset_name):
            # 更新GUI滑块值
            self.update_slider_values_from_mapper()
            self.update_status(f"已应用预设: {preset_name}")
        else:
            messagebox.showerror("错误", f"未知的预设: {preset_name}")
    
    def update_slider_values_from_mapper(self):
        """从映射器更新滑块值"""
        params = self.vibration_mapper.get_parameters()
        for param_name, value in params.items():
            var_name = f"{param_name}_var"
            if hasattr(self, var_name):
                getattr(self, var_name).set(value)
    
    def test_vibration(self):
        """测试震动功能"""
        if not self.controller_manager.vibration_supported:
            messagebox.showwarning("警告", "控制器不支持震动功能")
            return
        
        try:
            # 执行基础震动测试
            self.controller_manager.test_vibration_pattern('basic')
            self.update_status("震动测试完成")
        except Exception as e:
            messagebox.showerror("错误", f"震动测试失败: {e}")
    
    def emergency_stop(self):
        """紧急停止"""
        self.stop_conversion()
        self.controller_manager.emergency_stop()
        self.update_status("紧急停止执行完毕")
    
    def save_configuration(self):
        """保存配置"""
        try:
            config = {
                'vibration_mapper_params': self.vibration_mapper.get_parameters(),
                'audio_processor_params': {
                    'sample_rate': self.audio_processor.sample_rate,
                    'chunk_size': self.audio_processor.chunk_size,
                    'device_index': self.audio_processor.device_index
                },
                'gui_params': {
                    'preset': self.preset_var.get()
                }
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            self.update_status(f"配置已保存到 {self.config_file}")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {e}")
    
    def load_configuration(self):
        """加载配置"""
        if not os.path.exists(self.config_file):
            return
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 应用震动映射参数
            if 'vibration_mapper_params' in config:
                self.vibration_mapper.set_parameters(**config['vibration_mapper_params'])
                self.update_slider_values_from_mapper()
            
            # 应用GUI参数
            if 'gui_params' in config:
                preset = config['gui_params'].get('preset', 'balanced')
                self.preset_var.set(preset)
            
            self.update_status(f"配置已从 {self.config_file} 加载")
            
        except Exception as e:
            print(f"加载配置失败: {e}")
    
    def load_configuration_dialog(self):
        """加载配置对话框"""
        filename = filedialog.askopenfilename(
            title="加载配置文件",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            self.config_file = filename
            self.load_configuration()
    
    def reset_to_defaults(self):
        """重置为默认值"""
        if messagebox.askyesno("确认", "确定要重置所有参数为默认值吗？"):
            self.vibration_mapper.apply_preset('balanced')
            self.preset_var.set('balanced')
            self.update_slider_values_from_mapper()
            self.update_status("已重置为默认值")
    
    def update_status(self, message):
        """更新状态栏"""
        self.status_label.config(text=message)
    
    def update_status_with_vibration_info(self, vibration_status, fps):
        """更新状态栏，包含震动和声音识别信息"""
        status_text = f"处理音频数据 - FPS: {fps:.1f}"
        
        if vibration_status:
            left_intensity = vibration_status.get('left_intensity', 0)
            right_intensity = vibration_status.get('right_intensity', 0)
            sound_type = vibration_status.get('sound_type', 'normal')
            impact_detected = vibration_status.get('impact_detected', False)
            
            status_text += f" | 左马达: {left_intensity:.2f} | 右马达: {right_intensity:.2f}"
            
            # 显示声音类型（如果不是普通声音）
            if sound_type != 'normal':
                sound_type_names = {
                    'explosion': '💥爆炸',
                    'metal_clash': '⚔️金属碰撞', 
                    'gunshot': '🔫枪声',
                    'drum_hit': '🥁鼓声',
                    'glass_break': '💎玻璃破碎'
                }
                display_name = sound_type_names.get(sound_type, sound_type)
                status_text += f" | 声音类型: {display_name}"
            
            # 显示冲击状态
            if impact_detected:
                status_text += " | 🔥冲击检测!"
        
        self.status_label.config(text=status_text)
    
    def run(self):
        """运行GUI主循环"""
        # 初始化设备
        self.refresh_devices()
        
        # 注册关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 启动主循环
        self.root.mainloop()
    
    def on_closing(self):
        """关闭程序时的清理工作"""
        if self.is_running:
            self.stop_conversion()
        
        # 清理资源
        if self.controller_manager:
            self.controller_manager.cleanup()
        
        # 保存配置
        self.save_configuration()
        
        # 关闭窗口
        self.root.destroy()
