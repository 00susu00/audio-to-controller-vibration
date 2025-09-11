#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NVIDIA音频捕获解决方案
提供多种方法来捕获NVIDIA High Definition Audio设备的输出
"""

import subprocess
import sys
import os
import webbrowser

def solution_1_enable_nvidia_stereo_mix():
    """方案一：启用NVIDIA立体声混音"""
    print("🎯 方案一：启用NVIDIA立体声混音")
    print("=" * 50)
    
    print("📋 操作步骤：")
    print("1. 右键点击系统托盘的🔊音频图标")
    print("2. 选择「声音设置」")
    print("3. 向下滚动，点击「声音控制面板」")
    print("4. 切换到「录制」标签页")
    print("5. 在录制设备列表中右键空白处")
    print("6. 勾选「显示已禁用的设备」和「显示已断开的设备」")
    print("7. 查找包含'NVIDIA'或'High Definition Audio'的立体声混音设备")
    print("8. 右键该设备，选择「启用」")
    print("9. 右键该设备，选择「设为默认设备」")
    
    print("\n💡 如果找到NVIDIA立体声混音设备：")
    print("   - 在我们的程序中就可以选择这个设备了！")
    print("   - 它会直接捕获输出到LG TV的音频")
    
    print("\n❌ 如果没有找到NVIDIA立体声混音设备：")
    print("   - 说明NVIDIA驱动没有提供立体声混音功能")
    print("   - 请尝试方案二或方案三")
    
    # 尝试打开声音控制面板
    try:
        print("\n🚀 正在打开声音控制面板...")
        subprocess.run("control mmsys.cpl", shell=True)
        print("✅ 声音控制面板已打开，请按上述步骤操作")
    except Exception as e:
        print(f"❌ 无法自动打开控制面板: {e}")
        print("请手动打开：控制面板 → 硬件和声音 → 声音")

def solution_2_vb_cable():
    """方案二：使用VB-Cable虚拟音频设备"""
    print("\n🎯 方案二：VB-Cable虚拟音频设备 (推荐)")
    print("=" * 50)
    
    print("📋 VB-Cable是什么？")
    print("- 免费的虚拟音频设备软件")
    print("- 创建一个虚拟的音频输入/输出设备")
    print("- 可以将音频从一个应用程序传输到另一个应用程序")
    
    print("\n📥 安装步骤：")
    print("1. 访问VB-Audio官网：https://vb-audio.com/Cable/")
    print("2. 下载 VBCABLE_Driver_Pack43.zip")
    print("3. 解压并以管理员身份运行 VBCABLE_Setup_x64.exe")
    print("4. 重启计算机")
    
    print("\n⚙️ 配置步骤：")
    print("1. 安装完成后，在Windows声音设置中：")
    print("   - 播放设备中会出现「CABLE Input」")
    print("   - 录制设备中会出现「CABLE Output」")
    print()
    print("2. 设置音频同时输出：")
    print("   - 保持LG TV为主播放设备")
    print("   - 使用Windows「侦听此设备」功能：")
    print("     * 右键「CABLE Input」→ 属性 → 侦听")
    print("     * 勾选「侦听此设备」")
    print("     * 选择「LG TV SSCR2」作为播放设备")
    print()
    print("3. 在我们的程序中：")
    print("   - 选择「CABLE Output」作为音频输入设备")
    print("   - 现在可以捕获所有音频了！")
    
    # 询问是否打开下载页面
    try:
        choice = input("\n❓ 是否打开VB-Cable下载页面？(y/N): ").strip().lower()
        if choice in ['y', 'yes', 'Y']:
            print("🚀 正在打开VB-Cable下载页面...")
            webbrowser.open('https://vb-audio.com/Cable/')
            print("✅ 下载页面已打开")
    except:
        print("💻 请手动访问：https://vb-audio.com/Cable/")

def solution_3_audio_router():
    """方案三：使用Windows音频路由"""
    print("\n🎯 方案三：Windows音频同时输出")
    print("=" * 50)
    
    print("📋 这种方法使用Windows内置功能：")
    print("1. 设置LG TV为默认播放设备")
    print("2. 同时启用Realtek扬声器输出")
    print("3. 使用Realtek立体声混音捕获")
    
    print("\n⚙️ 操作步骤：")
    print("1. 右键音频图标 → 声音设置")
    print("2. 在「输出设备」中选择「LG TV SSCR2」")
    print("3. 点击「声音控制面板」")
    print("4. 在「播放」标签页中：")
    print("   - 右键「扬声器 (Realtek)」")
    print("   - 选择「属性」→「侦听」标签页")
    print("   - 勾选「侦听此设备」")
    print("   - 播放设备选择「LG TV SSCR2」")
    print("5. 在我们的程序中选择Realtek立体声混音")
    
    print("\n💡 优点：无需安装额外软件")
    print("⚠️ 缺点：可能会有轻微的音频延迟")

def solution_4_test_current():
    """方案四：测试当前配置"""
    print("\n🎯 方案四：测试当前Realtek立体声混音")
    print("=" * 50)
    
    print("🧪 让我们先测试一下当前的配置：")
    print("1. 确保LG TV为默认播放设备")
    print("2. 播放一些音频（如音乐、视频）")
    print("3. 在我们的程序中选择ID 24的立体声混音设备")
    print("4. 观察是否有音频信号")
    
    print("\n❓ 如果没有信号，说明Realtek立体声混音确实无法捕获NVIDIA输出")
    print("✅ 如果有信号，说明当前配置可能已经可以工作了")

def main():
    print("🎵 NVIDIA音频捕获解决方案")
    print("=" * 60)
    print("针对LG TV SSCR2 (NVIDIA High Definition Audio)的音频捕获问题")
    print("=" * 60)
    
    while True:
        print("\n📋 可用解决方案：")
        print("1. 启用NVIDIA立体声混音 (最直接)")
        print("2. 使用VB-Cable虚拟设备 (推荐)")
        print("3. Windows音频同时输出")
        print("4. 测试当前配置")
        print("5. 退出")
        
        try:
            choice = input("\n请选择解决方案 (1-5): ").strip()
            
            if choice == '1':
                solution_1_enable_nvidia_stereo_mix()
            elif choice == '2':
                solution_2_vb_cable()
            elif choice == '3':
                solution_3_audio_router()
            elif choice == '4':
                solution_4_test_current()
            elif choice == '5':
                print("\n👋 再见！如有问题请随时联系。")
                break
            else:
                print("❌ 无效选择，请输入1-5")
                
        except KeyboardInterrupt:
            print("\n👋 再见！")
            break
        except Exception as e:
            print(f"❌ 出错了: {e}")

if __name__ == "__main__":
    main()
