#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速延迟优化脚本
一键应用最佳的低延迟配置
"""

import subprocess
import sys
import platform
import json

def check_system_capability():
    """检查系统性能能力"""
    print("🔍 检查系统性能能力...")
    
    try:
        import psutil
        
        # CPU信息
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        # 内存信息
        memory = psutil.virtual_memory()
        memory_gb = memory.total / (1024**3)
        
        print(f"   CPU: {cpu_count} 核心")
        if cpu_freq:
            print(f"   频率: {cpu_freq.current:.0f} MHz")
        print(f"   内存: {memory_gb:.1f} GB")
        
        # 性能等级评估
        if cpu_count >= 8 and memory_gb >= 16:
            return "high"  # 高性能
        elif cpu_count >= 4 and memory_gb >= 8:
            return "medium"  # 中等性能
        else:
            return "low"  # 低性能
            
    except ImportError:
        print("   ⚠️ 无法获取详细系统信息 (缺少psutil)")
        return "medium"  # 默认中等性能

def get_optimal_config(performance_level):
    """根据系统性能获取最优配置"""
    configs = {
        "high": {
            "chunk_size": 16,
            "description": "极致延迟配置",
            "expected_latency": "2-3ms",
            "cpu_usage": "高",
            "stability": "需要高性能CPU"
        },
        "medium": {
            "chunk_size": 32,
            "description": "平衡延迟配置",
            "expected_latency": "4-6ms", 
            "cpu_usage": "中等",
            "stability": "大多数系统适用"
        },
        "low": {
            "chunk_size": 64,
            "description": "稳定延迟配置",
            "expected_latency": "6-10ms",
            "cpu_usage": "低",
            "stability": "高稳定性"
        }
    }
    
    return configs.get(performance_level, configs["medium"])

def apply_registry_optimizations():
    """应用Windows注册表优化 (需要管理员权限)"""
    if platform.system() != "Windows":
        return
    
    print("🔧 尝试应用Windows系统优化...")
    
    try:
        # 音频服务优化
        subprocess.run([
            "reg", "add", 
            "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\AudioSrv",
            "/v", "Type", "/t", "REG_DWORD", "/d", "16", "/f"
        ], capture_output=True, check=True)
        
        print("   ✅ 音频服务优化成功")
        
    except subprocess.CalledProcessError:
        print("   ⚠️ 系统优化需要管理员权限，已跳过")
    except Exception as e:
        print(f"   ⚠️ 系统优化失败: {e}")

def create_optimized_config(chunk_size):
    """创建优化的配置文件"""
    print("📝 创建优化配置文件...")
    
    optimized_config = {
        "basic_settings": {
            "low_freq_sensitivity": 1.0,
            "high_freq_sensitivity": 2.5,
            "overall_intensity": 1.0,
            "preset": "intense"
        },
        "advanced_settings": {
            "smoothing_factor": 0.0,  # 无平滑，最快响应
            "frequency_cutoff": 400,
            "frequency_difference_factor": 0.3,
            "min_low_freq_threshold": 0.1,
            "min_high_freq_threshold": 0.05,
            "min_volume_threshold": 0.02,
            "max_volume_threshold": 1.0
        },
        "performance_settings": {
            "chunk_size": chunk_size,
            "enable_sound_classification": False,  # 关闭以降低延迟
            "enable_impact_enhancement": False     # 关闭以降低延迟
        }
    }
    
    try:
        with open("low_latency_config.json", "w", encoding="utf-8") as f:
            json.dump(optimized_config, f, indent=2, ensure_ascii=False)
        
        print("   ✅ 配置文件已保存为: low_latency_config.json")
        return True
        
    except Exception as e:
        print(f"   ❌ 配置文件创建失败: {e}")
        return False

def main():
    """主优化流程"""
    print("🚀 快速延迟优化工具")
    print("=" * 40)
    
    # 1. 检查系统性能
    performance_level = check_system_capability()
    optimal_config = get_optimal_config(performance_level)
    
    print(f"\n📊 系统性能等级: {performance_level.upper()}")
    print(f"💡 推荐配置: {optimal_config['description']}")
    print(f"   - Chunk Size: {optimal_config['chunk_size']}")
    print(f"   - 预期延迟: {optimal_config['expected_latency']}")
    print(f"   - CPU使用: {optimal_config['cpu_usage']}")
    print(f"   - 稳定性: {optimal_config['stability']}")
    
    # 2. 用户确认
    print(f"\n是否应用此配置? (y/n): ", end="")
    if input().lower() != 'y':
        print("❌ 用户取消操作")
        return
    
    # 3. 应用系统优化
    apply_registry_optimizations()
    
    # 4. 创建优化配置
    config_created = create_optimized_config(optimal_config['chunk_size'])
    
    # 5. 提供启动命令
    print(f"\n🎯 优化配置应用完成!")
    print(f"📋 推荐启动命令:")
    print(f"   python main.py --chunk-size {optimal_config['chunk_size']} --high-priority --preset intense")
    
    if config_created:
        print(f"\n或使用优化配置文件:")
        print(f"   python main.py --config low_latency_config.json --high-priority")
    
    print(f"\n💡 额外优化建议:")
    print(f"   1. 在任务管理器中设置程序为'高优先级'")
    print(f"   2. 关闭不必要的后台程序")
    print(f"   3. 在声音设置中启用'独占模式'")
    print(f"   4. 在GUI中关闭'声音识别'和'冲击增强'")
    
    print(f"\n⚠️ 注意事项:")
    if optimal_config['chunk_size'] <= 32:
        print(f"   - chunk_size较小，请确保CPU性能充足")
        print(f"   - 如果出现音频断续，请增大chunk_size到64")
    
    print(f"\n🎉 延迟优化完成! 预期延迟: {optimal_config['expected_latency']}")

if __name__ == "__main__":
    main()
