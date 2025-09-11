#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统音频设置助手
帮助用户启用Windows立体声混音功能
"""

import subprocess
import sys
import winreg
from pathlib import Path

class SystemAudioHelper:
    """系统音频设置助手类"""
    
    def __init__(self):
        self.is_windows = sys.platform.startswith('win')
    
    def check_stereo_mix_status(self):
        """检查立体声混音状态"""
        if not self.is_windows:
            return False, "仅支持Windows系统"
        
        try:
            # 通过注册表检查录音设备状态
            import winreg as reg
            
            # 这里可以添加注册表检查逻辑
            # 但由于权限和复杂性问题，建议使用其他方法
            return None, "无法自动检测，请手动检查"
            
        except Exception as e:
            return False, f"检查失败: {e}"
    
    def open_sound_settings(self):
        """打开Windows声音设置"""
        if not self.is_windows:
            return False, "仅支持Windows系统"
        
        try:
            # 尝试打开新版Windows设置
            result = subprocess.run("ms-settings:sound", shell=True, timeout=5)
            if result.returncode == 0:
                return True, "已打开Windows声音设置"
        except:
            pass
        
        try:
            # 尝试打开经典声音控制面板
            subprocess.run("control mmsys.cpl", shell=True, timeout=5)
            return True, "已打开声音控制面板"
        except Exception as e:
            return False, f"无法打开声音设置: {e}"
    
    def get_setup_instructions(self):
        """获取设置说明"""
        if not self.is_windows:
            return ["当前系统不支持Windows立体声混音功能"]
        
        return [
            "启用立体声混音的步骤：",
            "",
            "方法一 - Windows 10/11:",
            "1. 右键点击任务栏的音量图标",
            "2. 选择'打开声音设置'",
            "3. 滚动到底部，点击'更多声音设置'",
            "4. 切换到'录制'选项卡",
            "5. 右键空白处，选择'显示禁用的设备'和'显示已断开的设备'",
            "6. 找到'立体声混音'或'Stereo Mix'，右键选择'启用'",
            "7. 可选：右键设置为'默认设备'",
            "",
            "方法二 - 经典控制面板:",
            "1. 按Win+R，输入'mmsys.cpl'并回车",
            "2. 切换到'录制'选项卡",
            "3. 按照上述步骤4-7操作",
            "",
            "替代方案:",
            "- 下载VB-Cable虚拟音频线缆",
            "- 使用OBS Studio的音频监听功能",
            "- 使用专业音频软件的内录功能",
            "",
            "注意：某些声卡可能不支持立体声混音功能"
        ]
    
    def install_vb_cable_guide(self):
        """VB-Cable安装指南"""
        return [
            "VB-Cable虚拟音频线缆安装指南：",
            "",
            "1. 访问官网：https://vb-audio.com/Cable/",
            "2. 下载VB-CABLE Virtual Audio Device",
            "3. 以管理员权限安装",
            "4. 重启计算机",
            "5. 在'播放设备'中将'CABLE Input'设为默认设备",
            "6. 在'录制设备'中启用'CABLE Output'",
            "7. 在程序中选择'CABLE Output'作为输入设备",
            "",
            "使用步骤：",
            "- 将系统音频输出到CABLE Input",
            "- 程序从CABLE Output录制音频",
            "- 如需听到声音，需要额外的音频路由设置"
        ]

def main():
    """主函数"""
    helper = SystemAudioHelper()
    
    print("="*60)
    print("系统音频设置助手")
    print("="*60)
    
    print("\n检查系统...")
    if not helper.is_windows:
        print("错误：当前系统不是Windows，无法使用立体声混音功能")
        print("建议使用专业音频软件或虚拟音频设备")
        return
    
    print("Windows系统检测成功")
    
    # 检查立体声混音状态
    status, message = helper.check_stereo_mix_status()
    print(f"立体声混音状态: {message}")
    
    print("\n" + "="*60)
    print("设置说明")
    print("="*60)
    
    instructions = helper.get_setup_instructions()
    for instruction in instructions:
        print(instruction)
    
    print("\n" + "="*60)
    print("操作选项")
    print("="*60)
    print("1. 打开Windows声音设置")
    print("2. 显示VB-Cable安装指南")
    print("3. 退出")
    
    while True:
        try:
            choice = input("\n请选择操作 (1-3): ").strip()
            
            if choice == '1':
                success, message = helper.open_sound_settings()
                print(f"结果: {message}")
                if success:
                    print("请按照上述说明启用立体声混音，然后重启程序")
                break
                
            elif choice == '2':
                print("\n" + "="*60)
                vb_guide = helper.install_vb_cable_guide()
                for line in vb_guide:
                    print(line)
                print("="*60)
                
            elif choice == '3':
                print("退出设置助手")
                break
                
            else:
                print("无效选择，请重新输入")
                
        except KeyboardInterrupt:
            print("\n程序被用户中断")
            break
        except Exception as e:
            print(f"操作出错: {e}")

if __name__ == "__main__":
    main()
