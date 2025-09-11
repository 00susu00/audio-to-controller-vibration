#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NVIDIA音频设备助手
专门用于检测和设置NVIDIA High Definition Audio相关的录音设备
"""

import pyaudio
import re
import subprocess
import sys

class NvidiaAudioHelper:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
    
    def find_nvidia_devices(self):
        """查找所有NVIDIA相关的音频设备"""
        nvidia_devices = {
            'input': [],    # 录音设备
            'output': []    # 播放设备
        }
        
        try:
            # 检查录音设备
            device_count = self.audio.get_device_count()
            print(f"扫描 {device_count} 个音频设备...\n")
            
            for i in range(device_count):
                try:
                    device_info = self.audio.get_device_info_by_index(i)
                    device_name = device_info.get('name', '').lower()
                    
                    # 检查是否为NVIDIA设备
                    if 'nvidia' in device_name or 'high definition audio' in device_name:
                        device_entry = {
                            'index': i,
                            'name': device_info.get('name', ''),
                            'channels': device_info.get('maxInputChannels', 0),
                            'sample_rate': device_info.get('defaultSampleRate', 0),
                            'type': 'unknown'
                        }
                        
                        # 分类设备类型
                        if device_info.get('maxInputChannels', 0) > 0:
                            # 可以作为录音设备
                            if 'stereo mix' in device_name or '立体声混音' in device_name:
                                device_entry['type'] = 'stereo_mix'
                            elif 'loopback' in device_name or '环回' in device_name:
                                device_entry['type'] = 'loopback'
                            else:
                                device_entry['type'] = 'input'
                            nvidia_devices['input'].append(device_entry)
                            
                        if device_info.get('maxOutputChannels', 0) > 0:
                            # 可以作为播放设备
                            nvidia_devices['output'].append(device_entry)
                
                except Exception as e:
                    continue
            
            return nvidia_devices
            
        except Exception as e:
            print(f"扫描设备时出错: {e}")
            return nvidia_devices
    
    def find_all_stereo_mix_devices(self):
        """查找所有立体声混音类型的设备"""
        stereo_mix_devices = []
        
        try:
            device_count = self.audio.get_device_count()
            
            for i in range(device_count):
                try:
                    device_info = self.audio.get_device_info_by_index(i)
                    device_name = device_info.get('name', '').lower()
                    
                    # 查找立体声混音相关设备
                    stereo_mix_keywords = [
                        'stereo mix', '立体声混音', 'what u hear', 
                        'loopback', '环回', 'wave out mix', '波形输出混音'
                    ]
                    
                    is_stereo_mix = any(keyword in device_name for keyword in stereo_mix_keywords)
                    
                    if is_stereo_mix and device_info.get('maxInputChannels', 0) > 0:
                        stereo_mix_devices.append({
                            'index': i,
                            'name': device_info.get('name', ''),
                            'channels': device_info.get('maxInputChannels', 0),
                            'sample_rate': device_info.get('defaultSampleRate', 0),
                            'driver': self._extract_driver_name(device_info.get('name', ''))
                        })
                
                except Exception as e:
                    continue
            
            return stereo_mix_devices
            
        except Exception as e:
            print(f"查找立体声混音设备时出错: {e}")
            return []
    
    def _extract_driver_name(self, device_name):
        """从设备名称中提取驱动名称"""
        device_name_lower = device_name.lower()
        
        if 'nvidia' in device_name_lower:
            return 'NVIDIA'
        elif 'realtek' in device_name_lower:
            return 'Realtek'
        elif 'high definition audio' in device_name_lower:
            return 'HD Audio'
        else:
            return 'Unknown'
    
    def get_current_default_playback_device(self):
        """获取当前默认播放设备（Windows）"""
        try:
            # 使用PowerShell获取默认播放设备
            cmd = """
            Get-AudioDevice -List | Where-Object {$_.Type -eq "Playback" -and $_.Default -eq $true} | Select-Object Name, ID
            """
            
            result = subprocess.run(['powershell', '-Command', cmd], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            else:
                return "无法检测默认播放设备"
                
        except Exception as e:
            return f"检测失败: {e}"
    
    def print_detailed_report(self):
        """打印详细的音频设备报告"""
        print("🎵 NVIDIA音频设备检测报告")
        print("=" * 60)
        
        # 检测NVIDIA设备
        nvidia_devices = self.find_nvidia_devices()
        
        if nvidia_devices['input'] or nvidia_devices['output']:
            print("\n📟 发现的NVIDIA音频设备:")
            
            if nvidia_devices['input']:
                print("\n  📥 录音设备 (可用于捕获音频):")
                for device in nvidia_devices['input']:
                    print(f"    设备ID {device['index']:2d}: {device['name']}")
                    print(f"               类型: {device['type']}")
                    print(f"               通道数: {device['channels']}")
                    print(f"               采样率: {device['sample_rate']:.0f} Hz")
                    print()
            
            if nvidia_devices['output']:
                print("  📤 播放设备:")
                for device in nvidia_devices['output']:
                    print(f"    设备ID {device['index']:2d}: {device['name']}")
                    print()
        else:
            print("\n❌ 未发现NVIDIA相关的录音设备")
        
        # 检测所有立体声混音设备
        stereo_devices = self.find_all_stereo_mix_devices()
        
        print("\n🔄 所有立体声混音设备:")
        if stereo_devices:
            for device in stereo_devices:
                status = "✅ 可捕获所有系统音频" if device['driver'] == 'Unknown' else f"⚠️  仅捕获{device['driver']}音频"
                print(f"  设备ID {device['index']:2d}: {device['name']}")
                print(f"             驱动: {device['driver']} - {status}")
                print(f"             通道数: {device['channels']}")
                print(f"             采样率: {device['sample_rate']:.0f} Hz")
                print()
        else:
            print("  ❌ 未发现立体声混音设备")
        
        # 检测当前默认播放设备
        print("\n🔊 当前默认播放设备:")
        default_device = self.get_current_default_playback_device()
        print(f"  {default_device}")
        
        print("\n💡 建议解决方案:")
        if not nvidia_devices['input']:
            print("  1. 启用NVIDIA立体声混音:")
            print("     - 右键点击系统托盘的音频图标")
            print("     - 选择「声音设置」→「声音控制面板」")
            print("     - 切换到「录制」标签页")
            print("     - 右键空白处，选择「显示已禁用的设备」")
            print("     - 找到NVIDIA相关的立体声混音，右键启用")
            print()
            print("  2. 使用VB-Cable虚拟音频设备:")
            print("     - 下载VB-Cable: https://vb-audio.com/Cable/")
            print("     - 安装后设置LG TV音频同时输出到VB-Cable")
            print("     - 在程序中选择VB-Cable作为输入设备")
            print()
            print("  3. 使用Realtek立体声混音(如果LG TV设为默认设备):")
            print("     - 在Windows声音设置中将LG TV设为默认播放设备")
            print("     - 使用现有的Realtek立体声混音设备")
        else:
            print("  ✅ 发现NVIDIA录音设备，可以直接使用！")
    
    def __del__(self):
        if hasattr(self, 'audio'):
            self.audio.terminate()

def main():
    print("🎯 NVIDIA音频设备检测工具")
    print("正在检测您的音频设备配置...\n")
    
    helper = NvidiaAudioHelper()
    helper.print_detailed_report()
    
    print("\n" + "=" * 60)
    print("检测完成！请根据上述建议配置您的音频设备。")

if __name__ == "__main__":
    main()
