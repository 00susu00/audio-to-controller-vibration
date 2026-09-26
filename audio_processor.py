#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频处理模块
实现实时音频采集、频谱分析和信号处理
"""

import pyaudio
import numpy as np
from scipy import signal
from scipy.fft import fft
import threading
import queue
import time

class AudioProcessor:
    def __init__(self, sample_rate=44100, chunk_size=1024, device_index=None):
        """
        初始化音频处理器
        
        Args:
            sample_rate: 采样率，默认44100Hz
            chunk_size: 音频块大小，默认1024（减小以降低延迟）
            device_index: 音频设备索引，None为默认设备
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.device_index = device_index
        
        # 音频流相关
        self.audio = None
        self.stream = None
        self.is_recording = False
        
        # 数据队列 - 减小队列大小以降低延迟
        self.audio_queue = queue.Queue(maxsize=3)
        self.volume_window_size = 3
        self.impact_energy_threshold = 5.0
        
        # 瞬态检测状态：短时能量基线 + 频谱变化基线
        self.event_energy_baseline = None
        self.event_flux_baseline = None
        self.event_prev_spectrum = None
        self.event_energy_alpha = 0.08
        self.event_flux_alpha = 0.10
        
        # 频谱分析参数
        self.window = np.hanning(chunk_size)
        
        # 多频段滤波器设置（用于精细频率分析）
        self.frequency_bands = {
            'sub_bass': (20, 60),      # 超低频：爆炸、雷声
            'bass': (60, 200),         # 低频：打击乐、低音
            'low_mid': (200, 500),     # 中低频：人声、吉他
            'mid': (500, 2000),        # 中频：人声主体
            'high_mid': (2000, 6000),  # 中高频：清晰度、细节
            'treble': (6000, 16000)    # 高频：金属声、尖锐音
        }
        
        # 各频段能量包络的Attack/Decay时间常数（秒）。
        # 低频需要更长观察时间，高频则保持更快响应。
        self.band_energy_time_constants = {
            'sub_bass': (0.045, 0.140),
            'bass': (0.030, 0.100),
            'low_mid': (0.020, 0.070),
            'mid': (0.015, 0.050),
            'high_mid': (0.010, 0.035),
            'treble': (0.008, 0.025)
        }
        self.band_energy_power = {
            band_name: None for band_name in self.frequency_bands
        }
        
        # 为每个频段创建适合实时流处理的SOS滤波器
        self.band_filters = {}
        for band_name, (low_freq, high_freq) in self.frequency_bands.items():
            self.band_filters[band_name] = self._create_bandpass_filter(low_freq, high_freq)
        
        # 简单低通/高通也使用SOS，避免每个音频块独立filtfilt产生边界伪影
        self.lowpass_filter = self._create_lowpass_filter(300)
        self.highpass_filter = self._create_highpass_filter(300)
        self._reset_filter_states()
        
        # 音量分析窗口
        self.volume_buffer = []
        
        
    def _reset_event_detection_state(self):
        """重置瞬态检测器的历史状态"""
        self.event_energy_baseline = None
        self.event_flux_baseline = None
        self.event_prev_spectrum = None
    
    def _reset_filter_states(self):
        """重置所有实时SOS滤波器与频段能量包络状态"""
        self.lowpass_filter_state = None
        self.highpass_filter_state = None
        self.band_filter_states = {
            band_name: None for band_name in self.band_filters
        }
        self.band_energy_power = {
            band_name: None for band_name in self.frequency_bands
        }
    
    def _smooth_band_energy(self, band_name, instant_power, frame_count):
        """按频段时间常数平滑功率，低频长观察、高频快响应"""
        previous_power = self.band_energy_power.get(band_name)
        if previous_power is None:
            self.band_energy_power[band_name] = instant_power
            return instant_power
        
        attack_tau, decay_tau = self.band_energy_time_constants[band_name]
        tau = attack_tau if instant_power >= previous_power else decay_tau
        duration = max(float(frame_count) / float(self.sample_rate), 1e-6)
        alpha = 1.0 - np.exp(-duration / max(tau, 1e-6))
        
        smoothed_power = (
            previous_power
            + alpha * (instant_power - previous_power)
        )
        self.band_energy_power[band_name] = smoothed_power
        return smoothed_power
    
    def _apply_stateful_sos_filter(self, sos, audio_data, state):
        """对连续音频块应用有状态SOS滤波"""
        if audio_data is None or len(audio_data) == 0:
            return np.asarray(audio_data), state
        
        if state is None:
            # 以首个样本初始化稳态，降低在流启动/切换设备时的滤波器瞬态
            state = signal.sosfilt_zi(sos) * float(audio_data[0])
        
        filtered, new_state = signal.sosfilt(sos, audio_data, zi=state)
        return filtered, new_state
    
    def _calculate_spectral_flux(self, audio_data):
        """计算归一化正向频谱通量，返回(通量, 是否存在上一帧频谱)"""
        if audio_data is None or len(audio_data) < 4:
            return 0.0, False
        
        window = np.hanning(len(audio_data))
        spectrum = np.abs(np.fft.rfft(audio_data * window))
        spectrum = spectrum / (np.sum(spectrum) + 1e-12)
        
        if (
            self.event_prev_spectrum is None
            or len(self.event_prev_spectrum) != len(spectrum)
        ):
            self.event_prev_spectrum = spectrum
            return 0.0, False
        
        positive_change = np.maximum(spectrum - self.event_prev_spectrum, 0.0)
        spectral_flux = float(np.sum(positive_change))
        self.event_prev_spectrum = spectrum
        return spectral_flux, True
    
    def _create_lowpass_filter(self, cutoff_freq):
        """创建低通SOS滤波器"""
        nyquist = self.sample_rate / 2
        normalized_cutoff = cutoff_freq / nyquist
        return signal.butter(4, normalized_cutoff, btype='low', output='sos')
    
    def _create_highpass_filter(self, cutoff_freq):
        """创建高通SOS滤波器"""
        nyquist = self.sample_rate / 2
        normalized_cutoff = cutoff_freq / nyquist
        return signal.butter(4, normalized_cutoff, btype='high', output='sos')
    
    def _create_bandpass_filter(self, low_freq, high_freq):
        """创建带通SOS滤波器"""
        nyquist = self.sample_rate / 2
        low_normalized = low_freq / nyquist
        high_normalized = high_freq / nyquist
        
        # 确保频率在有效范围内
        low_normalized = max(0.001, min(0.999, low_normalized))
        high_normalized = max(0.001, min(0.999, high_normalized))
        
        if low_normalized >= high_normalized:
            high_normalized = min(0.999, low_normalized + 0.01)
        
        return signal.butter(
            4,
            [low_normalized, high_normalized],
            btype='band',
            output='sos'
        )
    
    def get_audio_devices(self):
        """获取可用的音频设备列表"""
        if not self.audio:
            self.audio = pyaudio.PyAudio()
        
        devices = []
        for i in range(self.audio.get_device_count()):
            device_info = self.audio.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:  # 只显示输入设备
                device_name = device_info['name']
                device_type = self._classify_device_type(device_name)
                
                devices.append({
                    'index': i,
                    'name': device_name,
                    'type': device_type,
                    'channels': device_info['maxInputChannels'],
                    'sample_rate': device_info['defaultSampleRate'],
                    'is_system_audio': device_type in ['stereo_mix', 'what_you_hear', 'loopback']
                })
        
        # 按类型排序：系统音频设备在前
        devices.sort(key=lambda x: (0 if x['is_system_audio'] else 1, x['name']))
        return devices
    
    def _classify_device_type(self, device_name):
        """分类设备类型"""
        device_name_lower = device_name.lower()
        
        # 系统音频捕获设备的常见名称
        system_audio_keywords = [
            'stereo mix', '立体声混音', 'stereomix',
            'what you hear', 'what u hear', 'wave out mix',
            'sum', 'loopback', '您听到的声音',
            'speakers', '扬声器', 'output', '输出',
            'playback', '播放', 'render', '呈现'
        ]
        
        microphone_keywords = [
            'microphone', 'mic', '麦克风', '话筒',
            'input', '输入', 'capture', '捕获'
        ]
        
        for keyword in system_audio_keywords:
            if keyword in device_name_lower:
                if 'stereo mix' in device_name_lower or '立体声混音' in device_name_lower:
                    return 'stereo_mix'
                elif 'what you hear' in device_name_lower or '您听到的声音' in device_name_lower:
                    return 'what_you_hear'
                else:
                    return 'loopback'
        
        for keyword in microphone_keywords:
            if keyword in device_name_lower:
                return 'microphone'
        
        return 'unknown'
    
    def start_recording(self, callback=None):
        """开始音频录制"""
        if self.is_recording:
            return False
        
        try:
            self._reset_event_detection_state()
            self._reset_filter_states()
            
            if not self.audio:
                self.audio = pyaudio.PyAudio()
            
            self.stream = self.audio.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback if callback is None else callback
            )
            
            self.stream.start_stream()
            self.is_recording = True
            return True
            
        except Exception as e:
            print(f"启动音频录制失败: {e}")
            return False
    
    def stop_recording(self):
        """停止音频录制"""
        if not self.is_recording:
            return
        
        self.is_recording = False
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        if self.audio:
            self.audio.terminate()
            self.audio = None
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """音频回调函数"""
        if status:
            print(f"音频状态: {status}")
        
        try:
            # 将音频数据添加到队列
            audio_data = np.frombuffer(in_data, dtype=np.float32)
            # 标准模式
            if not self.audio_queue.full():
                self.audio_queue.put(audio_data)
        except Exception as e:
            print(f"音频回调错误: {e}")
        
        return (in_data, pyaudio.paContinue)
    
    def get_latest_audio_data(self, timeout=0.1):
        """获取最新的音频数据"""
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def analyze_frequency_spectrum(self, audio_data):
        """分析音频数据的频谱"""
        # 应用窗口函数
        windowed_data = audio_data * self.window[:len(audio_data)]
        
        # FFT变换
        fft_data = fft(windowed_data)
        magnitude = np.abs(fft_data[:len(fft_data)//2])  # 只取正频率部分
        
        # 频率轴
        freqs = np.fft.fftfreq(len(windowed_data), 1/self.sample_rate)[:len(magnitude)]
        
        return freqs, magnitude
    
    def separate_frequency_bands(self, audio_data):
        """使用有状态SOS滤波器连续分离低频和高频信号"""
        low_freq_signal, self.lowpass_filter_state = self._apply_stateful_sos_filter(
            self.lowpass_filter,
            audio_data,
            self.lowpass_filter_state
        )
        high_freq_signal, self.highpass_filter_state = self._apply_stateful_sos_filter(
            self.highpass_filter,
            audio_data,
            self.highpass_filter_state
        )
        return low_freq_signal, high_freq_signal
    
    
    def analyze_frequency_bands(self, audio_data):
        """使用跨音频块保持状态的SOS滤波器分析六个频段"""
        band_analysis = {}
        
        for band_name, sos in self.band_filters.items():
            try:
                band_signal, new_state = self._apply_stateful_sos_filter(
                    sos,
                    audio_data,
                    self.band_filter_states.get(band_name)
                )
                self.band_filter_states[band_name] = new_state
                
                # 当前块的瞬时功率/RMS
                instant_power = float(np.mean(band_signal**2))
                instant_rms_energy = float(np.sqrt(max(instant_power, 0.0)))
                peak_energy = float(np.max(np.abs(band_signal)))
                
                # 使用各频段不同时间常数平滑功率，再转回RMS。
                # 这样20–60Hz不会被11.6ms短块的相位位置强烈影响，
                # 高频仍保持较快的触觉响应。
                smoothed_power = self._smooth_band_energy(
                    band_name,
                    instant_power,
                    len(audio_data)
                )
                rms_energy = float(np.sqrt(max(smoothed_power, 0.0)))
                
                # 保留原有频谱特征输出
                spectral_centroid = self._calculate_spectral_centroid(band_signal)
                spectral_rolloff = self._calculate_spectral_rolloff(band_signal)
                
                band_analysis[band_name] = {
                    'rms_energy': rms_energy,
                    'instant_rms_energy': instant_rms_energy,
                    'peak_energy': peak_energy,
                    'spectral_centroid': spectral_centroid,
                    'spectral_rolloff': spectral_rolloff,
                    'frequency_range': self.frequency_bands[band_name]
                }
                
            except Exception as e:
                print(f"频段 {band_name} 实时滤波错误: {e}")
                band_analysis[band_name] = {
                    'rms_energy': 0.0,
                    'instant_rms_energy': 0.0,
                    'peak_energy': 0.0,
                    'spectral_centroid': 0.0,
                    'spectral_rolloff': 0.0,
                    'frequency_range': self.frequency_bands[band_name]
                }
        
        return band_analysis
    
    
    def _calculate_spectral_centroid(self, audio_data):
        """计算频谱质心（音色亮度指标）"""
        if len(audio_data) < 4:
            return 0.0
            
        try:
            # FFT分析
            fft_data = np.fft.fft(audio_data)
            magnitude = np.abs(fft_data[:len(fft_data)//2])
            freqs = np.fft.fftfreq(len(audio_data), 1/self.sample_rate)[:len(magnitude)]
            
            # 计算频谱质心
            if np.sum(magnitude) > 0:
                centroid = np.sum(freqs * magnitude) / np.sum(magnitude)
                return centroid
            else:
                return 0.0
        except:
            return 0.0
    
    def _calculate_spectral_rolloff(self, audio_data):
        """计算频谱滚降点（85%能量所在的频率）"""
        if len(audio_data) < 4:
            return 0.0
            
        try:
            fft_data = np.fft.fft(audio_data)
            magnitude = np.abs(fft_data[:len(fft_data)//2])
            freqs = np.fft.fftfreq(len(audio_data), 1/self.sample_rate)[:len(magnitude)]
            
            # 计算累积能量
            total_energy = np.sum(magnitude**2)
            if total_energy == 0:
                return 0.0
                
            cumulative_energy = np.cumsum(magnitude**2)
            rolloff_idx = np.where(cumulative_energy >= 0.85 * total_energy)[0]
            
            if len(rolloff_idx) > 0:
                return freqs[rolloff_idx[0]]
            else:
                return freqs[-1]
        except:
            return 0.0
    
    def detect_audio_events(self, audio_data, previous_data=None, band_analysis=None):
        """使用EMA能量基线与频谱通量联合检测瞬态/冲击"""
        events = {
            'impact_detected': False,
            'impact_intensity': 0.0,
            'frequency_shift': 0.0,
            'energy_change_rate': 0.0,
            'energy_ratio': 1.0,
            'energy_onset_score': 0.0,
            'spectral_flux': 0.0,
            'spectral_flux_score': 0.0,
            'transient_score': 0.0,
            'dominant_frequency_band': 'mid',
            'has_previous_frame': False
        }
        
        try:
            current_energy = float(np.mean(audio_data**2))
            has_previous_audio = (
                previous_data is not None
                and len(previous_data) == len(audio_data)
            )
            
            # 先基于历史EMA计算能量突增，随后再更新基线，避免瞬态污染参考值
            if self.event_energy_baseline is None:
                self.event_energy_baseline = current_energy
                energy_ratio = 1.0
                energy_onset_score = 0.0
            else:
                baseline = max(self.event_energy_baseline, 1e-10)
                energy_ratio = current_energy / baseline
                threshold = max(float(self.impact_energy_threshold), 1.01)
                energy_onset_score = float(np.clip(
                    np.log(max(energy_ratio, 1.0)) / np.log(threshold),
                    0.0,
                    1.0
                ))
                
                # 强瞬态期间让基线慢速跟随，普通声音则正常EMA跟随
                alpha = self.event_energy_alpha
                if energy_ratio > 1.5:
                    alpha *= 0.20
                self.event_energy_baseline = (
                    (1.0 - alpha) * self.event_energy_baseline
                    + alpha * current_energy
                )
            
            events['energy_ratio'] = float(energy_ratio)
            events['energy_onset_score'] = energy_onset_score
            
            # 保留相邻帧能量变化，兼容现有监控/逻辑
            if has_previous_audio:
                previous_energy = float(np.mean(previous_data**2))
                previous_ratio = current_energy / max(previous_energy, 1e-10)
                events['energy_change_rate'] = previous_ratio - 1.0
            
            # 频谱通量用于捕捉“音色/频谱突然变化”，弥补单纯音量比值的不足
            spectral_flux, has_previous_spectrum = self._calculate_spectral_flux(audio_data)
            events['spectral_flux'] = spectral_flux
            
            if has_previous_spectrum:
                if self.event_flux_baseline is None:
                    self.event_flux_baseline = spectral_flux
                    spectral_flux_score = 0.0
                else:
                    flux_reference = max(self.event_flux_baseline, 0.015)
                    spectral_flux_score = float(np.clip(
                        (spectral_flux - self.event_flux_baseline)
                        / (flux_reference * 2.0),
                        0.0,
                        1.0
                    ))
                    
                    flux_alpha = self.event_flux_alpha
                    if spectral_flux_score > 0.6:
                        flux_alpha *= 0.25
                    self.event_flux_baseline = (
                        (1.0 - flux_alpha) * self.event_flux_baseline
                        + flux_alpha * spectral_flux
                    )
            else:
                spectral_flux_score = 0.0
            
            events['spectral_flux_score'] = spectral_flux_score
            events['has_previous_frame'] = has_previous_audio and has_previous_spectrum
            
            # 联合瞬态分数：能量突增为主，频谱突变为辅
            transient_score = float(np.clip(
                0.70 * energy_onset_score + 0.30 * spectral_flux_score,
                0.0,
                1.0
            ))
            events['transient_score'] = transient_score
            
            # 强能量突增直接判定冲击；联合特征可捕捉较弱但很尖锐的SFX
            hard_energy_impact = energy_ratio > max(self.impact_energy_threshold, 1.01)
            combined_impact = transient_score > 0.72 and energy_ratio > 1.35
            spectral_impact = spectral_flux_score > 0.90 and energy_ratio > 1.15
            
            if events['has_previous_frame'] and (
                hard_energy_impact or combined_impact or spectral_impact
            ):
                events['impact_detected'] = True
                events['impact_intensity'] = float(np.clip(
                    max(energy_onset_score, transient_score),
                    0.0,
                    1.0
                ))
            
            # 分析频段分布，找出主导频段；已有结果时直接复用，避免重复滤波
            if band_analysis is None:
                band_analysis = self.analyze_frequency_bands(audio_data)
            max_energy = 0.0
            dominant_band = 'mid'
            
            for band_name, analysis in band_analysis.items():
                if analysis['rms_energy'] > max_energy:
                    max_energy = analysis['rms_energy']
                    dominant_band = band_name
            
            events['dominant_frequency_band'] = dominant_band
            
            # 计算频率偏移（高频vs低频的比例）
            high_energy = (
                band_analysis.get('high_mid', {}).get('rms_energy', 0)
                + band_analysis.get('treble', {}).get('rms_energy', 0)
            )
            low_energy = (
                band_analysis.get('sub_bass', {}).get('rms_energy', 0)
                + band_analysis.get('bass', {}).get('rms_energy', 0)
            )
            
            if low_energy + high_energy > 1e-10:
                events['frequency_shift'] = (
                    (high_energy - low_energy) / (high_energy + low_energy)
                )
            
        except Exception as e:
            print(f"音频事件检测错误: {e}")
        
        return events
    
    def calculate_rms_volume(self, audio_data):
        """计算RMS音量"""
        return np.sqrt(np.mean(audio_data**2))
    
    def calculate_peak_volume(self, audio_data):
        """计算峰值音量"""
        return np.max(np.abs(audio_data))
    
    def get_volume_analysis(self, audio_data):
        """获取音量分析结果"""
        rms_volume = self.calculate_rms_volume(audio_data)
        peak_volume = self.calculate_peak_volume(audio_data)
        
        # 分离频段并分析音量
        low_freq_signal, high_freq_signal = self.separate_frequency_bands(audio_data)
        
        low_freq_rms = self.calculate_rms_volume(low_freq_signal)
        high_freq_rms = self.calculate_rms_volume(high_freq_signal)
        
        # 更新音量缓冲区（用于平滑处理）
        self.volume_buffer.append({
            'total_rms': rms_volume,
            'total_peak': peak_volume,
            'low_freq_rms': low_freq_rms,
            'high_freq_rms': high_freq_rms
        })
        
        # 保持缓冲区大小
        if len(self.volume_buffer) > self.volume_window_size:
            self.volume_buffer.pop(0)
        
        # 计算平滑后的音量值
        if len(self.volume_buffer) > 0:
            avg_total_rms = np.mean([v['total_rms'] for v in self.volume_buffer])
            avg_low_rms = np.mean([v['low_freq_rms'] for v in self.volume_buffer])
            avg_high_rms = np.mean([v['high_freq_rms'] for v in self.volume_buffer])
            
            return {
                'total_rms': rms_volume,
                'total_peak': peak_volume,
                'low_freq_rms': low_freq_rms,
                'high_freq_rms': high_freq_rms,
                'smoothed_total_rms': avg_total_rms,
                'smoothed_low_rms': avg_low_rms,
                'smoothed_high_rms': avg_high_rms
            }
        
        return {
            'total_rms': rms_volume,
            'total_peak': peak_volume,
            'low_freq_rms': low_freq_rms,
            'high_freq_rms': high_freq_rms,
            'smoothed_total_rms': rms_volume,
            'smoothed_low_rms': low_freq_rms,
            'smoothed_high_rms': high_freq_rms
        }
    
    def set_filter_cutoff_frequency(self, cutoff_freq):
        """设置滤波器截止频率，并重置对应实时滤波状态"""
        self.lowpass_filter = self._create_lowpass_filter(cutoff_freq)
        self.highpass_filter = self._create_highpass_filter(cutoff_freq)
        self.lowpass_filter_state = None
        self.highpass_filter_state = None

    def set_impact_energy_threshold(self, threshold):
        """设置冲击检测的能量倍数阈值"""
        self.impact_energy_threshold = max(1.01, float(threshold))
