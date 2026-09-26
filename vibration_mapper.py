#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
震动映射模块
实现音频信号到手柄震动的映射转换
"""

import numpy as np
import time
import threading
from threading import Lock

class VibrationMapper:
    def __init__(self, controller_manager):
        """
        初始化震动映射器
        
        Args:
            controller_manager: 控制器管理器实例
        """
        self.controller_manager = controller_manager
        
        # 映射参数
        self.low_freq_sensitivity = 1.0      # 低频敏感度
        self.high_freq_sensitivity = 2.5     # 高频敏感度
        self.overall_intensity = 1.0         # 整体强度倍数
        
        # 音量阈值
        self.min_volume_threshold = 0.03     # 最小音量阈值（通用）
        self.max_volume_threshold = 1.0      # 最大音量阈值（通用）
        
        # 分频段阈值
        self.min_low_freq_threshold = 0.15   # 低频最小响应阈值
        self.min_high_freq_threshold = 0.05  # 高频最小响应阈值
        
        # 震动强度范围
        self.min_vibration_intensity = 0.0   # 最小震动强度
        self.max_vibration_intensity = 1.0   # 最大震动强度
        
        # 平滑和响应性参数
        self.smoothing_factor = 0.0          # 平滑因子 (0-1, 越大越平滑)
        self.attack_time = 0.01              # 攻击时间 (秒)
        self.decay_time = 0.10               # 衰减时间 (秒)
        
        # 频率分离点
        self.frequency_cutoff = 400          # Hz
        
        # 频率差增强参数
        self.frequency_difference_factor = 1.0  # 0-1, 增强主导频段，弱化非主导频段
        
        # 高级映射选项
        self.enable_frequency_boost = True      # 启用频率增强
        self.enable_dynamic_range = True        # 启用动态范围压缩
        self.enable_stereo_separation = True    # 启用立体声分离
        self.enable_impact_enhancement = False  # 启用冲击增强
        self.enable_sound_classification = False # 启用声音分类
        self.enable_six_band_mapping = True      # 启用六频段直接震动映射
        self.enable_sfx_gate = True              # 启用统一SFX触觉门控
        self.sfx_gate_threshold = 0.35           # SFX分数门槛
        self.sfx_gate_strength = 0.65            # 门控抑制强度
        self.sfx_gate_floor = 0.20               # 低分声音最低保留比例
        self.band_weights = {
            'sub_bass': 1.00,
            'bass': 0.90,
            'low_mid': 0.45,
            'mid': 0.15,
            'high_mid': 0.55,
            'treble': 0.70
        }
        self.continuous_sound_suppression = 0.75 # 持续稳定声音基础抑制
        self.midrange_dialogue_suppression = 0.30 # 中频/对白额外抑制
        self.transient_preservation = 1.0        # 瞬态/SFX穿透抑制层的程度
        
        # 音频特征增强设置
        self.impact_multiplier = 3.0         # 冲击增强倍数
        self.explosion_bass_boost = 2.5      # 爆炸低频增强
        self.metal_treble_boost = 2.0        # 金属高频增强
        self.impact_duration = 0.15          # 冲击持续时间(秒)
        
        # 声音分类阈值
        self.classification_thresholds = {
            'explosion': {'sub_bass': 0.3, 'bass': 0.2, 'impact_intensity': 0.4},
            'metal_clash': {'high_mid': 0.25, 'treble': 0.2, 'impact_intensity': 0.3},
            'gunshot': {'mid': 0.3, 'high_mid': 0.25, 'impact_intensity': 0.5},
            'drum_hit': {'bass': 0.4, 'low_mid': 0.3, 'impact_intensity': 0.3},
            'glass_break': {'high_mid': 0.4, 'treble': 0.35, 'impact_intensity': 0.2}
        }
        
        # 冲击检测状态
        self.impact_start_time = 0
        self.impact_active = False
        self.previous_audio_data = None
        
        # 内部状态
        self.current_left_intensity = 0.0
        self.current_right_intensity = 0.0
        self.last_update_time = time.time()
        self.envelope_left_intensity = 0.0
        self.envelope_right_intensity = 0.0
        self.last_envelope_time = time.time()
        
        # 使用锁保证线程安全
        self.intensity_lock = Lock()
        
        # 历史数据用于平滑处理
        self.intensity_history = []
        self.history_size = 2
    
    
    def set_parameters(self, **kwargs):
        """设置映射参数"""
        for param, value in kwargs.items():
            if hasattr(self, param):
                setattr(self, param, value)
    
    def get_parameters(self):
        """获取当前映射参数"""
        return {
            'low_freq_sensitivity': self.low_freq_sensitivity,
            'high_freq_sensitivity': self.high_freq_sensitivity,
            'overall_intensity': self.overall_intensity,
            'min_volume_threshold': self.min_volume_threshold,
            'max_volume_threshold': self.max_volume_threshold,
            'min_low_freq_threshold': self.min_low_freq_threshold,
            'min_high_freq_threshold': self.min_high_freq_threshold,
            'min_vibration_intensity': self.min_vibration_intensity,
            'max_vibration_intensity': self.max_vibration_intensity,
            'smoothing_factor': self.smoothing_factor,
            'attack_time': self.attack_time,
            'decay_time': self.decay_time,
            'frequency_cutoff': self.frequency_cutoff,
            'frequency_difference_factor': self.frequency_difference_factor,
            'enable_six_band_mapping': self.enable_six_band_mapping,
            'enable_sfx_gate': self.enable_sfx_gate,
            'sfx_gate_threshold': self.sfx_gate_threshold,
            'sfx_gate_strength': self.sfx_gate_strength,
            'sfx_gate_floor': self.sfx_gate_floor,
            'band_weights': self.band_weights.copy(),
            'continuous_sound_suppression': self.continuous_sound_suppression,
            'midrange_dialogue_suppression': self.midrange_dialogue_suppression,
            'transient_preservation': self.transient_preservation
        }
    
    def normalize_volume(self, volume):
        """标准化音量到0-1范围"""
        # 限制在阈值范围内
        volume = max(self.min_volume_threshold, min(volume, self.max_volume_threshold))
        
        # 标准化到0-1
        normalized = (volume - self.min_volume_threshold) / (self.max_volume_threshold - self.min_volume_threshold)
        
        # 应用动态范围压缩（如果启用）
        if self.enable_dynamic_range:
            # 使用对数压缩增强小音量的响应
            normalized = np.power(normalized, 0.5)  # 平方根压缩
        
        return normalized
    
    def apply_frequency_boost(self, low_intensity, high_intensity):
        """应用频率增强"""
        if not self.enable_frequency_boost:
            return low_intensity, high_intensity
        
        # 对低频和高频应用不同的增强曲线
        # 低频使用对数增强，高频使用线性增强
        enhanced_low = np.power(low_intensity, 0.8)  # 稍微压缩
        enhanced_high = np.power(high_intensity, 0.7)  # 更多压缩，增强响应性
        
        return enhanced_low, enhanced_high
    
    def apply_smoothing(self, left_intensity, right_intensity):
        """应用平滑处理"""
        # 完整平滑处理
        current_time = time.time()
        time_delta = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # 计算平滑系数（基于时间和设置）
        actual_smoothing = min(1.0, self.smoothing_factor * time_delta * 10)  # 时间补偿
        
        # 应用指数平滑
        with self.intensity_lock:
            self.current_left_intensity = (
                self.current_left_intensity * actual_smoothing +
                left_intensity * (1 - actual_smoothing)
            )
            self.current_right_intensity = (
                self.current_right_intensity * actual_smoothing +
                right_intensity * (1 - actual_smoothing)
            )
        
        return self.current_left_intensity, self.current_right_intensity
    
    def apply_frequency_difference(self, left_intensity, right_intensity):
        """应用频率差增强效果"""
        if self.frequency_difference_factor <= 0.0:
            # 无增强，直接返回原值
            return left_intensity, right_intensity
        
        # 计算两个强度的大小关系
        total_intensity = left_intensity + right_intensity
        
        # 如果总强度太小，不进行处理
        if total_intensity < 0.001:
            return left_intensity, right_intensity
        
        # 确定哪个是主导频段
        if left_intensity > right_intensity:
            # 左马达（低频）主导
            dominant_intensity = left_intensity
            secondary_intensity = right_intensity
            left_is_dominant = True
        else:
            # 右马达（高频）主导
            dominant_intensity = right_intensity
            secondary_intensity = left_intensity
            left_is_dominant = False
        
        # 计算增强后的值
        factor = self.frequency_difference_factor
        
        # 主导频段增强：dominant + (secondary * factor)
        enhanced_dominant = dominant_intensity + (secondary_intensity * factor)
        # 次要频段削弱：secondary * (1 - factor)
        enhanced_secondary = secondary_intensity * (1.0 - factor)
        
        # 确保不超过最大值
        enhanced_dominant = min(enhanced_dominant, 1.0)
        enhanced_secondary = max(enhanced_secondary, 0.0)
        
        # 根据哪个是主导频段返回正确的值
        if left_is_dominant:
            return enhanced_dominant, enhanced_secondary
        else:
            return enhanced_secondary, enhanced_dominant
    
    def calculate_attack_decay(self, target_intensity, current_intensity, time_delta):
        """计算攻击和衰减效果"""
        if target_intensity > current_intensity:
            # 攻击阶段 - 快速上升
            rate = 1.0 / max(0.001, self.attack_time)
            change = min(target_intensity - current_intensity, rate * time_delta)
            return current_intensity + change
        else:
            # 衰减阶段 - 缓慢下降
            rate = 1.0 / max(0.001, self.decay_time)
            change = min(current_intensity - target_intensity, rate * time_delta)
            return current_intensity - change
    
    def apply_attack_decay_envelope(self, left_intensity, right_intensity):
        """对最终震动输出应用独立的 Attack/Decay 包络"""
        current_time = time.time()
        time_delta = max(0.0, current_time - self.last_envelope_time)
        self.last_envelope_time = current_time

        target_left = float(np.clip(left_intensity, 0.0, 1.0))
        target_right = float(np.clip(right_intensity, 0.0, 1.0))

        self.envelope_left_intensity = self.calculate_attack_decay(
            target_left, self.envelope_left_intensity, time_delta
        )
        self.envelope_right_intensity = self.calculate_attack_decay(
            target_right, self.envelope_right_intensity, time_delta
        )

        return self.envelope_left_intensity, self.envelope_right_intensity

    def map_audio_to_vibration(self, volume_analysis):
        """
        将音频分析结果映射到震动强度
        
        Args:
            volume_analysis: 音频分析结果字典
            
        Returns:
            tuple: (left_motor_intensity, right_motor_intensity)
        """
        # 获取音频分析数据
        low_freq_volume = volume_analysis.get('smoothed_low_rms', 0)
        high_freq_volume = volume_analysis.get('smoothed_high_rms', 0)
        
        # 应用分频段阈值过滤
        filtered_low = low_freq_volume if low_freq_volume >= self.min_low_freq_threshold else 0.0
        filtered_high = high_freq_volume if high_freq_volume >= self.min_high_freq_threshold else 0.0
        
        # 标准化音量
        normalized_low = self.normalize_volume(filtered_low)
        normalized_high = self.normalize_volume(filtered_high)
        
        # 应用敏感度
        adjusted_low = normalized_low * self.low_freq_sensitivity
        adjusted_high = normalized_high * self.high_freq_sensitivity
        
        # 应用频率增强
        enhanced_low, enhanced_high = self.apply_frequency_boost(adjusted_low, adjusted_high)
        
        # 映射到震动强度范围
        left_intensity = np.clip(
            enhanced_low * self.overall_intensity,
            self.min_vibration_intensity,
            self.max_vibration_intensity
        )
        
        right_intensity = np.clip(
            enhanced_high * self.overall_intensity,
            self.min_vibration_intensity,
            self.max_vibration_intensity
        )
        
        # 应用频率差增强
        enhanced_left, enhanced_right = self.apply_frequency_difference(left_intensity, right_intensity)
        
        # 应用平滑处理
        smoothed_left, smoothed_right = self.apply_smoothing(enhanced_left, enhanced_right)
        
        return smoothed_left, smoothed_right
    
    def map_frequency_bands_to_vibration(self, band_analysis):
        """将六频段能量按权重合成为左右两颗 XInput 马达"""
        if not band_analysis:
            return 0.0, 0.0

        energies = {
            band: max(0.0, float(band_analysis.get(band, {}).get('rms_energy', 0.0)))
            for band in ('sub_bass', 'bass', 'low_mid', 'mid', 'high_mid', 'treble')
        }

        # 左马达偏低频，右马达偏高频；交界频段保留少量交叉馈送。
        left_mix = {
            'sub_bass': 1.00,
            'bass': 1.00,
            'low_mid': 0.75,
            'mid': 0.25,
            'high_mid': 0.05,
            'treble': 0.00
        }
        right_mix = {
            'sub_bass': 0.00,
            'bass': 0.10,
            'low_mid': 0.35,
            'mid': 0.65,
            'high_mid': 1.00,
            'treble': 1.00
        }

        left_energy_sq = 0.0
        right_energy_sq = 0.0
        for band, energy in energies.items():
            weight = max(0.0, float(self.band_weights.get(band, 1.0)))
            weighted_energy = energy * weight
            left_energy_sq += (weighted_energy * left_mix[band]) ** 2
            right_energy_sq += (weighted_energy * right_mix[band]) ** 2

        left_energy = np.sqrt(left_energy_sq)
        right_energy = np.sqrt(right_energy_sq)

        filtered_low = left_energy if left_energy >= self.min_low_freq_threshold else 0.0
        filtered_high = right_energy if right_energy >= self.min_high_freq_threshold else 0.0

        normalized_low = self.normalize_volume(filtered_low)
        normalized_high = self.normalize_volume(filtered_high)

        adjusted_low = normalized_low * self.low_freq_sensitivity
        adjusted_high = normalized_high * self.high_freq_sensitivity
        enhanced_low, enhanced_high = self.apply_frequency_boost(adjusted_low, adjusted_high)

        left_intensity = np.clip(
            enhanced_low * self.overall_intensity,
            self.min_vibration_intensity,
            self.max_vibration_intensity
        )
        right_intensity = np.clip(
            enhanced_high * self.overall_intensity,
            self.min_vibration_intensity,
            self.max_vibration_intensity
        )

        enhanced_left, enhanced_right = self.apply_frequency_difference(
            left_intensity, right_intensity
        )
        return self.apply_smoothing(enhanced_left, enhanced_right)

    def _calculate_sfx_score(self, sound_type, band_analysis, audio_events):
        """计算当前声音是否值得产生触觉的统一SFX分数，并返回可解释特征"""
        default_components = {
            'transient_score': 0.0,
            'impact_score': 0.0,
            'low_ratio': 0.0,
            'high_ratio': 0.0,
            'edge_ratio': 0.0,
            'vocal_ratio': 0.0,
            'steady_score': 1.0,
            'dominant_bonus': 0.0,
            'raw_score': 0.0
        }
        
        if not band_analysis or not audio_events:
            return 1.0, default_components
        
        # 第一帧没有跨帧变化信息，不做门控，避免启动瞬间被误压制
        if not audio_events.get('has_previous_frame', False):
            return 1.0, default_components
        
        energies = {
            name: max(0.0, float(band_analysis.get(name, {}).get('rms_energy', 0.0)))
            for name in ('sub_bass', 'bass', 'low_mid', 'mid', 'high_mid', 'treble')
        }
        total_energy = sum(energies.values())
        if total_energy <= 1e-10:
            return 0.0, default_components
        
        transient_score = float(np.clip(
            audio_events.get(
                'transient_score',
                abs(audio_events.get('energy_change_rate', 0.0)) / 1.5
            ),
            0.0,
            1.0
        ))
        impact_score = float(np.clip(
            audio_events.get('impact_intensity', 0.0), 0.0, 1.0
        ))
        
        low_ratio = float(np.clip(
            (energies['sub_bass'] + energies['bass']) / total_energy, 0.0, 1.0
        ))
        high_ratio = float(np.clip(
            (energies['high_mid'] + energies['treble']) / total_energy, 0.0, 1.0
        ))
        edge_ratio = float(np.clip(max(low_ratio, high_ratio), 0.0, 1.0))
        
        vocal_ratio = float(np.clip(
            (
                energies['low_mid']
                + energies['mid']
                + 0.5 * energies['high_mid']
            ) / total_energy,
            0.0,
            1.0
        ))
        steady_score = 1.0 - transient_score
        
        dominant_band = audio_events.get('dominant_frequency_band', 'mid')
        dominant_bonus = 1.0 if dominant_band in (
            'sub_bass', 'bass', 'high_mid', 'treble'
        ) else 0.25
        
        raw_score = (
            0.45 * transient_score
            + 0.20 * impact_score
            + 0.20 * edge_ratio
            + 0.15 * dominant_bonus
            - 0.25 * steady_score * vocal_ratio
        )
        score = raw_score
        
        # 已识别的典型SFX与明确冲击不应被门控层误杀
        if sound_type != 'normal':
            score = max(score, 0.90)
        if audio_events.get('impact_detected', False):
            score = max(score, 0.95)
        
        components = {
            'transient_score': transient_score,
            'impact_score': impact_score,
            'low_ratio': low_ratio,
            'high_ratio': high_ratio,
            'edge_ratio': edge_ratio,
            'vocal_ratio': vocal_ratio,
            'steady_score': steady_score,
            'dominant_bonus': dominant_bonus,
            'raw_score': float(np.clip(raw_score, 0.0, 1.0))
        }
        return float(np.clip(score, 0.0, 1.0)), components

    def _apply_sfx_haptic_gate(
        self, left_intensity, right_intensity, sound_type, band_analysis, audio_events
    ):
        """根据SFX分数衰减对白/BGM等低触觉价值声音"""
        score, components = self._calculate_sfx_score(
            sound_type, band_analysis, audio_events
        )
        
        if not self.enable_sfx_gate:
            return left_intensity, right_intensity, score, 1.0, components
        
        # 第一帧直接放行
        if not audio_events or not audio_events.get('has_previous_frame', False):
            return left_intensity, right_intensity, score, 1.0, components
        
        threshold = float(np.clip(self.sfx_gate_threshold, 0.0, 0.95))
        strength = float(np.clip(self.sfx_gate_strength, 0.0, 1.0))
        floor = float(np.clip(self.sfx_gate_floor, 0.0, 1.0))
        
        open_amount = float(np.clip(
            (score - threshold) / max(1.0 - threshold, 1e-6), 0.0, 1.0
        ))
        # smoothstep，避免门槛附近发生硬切换
        open_amount = open_amount * open_amount * (3.0 - 2.0 * open_amount)
        
        target_gain = floor + (1.0 - floor) * open_amount
        gate_gain = 1.0 - strength * (1.0 - target_gain)
        
        return (
            left_intensity * gate_gain,
            right_intensity * gate_gain,
            score,
            gate_gain,
            components
        )

    def update_controller_vibration(self, left_intensity, right_intensity, force=False):
        """更新控制器震动"""
        if self.controller_manager:
            # 转换强度到XInput格式 (0-65535)
            left_motor = int(left_intensity * 65535)
            right_motor = int(right_intensity * 65535)
            
            # 发送震动命令
            return self.controller_manager.set_vibration(left_motor, right_motor, force=force)
        return False
    
    def process_audio_frame(self, volume_analysis, audio_processor=None, current_audio_data=None):
        """
        处理单个音频帧
        
        Args:
            volume_analysis: 音频分析结果
            audio_processor: 音频处理器实例（用于高级分析）
            current_audio_data: 当前音频数据（用于特征检测）
            
        Returns:
            dict: 震动状态信息
        """
        # 高级音频特征分析
        band_analysis = None
        audio_events = None
        sound_type = 'normal'
        sfx_score = 1.0
        sfx_gate_gain = 1.0
        sfx_components = {
            'transient_score': 0.0,
            'impact_score': 0.0,
            'low_ratio': 0.0,
            'high_ratio': 0.0,
            'edge_ratio': 0.0,
            'vocal_ratio': 0.0,
            'steady_score': 1.0,
            'dominant_bonus': 0.0,
            'raw_score': 0.0
        }
        
        needs_audio_analysis = (
            self.enable_sound_classification
            or self.enable_impact_enhancement
            or self.enable_six_band_mapping
            or self.enable_sfx_gate
        )
        if audio_processor and current_audio_data is not None and needs_audio_analysis:
            try:
                # 声音分类、六频段映射和SFX门控都需要频段分析
                if (
                    self.enable_sound_classification
                    or self.enable_six_band_mapping
                    or self.enable_sfx_gate
                ):
                    band_analysis = audio_processor.analyze_frequency_bands(current_audio_data)
                
                # 声音分类、冲击增强和SFX门控需要跨帧事件特征
                if (
                    self.enable_sound_classification
                    or self.enable_impact_enhancement
                    or self.enable_sfx_gate
                ):
                    audio_events = audio_processor.detect_audio_events(
                        current_audio_data,
                        self.previous_audio_data,
                        band_analysis=band_analysis
                    )
                
                # 声音分类
                if self.enable_sound_classification and band_analysis and audio_events:
                    sound_type = self._classify_sound_type(band_analysis, audio_events)
                
                # 只有事件检测开启时才维护上一帧，避免无意义的数据复制
                if audio_events is not None and len(current_audio_data) > 0:
                    self.previous_audio_data = current_audio_data.copy()
                    
            except Exception as e:
                print(f"高级音频分析错误: {e}")
        
        # 基础映射：优先使用六频段；关闭后回退到原来的低/高频映射
        if self.enable_sound_classification and band_analysis and audio_events:
            left_intensity, right_intensity = self._intelligent_vibration_mapping(
                sound_type, band_analysis, audio_events, volume_analysis
            )
        elif self.enable_six_band_mapping and band_analysis:
            left_intensity, right_intensity = self.map_frequency_bands_to_vibration(
                band_analysis
            )
        else:
            left_intensity, right_intensity = self.map_audio_to_vibration(volume_analysis)
        
        # 统一SFX触觉门控：不依赖准确分类，先判断“值不值得震”
        if self.enable_sfx_gate and band_analysis and audio_events:
            (
                left_intensity,
                right_intensity,
                sfx_score,
                sfx_gate_gain,
                sfx_components
            ) = self._apply_sfx_haptic_gate(
                left_intensity,
                right_intensity,
                sound_type,
                band_analysis,
                audio_events
            )
        
        # 对持续、非冲击的普通声音做抑制：降低对白/BGM，优先保留瞬态SFX
        if self.enable_sound_classification and band_analysis and audio_events:
            left_intensity, right_intensity = self._apply_continuous_sound_suppression(
                left_intensity, right_intensity, sound_type, band_analysis, audio_events
            )
        
        # 应用冲击增强
        if self.enable_impact_enhancement and audio_events:
            left_intensity, right_intensity = self._apply_impact_enhancement(
                left_intensity, right_intensity, audio_events
            )
        
        # 对最终结果应用 Attack/Decay 包络
        left_intensity, right_intensity = self.apply_attack_decay_envelope(
            left_intensity, right_intensity
        )

        # 更新控制器
        self.update_controller_vibration(left_intensity, right_intensity)
        
        # 返回状态信息
        return {
            'left_intensity': left_intensity,
            'right_intensity': right_intensity,
            'left_motor_value': int(left_intensity * 65535),
            'right_motor_value': int(right_intensity * 65535),
            'input_low_freq': volume_analysis.get('smoothed_low_rms', 0),
            'input_high_freq': volume_analysis.get('smoothed_high_rms', 0),
            'sound_type': sound_type,
            'sfx_score': sfx_score,
            'sfx_gate_gain': sfx_gate_gain,
            'sfx_components': sfx_components,
            'frequency_bands': {
                name: float(band_analysis.get(name, {}).get('rms_energy', 0.0))
                if band_analysis else 0.0
                for name in ('sub_bass', 'bass', 'low_mid', 'mid', 'high_mid', 'treble')
            },
            'impact_detected': audio_events.get('impact_detected', False) if audio_events else False,
            'impact_intensity': audio_events.get('impact_intensity', 0.0) if audio_events else 0.0,
            'transient_detector': {
                'energy_ratio': audio_events.get('energy_ratio', 1.0) if audio_events else 1.0,
                'energy_onset_score': audio_events.get('energy_onset_score', 0.0) if audio_events else 0.0,
                'spectral_flux': audio_events.get('spectral_flux', 0.0) if audio_events else 0.0,
                'spectral_flux_score': audio_events.get('spectral_flux_score', 0.0) if audio_events else 0.0,
                'transient_score': audio_events.get('transient_score', 0.0) if audio_events else 0.0
            },
            'dominant_frequency_band': audio_events.get('dominant_frequency_band', 'mid') if audio_events else 'mid'
        }
    
    def get_current_intensities(self):
        """获取当前震动强度"""
        with self.intensity_lock:
            return self.current_left_intensity, self.current_right_intensity
    
    def stop_vibration(self):
        """停止所有震动"""
        with self.intensity_lock:
            self.current_left_intensity = 0.0
            self.current_right_intensity = 0.0
            self.envelope_left_intensity = 0.0
            self.envelope_right_intensity = 0.0
            self.last_envelope_time = time.time()
        
        if self.controller_manager:
            self.controller_manager.set_vibration(0, 0)
    
    def _classify_sound_type(self, band_analysis, audio_events):
        """基于频谱和事件特征分类声音类型"""
        if not band_analysis or not audio_events:
            return 'normal'
        
        # 获取各频段能量
        sub_bass = band_analysis.get('sub_bass', {}).get('rms_energy', 0)
        bass = band_analysis.get('bass', {}).get('rms_energy', 0)
        low_mid = band_analysis.get('low_mid', {}).get('rms_energy', 0)
        mid = band_analysis.get('mid', {}).get('rms_energy', 0)
        high_mid = band_analysis.get('high_mid', {}).get('rms_energy', 0)
        treble = band_analysis.get('treble', {}).get('rms_energy', 0)
        
        impact_intensity = audio_events.get('impact_intensity', 0)
        dominant_band = audio_events.get('dominant_frequency_band', 'mid')
        
        # 爆炸声检测：超低频+低频主导，高冲击强度
        explosion_score = (sub_bass * 2 + bass * 1.5 + impact_intensity) / 3
        if (explosion_score > self.classification_thresholds['explosion']['sub_bass'] and
            impact_intensity > self.classification_thresholds['explosion']['impact_intensity']):
            return 'explosion'
        
        # 金属碰撞检测：高频+中高频主导，中等冲击
        metal_score = (high_mid * 1.5 + treble * 2 + impact_intensity * 0.8) / 3
        if (metal_score > self.classification_thresholds['metal_clash']['high_mid'] and
            dominant_band in ['high_mid', 'treble']):
            return 'metal_clash'
        
        # 枪声检测：中频+高频突出，极高冲击强度
        gunshot_score = (mid * 1.2 + high_mid * 1.5 + impact_intensity * 2) / 3
        if (gunshot_score > self.classification_thresholds['gunshot']['mid'] and
            impact_intensity > self.classification_thresholds['gunshot']['impact_intensity']):
            return 'gunshot'
        
        # 鼓声检测：低频+中低频主导
        drum_score = (bass * 1.8 + low_mid * 1.3 + impact_intensity) / 3
        if (drum_score > self.classification_thresholds['drum_hit']['bass'] and
            dominant_band in ['bass', 'low_mid']):
            return 'drum_hit'
        
        # 玻璃破碎检测：高频主导，中等冲击
        glass_score = (high_mid * 1.8 + treble * 2.2 + impact_intensity * 0.5) / 3
        if (glass_score > self.classification_thresholds['glass_break']['high_mid'] and
            dominant_band in ['high_mid', 'treble']):
            return 'glass_break'
        
        return 'normal'
    
    def _intelligent_vibration_mapping(self, sound_type, band_analysis, audio_events, volume_analysis):
        """基于声音类型的智能震动映射"""
        
        # 获取基础数据
        low_freq_rms = volume_analysis.get('smoothed_low_rms', 0)
        high_freq_rms = volume_analysis.get('smoothed_high_rms', 0)
        total_rms = volume_analysis.get('smoothed_total_rms', 0)
        
        # 基础映射：六频段开启时以六频段结果作为智能分类的底座
        if self.enable_six_band_mapping and band_analysis:
            base_left, base_right = self.map_frequency_bands_to_vibration(band_analysis)
        else:
            base_left, base_right = self.map_audio_to_vibration(volume_analysis)
        
        # 根据声音类型调整映射
        if sound_type == 'explosion':
            # 爆炸：强化左马达（低频），削弱右马达
            enhanced_left = base_left * self.explosion_bass_boost
            enhanced_right = base_right * 0.3
            
            # 如果有频段分析数据，使用超低频增强
            if band_analysis:
                sub_bass_energy = band_analysis.get('sub_bass', {}).get('rms_energy', 0)
                bass_energy = band_analysis.get('bass', {}).get('rms_energy', 0)
                explosion_intensity = (sub_bass_energy * 2 + bass_energy) / 3
                enhanced_left = max(enhanced_left, explosion_intensity * 3.0)
            
            return enhanced_left, enhanced_right
            
        elif sound_type == 'metal_clash':
            # 金属碰撞：强化右马达（高频），保持左马达
            enhanced_left = base_left * 0.6
            enhanced_right = base_right * self.metal_treble_boost
            
            # 使用高频段数据增强
            if band_analysis:
                high_mid_energy = band_analysis.get('high_mid', {}).get('rms_energy', 0)
                treble_energy = band_analysis.get('treble', {}).get('rms_energy', 0)
                metal_intensity = (high_mid_energy + treble_energy * 1.5) / 2
                enhanced_right = max(enhanced_right, metal_intensity * 2.5)
            
            return enhanced_left, enhanced_right
            
        elif sound_type == 'gunshot':
            # 枪声：快速全频段冲击，偏向右马达
            gunshot_intensity = total_rms * 2.5
            enhanced_left = gunshot_intensity * 0.7
            enhanced_right = gunshot_intensity * 1.0
            return enhanced_left, enhanced_right
            
        elif sound_type == 'drum_hit':
            # 鼓声：强化低频，轻微高频
            enhanced_left = base_left * 2.0
            enhanced_right = base_right * 0.5
            
            # 使用低频段数据
            if band_analysis:
                bass_energy = band_analysis.get('bass', {}).get('rms_energy', 0)
                enhanced_left = max(enhanced_left, bass_energy * 2.5)
            
            return enhanced_left, enhanced_right
            
        elif sound_type == 'glass_break':
            # 玻璃破碎：主要高频，短促尖锐
            enhanced_left = base_left * 0.2
            enhanced_right = base_right * 1.8
            
            # 使用高频段数据，但强度不如金属
            if band_analysis:
                treble_energy = band_analysis.get('treble', {}).get('rms_energy', 0)
                enhanced_right = max(enhanced_right, treble_energy * 1.5)
            
            return enhanced_left, enhanced_right
            
        else:
            # 普通声音：使用标准映射
            return base_left, base_right
    
    def _apply_continuous_sound_suppression(
        self, left_intensity, right_intensity, sound_type, band_analysis, audio_events
    ):
        """抑制持续对白/BGM，并按可调强度保留瞬态和已识别SFX"""
        # 使用联合瞬态检测结果；旧数据缺少该字段时回退到相邻帧能量变化
        transient_score = float(np.clip(
            audio_events.get(
                'transient_score',
                abs(audio_events.get('energy_change_rate', 0.0)) / 1.5
            ),
            0.0,
            1.0
        ))
        if sound_type != 'normal' or audio_events.get('impact_detected', False):
            transient_score = 1.0
        
        # transient_preservation=1 保持瞬态完全穿透；=0 则不提供额外保护
        steady_score = float(np.clip(
            1.0 - self.transient_preservation * transient_score, 0.0, 1.0
        ))
        
        # 人声/旋律通常集中在中频；中频占比越高，抑制越强
        energies = {
            name: band_analysis.get(name, {}).get('rms_energy', 0.0)
            for name in ('sub_bass', 'bass', 'low_mid', 'mid', 'high_mid', 'treble')
        }
        total_energy = sum(energies.values())
        if total_energy <= 1e-10:
            return left_intensity, right_intensity
        
        mid_energy = energies['low_mid'] + energies['mid'] + energies['high_mid']
        mid_ratio = float(np.clip(mid_energy / total_energy, 0.0, 1.0))
        
        # 基础抑制负责持续稳定声音；额外中频抑制负责对白/旋律密集区域。
        # 默认 0.75 / 0.30 与上一版的默认曲线保持近似一致。
        base_suppression = self.continuous_sound_suppression * steady_score * 0.6
        dialogue_suppression = (
            self.midrange_dialogue_suppression * steady_score * mid_ratio
        )
        suppression = float(np.clip(
            base_suppression + dialogue_suppression, 0.0, 0.9
        ))
        keep = 1.0 - suppression
        
        return left_intensity * keep, right_intensity * keep

    def _apply_impact_enhancement(self, left_intensity, right_intensity, audio_events):
        """应用冲击增强效果"""
        if not audio_events.get('impact_detected', False):
            # 如果冲击已过期，逐渐减弱增强效果
            if self.impact_active:
                current_time = time.time()
                time_since_impact = current_time - self.impact_start_time
                if time_since_impact > self.impact_duration:
                    self.impact_active = False
            return left_intensity, right_intensity
        
        # 检测到新冲击
        current_time = time.time()
        if not self.impact_active:
            self.impact_active = True
            self.impact_start_time = current_time
        
        # 计算冲击增强系数
        impact_intensity = audio_events.get('impact_intensity', 0.5)
        time_since_impact = current_time - self.impact_start_time
        
        # 冲击衰减曲线（指数衰减）
        if time_since_impact < self.impact_duration:
            decay_factor = np.exp(-time_since_impact / (self.impact_duration / 3))
            enhancement = impact_intensity * self.impact_multiplier * decay_factor
            
            # 应用增强
            enhanced_left = left_intensity + (left_intensity * enhancement)
            enhanced_right = right_intensity + (right_intensity * enhancement)
            
            # 确保不超过最大值
            enhanced_left = min(enhanced_left, 1.0)
            enhanced_right = min(enhanced_right, 1.0)
            
            return enhanced_left, enhanced_right
        else:
            self.impact_active = False
            
        return left_intensity, right_intensity

    def set_impact_settings(self, multiplier=3.0, duration=0.15):
        """设置冲击增强参数"""
        self.impact_multiplier = multiplier
        self.impact_duration = duration
        
    def set_sound_type_boosts(self, explosion_boost=2.5, metal_boost=2.0):
        """设置不同声音类型的增强倍数"""
        self.explosion_bass_boost = explosion_boost
        self.metal_treble_boost = metal_boost
    
    def get_current_sound_analysis(self):
        """获取当前声音分析结果"""
        if self.intensity_history:
            latest = self.intensity_history[-1]
            return {
                'sound_type': latest.get('sound_type', 'normal'),
                'impact_active': self.impact_active,
                'time_since_last_impact': time.time() - self.impact_start_time if self.impact_active else 0
            }
        return {'sound_type': 'normal', 'impact_active': False, 'time_since_last_impact': 0}

    def test_vibration_mapping(self, test_volume_low=0.5, test_volume_high=0.5):
        """测试震动映射"""
        test_analysis = {
            'smoothed_low_rms': test_volume_low,
            'smoothed_high_rms': test_volume_high,
            'total_rms': (test_volume_low + test_volume_high) / 2
        }
        
        return self.map_audio_to_vibration(test_analysis)
