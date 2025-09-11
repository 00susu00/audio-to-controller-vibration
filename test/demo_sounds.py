#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能震动测试演示程序
生成不同类型的测试音频，展示声音识别和差异化震动效果
"""

import numpy as np
import pyaudio
import time
import threading
import argparse
from audio_processor import AudioProcessor
from vibration_mapper import VibrationMapper
from controller_manager import ControllerManager

class SoundGenerator:
    """测试声音生成器"""
    
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.audio = pyaudio.PyAudio()
        
    def generate_explosion_sound(self, duration=2.0):
        """生成爆炸声：超低频主导 + 瞬时冲击"""
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # 超低频成分 (20-60Hz)
        sub_bass = np.sin(2 * np.pi * 35 * t) * 0.8
        
        # 低频成分 (60-200Hz)
        bass = np.sin(2 * np.pi * 120 * t) * 0.6
        
        # 噪声成分模拟爆炸质感
        noise = np.random.normal(0, 0.3, len(t))
        
        # 指数衰减包络
        envelope = np.exp(-t * 2)
        
        # 合成爆炸声
        explosion = (sub_bass + bass + noise) * envelope
        
        # 添加瞬时冲击
        impact_samples = int(0.05 * self.sample_rate)  # 50ms冲击
        explosion[:impact_samples] *= 3.0
        
        return np.clip(explosion, -1.0, 1.0).astype(np.float32)
    
    def generate_metal_clash_sound(self, duration=1.0):
        """生成金属碰撞声：高频主导 + 短促冲击"""
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # 高频金属谐波 (2000-8000Hz)
        metal1 = np.sin(2 * np.pi * 2800 * t) * 0.4
        metal2 = np.sin(2 * np.pi * 4200 * t) * 0.3
        metal3 = np.sin(2 * np.pi * 6800 * t) * 0.2
        
        # 高频噪声模拟金属摩擦
        high_noise = np.random.normal(0, 0.2, len(t))
        high_noise = np.convolve(high_noise, [0.1, 0.8, 0.1], mode='same')  # 简单高通滤波
        
        # 快速衰减包络
        envelope = np.exp(-t * 8)
        
        # 合成金属碰撞声
        metal_clash = (metal1 + metal2 + metal3 + high_noise) * envelope
        
        return np.clip(metal_clash, -1.0, 1.0).astype(np.float32)
    
    def generate_gunshot_sound(self, duration=0.5):
        """生成枪声：中高频突发 + 极强冲击"""
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # 中频成分 (500-2000Hz)
        mid_freq = np.sin(2 * np.pi * 1200 * t) * 0.5
        
        # 高频成分 (2000-8000Hz)
        high_freq = np.sin(2 * np.pi * 3600 * t) * 0.4
        
        # 白噪声模拟爆破声
        noise = np.random.normal(0, 0.6, len(t))
        
        # 极快衰减包络
        envelope = np.exp(-t * 15)
        
        # 合成枪声
        gunshot = (mid_freq + high_freq + noise) * envelope
        
        # 添加极强瞬时冲击
        impact_samples = int(0.02 * self.sample_rate)  # 20ms强冲击
        gunshot[:impact_samples] *= 5.0
        
        return np.clip(gunshot, -1.0, 1.0).astype(np.float32)
    
    def generate_drum_hit_sound(self, duration=1.5):
        """生成鼓声：低频主导 + 中等冲击"""
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # 低频鼓声 (60-200Hz)
        drum_fundamental = np.sin(2 * np.pi * 80 * t) * 0.7
        
        # 低频谐波
        drum_harmonic = np.sin(2 * np.pi * 160 * t) * 0.3
        
        # 中低频细节 (200-500Hz)
        mid_detail = np.sin(2 * np.pi * 300 * t) * 0.2
        
        # 鼓皮噪声
        drum_noise = np.random.normal(0, 0.1, len(t))
        
        # 鼓声包络
        envelope = np.exp(-t * 1.5)
        
        # 合成鼓声
        drum_hit = (drum_fundamental + drum_harmonic + mid_detail + drum_noise) * envelope
        
        return np.clip(drum_hit, -1.0, 1.0).astype(np.float32)
    
    def generate_glass_break_sound(self, duration=0.8):
        """生成玻璃破碎声：高频尖锐 + 细碎冲击"""
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # 高频尖锐声 (4000-12000Hz)
        glass1 = np.sin(2 * np.pi * 6000 * t) * 0.4
        glass2 = np.sin(2 * np.pi * 8500 * t) * 0.3
        glass3 = np.sin(2 * np.pi * 11000 * t) * 0.2
        
        # 高频随机噪声模拟碎片
        fragments = np.random.normal(0, 0.3, len(t))
        # 简单高通滤波
        fragments = np.convolve(fragments, [-0.1, 0.2, -0.1], mode='same')
        
        # 分段衰减包络模拟破碎过程
        envelope = np.exp(-t * 3) + np.exp(-(t-0.1) * 8) * 0.5
        
        # 合成玻璃破碎声
        glass_break = (glass1 + glass2 + glass3 + fragments) * envelope
        
        return np.clip(glass_break, -1.0, 1.0).astype(np.float32)
    
    def play_sound(self, audio_data, volume=0.8):
        """播放生成的声音"""
        try:
            # 调整音量
            audio_data = audio_data * volume
            
            # 播放音频
            stream = self.audio.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=self.sample_rate,
                output=True
            )
            
            # 分块播放以避免延迟
            chunk_size = 1024
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i+chunk_size]
                stream.write(chunk.tobytes())
            
            stream.close()
            
        except Exception as e:
            print(f"播放音频失败: {e}")
    
    def cleanup(self):
        """清理资源"""
        self.audio.terminate()

def run_demo(args):
    """运行智能震动演示"""
    print("="*60)
    print("🎯 智能声音识别与差异化震动演示")
    print("="*60)
    
    # 初始化组件
    try:
        sound_generator = SoundGenerator()
        audio_processor = AudioProcessor()
        controller_manager = ControllerManager()
        
        if not controller_manager.connected_controllers:
            print("⚠️ 未检测到手柄，只进行声音生成演示")
        
        vibration_mapper = VibrationMapper(controller_manager)
        vibration_mapper.apply_preset('intense')  # 使用强化预设
        
        # 演示声音类型列表
        sound_demos = [
            ("💥 爆炸声", sound_generator.generate_explosion_sound, "强烈低频震动，模拟爆炸冲击"),
            ("⚔️ 金属碰撞", sound_generator.generate_metal_clash_sound, "尖锐高频震动，模拟刀剑碰撞"),
            ("🔫 枪声", sound_generator.generate_gunshot_sound, "瞬间全频段冲击，模拟射击"),
            ("🥁 鼓声", sound_generator.generate_drum_hit_sound, "深沉低频震动，模拟打击乐"),
            ("💎 玻璃破碎", sound_generator.generate_glass_break_sound, "细腻高频震动，模拟破碎声")
        ]
        
        print("\n开始声音识别和震动演示...\n")
        
        for i, (name, generator_func, description) in enumerate(sound_demos, 1):
            print(f"{i}/5 {name}")
            print(f"   描述: {description}")
            
            # 生成测试声音
            print("   🎵 生成音频...")
            audio_data = generator_func()
            
            if args.save_audio:
                # 保存音频文件用于测试
                import scipy.io.wavfile as wavfile
                filename = f"demo_{name.replace(' ', '_').lower()}.wav"
                wavfile.write(filename, sound_generator.sample_rate, 
                             (audio_data * 32767).astype(np.int16))
                print(f"   💾 已保存: {filename}")
            
            # 播放声音并监控震动反应
            print("   🔊 播放并分析...")
            
            # 启动震动监控线程
            vibration_results = []
            def vibration_monitor():
                chunks = len(audio_data) // 1024
                for i in range(chunks):
                    start_idx = i * 1024
                    end_idx = min((i + 1) * 1024, len(audio_data))
                    chunk = audio_data[start_idx:end_idx]
                    
                    if len(chunk) > 0:
                        # 分析音频
                        volume_analysis = audio_processor.get_volume_analysis(chunk)
                        
                        # 处理震动映射
                        vibration_status = vibration_mapper.process_audio_frame(
                            volume_analysis, audio_processor, chunk
                        )
                        
                        vibration_results.append(vibration_status)
                    
                    time.sleep(0.02)  # 模拟实时处理
            
            # 启动监控
            monitor_thread = threading.Thread(target=vibration_monitor)
            monitor_thread.start()
            
            # 播放声音
            if not args.no_audio:
                sound_generator.play_sound(audio_data, volume=args.volume)
            
            # 等待分析完成
            monitor_thread.join()
            
            # 分析结果
            if vibration_results:
                sound_types = [r.get('sound_type', 'normal') for r in vibration_results]
                impact_detections = sum(1 for r in vibration_results if r.get('impact_detected', False))
                max_left = max(r.get('left_intensity', 0) for r in vibration_results)
                max_right = max(r.get('right_intensity', 0) for r in vibration_results)
                
                # 统计识别到的声音类型
                detected_type = max(set(sound_types), key=sound_types.count)
                
                print(f"   📊 识别结果: {detected_type}")
                print(f"   ⚡ 冲击检测: {impact_detections} 次")
                print(f"   🎮 震动强度: 左={max_left:.2f}, 右={max_right:.2f}")
                
                if detected_type == 'explosion':
                    print("   ✅ 正确识别为爆炸声 - 低频震动占主导")
                elif detected_type == 'metal_clash':
                    print("   ✅ 正确识别为金属碰撞 - 高频震动占主导")
                elif detected_type == 'gunshot':
                    print("   ✅ 正确识别为枪声 - 全频段强冲击")
                elif detected_type == 'drum_hit':
                    print("   ✅ 正确识别为鼓声 - 低频节拍感")
                elif detected_type == 'glass_break':
                    print("   ✅ 正确识别为玻璃破碎 - 高频细腻震动")
                else:
                    print("   ⚠️ 识别为普通声音 - 可能需要调整识别阈值")
            
            print()
            
            if i < len(sound_demos):
                time.sleep(1)  # 间隔时间
        
        print("🎉 演示完成！")
        print("\n📋 总结:")
        print("- 爆炸声 → 强化左马达（低频）震动")
        print("- 金属碰撞 → 强化右马达（高频）震动")
        print("- 枪声 → 瞬间全频段冲击")
        print("- 鼓声 → 深沉低频节拍震动")
        print("- 玻璃破碎 → 细腻高频震动")
        
        if controller_manager.connected_controllers:
            print(f"\n🎮 检测到手柄: {len(controller_manager.connected_controllers)} 个")
        else:
            print("\n⚠️ 建议连接Xbox手柄以体验震动效果")
        
    except Exception as e:
        print(f"演示运行失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理资源
        try:
            sound_generator.cleanup()
            if 'vibration_mapper' in locals():
                vibration_mapper.stop_vibration()
            if 'controller_manager' in locals():
                controller_manager.cleanup()
        except:
            pass

def main():
    parser = argparse.ArgumentParser(
        description="智能声音识别与差异化震动演示",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
演示说明:
  本程序会生成5种不同类型的测试声音，展示智能声音识别功能：
  
  1. 💥 爆炸声 - 测试超低频识别和强低频震动
  2. ⚔️ 金属碰撞 - 测试高频识别和尖锐震动  
  3. 🔫 枪声 - 测试冲击检测和瞬间震动
  4. 🥁 鼓声 - 测试低频节拍和节奏震动
  5. 💎 玻璃破碎 - 测试高频细节和细腻震动
  
  每种声音都会被实时分析并产生对应的震动效果。
        """)
    
    parser.add_argument('--no-audio', action='store_true',
                       help='不播放声音，只进行震动分析')
    
    parser.add_argument('--save-audio', action='store_true',
                       help='保存生成的音频文件到当前目录')
    
    parser.add_argument('--volume', type=float, default=0.5,
                       help='播放音量 (0.0-1.0，默认0.5)')
    
    
    args = parser.parse_args()
    
    run_demo(args)

if __name__ == "__main__":
    main()
