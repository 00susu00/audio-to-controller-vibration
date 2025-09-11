#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
延迟配置测试工具
测试不同chunk_size下的延迟和性能表现
"""

import time
import numpy as np
from audio_processor import AudioProcessor
from vibration_mapper import VibrationMapper
from controller_manager import ControllerManager

class LatencyTester:
    def __init__(self):
        """初始化延迟测试器"""
        self.controller_manager = ControllerManager()
        self.test_duration = 5.0  # 测试时长(秒)
        
    def calculate_theoretical_latency(self, chunk_size, sample_rate=44100, queue_size=3):
        """计算理论延迟"""
        chunk_delay = (chunk_size / sample_rate) * 1000  # ms
        queue_delay = queue_size * chunk_delay
        processing_delay = 2.0  # 估算处理延迟
        return chunk_delay + queue_delay + processing_delay
    
    def test_chunk_size(self, chunk_size):
        """测试指定chunk_size的性能"""
        print(f"\n🧪 测试 chunk_size = {chunk_size}")
        print("-" * 40)
        
        try:
            # 创建组件
            audio_processor = AudioProcessor(chunk_size=chunk_size)
            vibration_mapper = VibrationMapper(self.controller_manager)
            
            # 理论延迟
            theoretical_latency = self.calculate_theoretical_latency(chunk_size)
            print(f"📊 理论延迟: {theoretical_latency:.1f}ms")
            
            # 性能测试
            if not audio_processor.start_recording():
                print("❌ 无法启动音频录制")
                return None
            
            print(f"⏱️  开始 {self.test_duration} 秒性能测试...")
            
            start_time = time.time()
            frame_count = 0
            processing_times = []
            audio_dropouts = 0
            
            while time.time() - start_time < self.test_duration:
                # 获取音频数据
                audio_data = audio_processor.get_latest_audio_data(timeout=0.1)
                
                if audio_data is not None:
                    # 测量处理时间
                    process_start = time.perf_counter()
                    
                    # 音频处理
                    volume_analysis = audio_processor.get_volume_analysis(audio_data)
                    vibration_status = vibration_mapper.process_audio_frame(
                        volume_analysis, audio_processor, audio_data
                    )
                    
                    process_end = time.perf_counter()
                    processing_times.append((process_end - process_start) * 1000)
                    frame_count += 1
                else:
                    audio_dropouts += 1
            
            audio_processor.stop_recording()
            
            # 统计结果
            if processing_times:
                avg_processing = np.mean(processing_times)
                max_processing = np.max(processing_times)
                fps = frame_count / self.test_duration
                dropout_rate = (audio_dropouts / (frame_count + audio_dropouts)) * 100
                
                print(f"📈 测试结果:")
                print(f"   帧数: {frame_count}")
                print(f"   平均FPS: {fps:.1f}")
                print(f"   平均处理时间: {avg_processing:.2f}ms")
                print(f"   最大处理时间: {max_processing:.2f}ms")
                print(f"   音频丢帧率: {dropout_rate:.1f}%")
                
                # 实际延迟估算
                actual_latency = theoretical_latency + avg_processing
                print(f"🎯 实际延迟估算: {actual_latency:.1f}ms")
                
                # 评级
                if dropout_rate > 5:
                    grade = "❌ 不稳定"
                elif actual_latency < 5:
                    grade = "✅ 优秀"
                elif actual_latency < 10:
                    grade = "✅ 良好"
                elif actual_latency < 20:
                    grade = "⚠️ 一般"
                else:
                    grade = "❌ 较差"
                
                print(f"⭐ 总体评级: {grade}")
                
                return {
                    'chunk_size': chunk_size,
                    'theoretical_latency': theoretical_latency,
                    'actual_latency': actual_latency,
                    'fps': fps,
                    'dropout_rate': dropout_rate,
                    'avg_processing': avg_processing,
                    'grade': grade
                }
            else:
                print("❌ 测试失败: 未获取到音频数据")
                return None
                
        except Exception as e:
            print(f"❌ 测试出错: {e}")
            return None
    
    def run_comprehensive_test(self):
        """运行全面的延迟测试"""
        print("🚀 延迟配置综合测试")
        print("=" * 50)
        
        chunk_sizes = [16, 32, 64, 128, 256]
        results = []
        
        for chunk_size in chunk_sizes:
            result = self.test_chunk_size(chunk_size)
            if result:
                results.append(result)
            
            # 短暂休息避免资源冲突
            time.sleep(1)
        
        # 汇总报告
        print("\n" + "=" * 50)
        print("📊 延迟测试汇总报告")
        print("=" * 50)
        
        print(f"{'Chunk Size':<12} {'理论延迟':<10} {'实际延迟':<10} {'FPS':<8} {'丢帧率':<8} {'评级':<10}")
        print("-" * 60)
        
        best_config = None
        best_score = float('inf')
        
        for result in results:
            print(f"{result['chunk_size']:<12} {result['theoretical_latency']:<10.1f} "
                  f"{result['actual_latency']:<10.1f} {result['fps']:<8.1f} "
                  f"{result['dropout_rate']:<8.1f}% {result['grade']:<10}")
            
            # 综合评分 (延迟权重更高)
            score = result['actual_latency'] * 2 + result['dropout_rate'] * 0.5
            if result['dropout_rate'] < 5 and score < best_score:
                best_score = score
                best_config = result
        
        if best_config:
            print(f"\n🏆 推荐配置: chunk_size = {best_config['chunk_size']}")
            print(f"   - 预期延迟: {best_config['actual_latency']:.1f}ms")
            print(f"   - 稳定性: 丢帧率 {best_config['dropout_rate']:.1f}%")
            print(f"\n💡 启动命令:")
            print(f"   python main.py --chunk-size {best_config['chunk_size']} --high-priority")
        
        print(f"\n📝 测试完成! 共测试了 {len(results)} 个配置")

def main():
    """主函数"""
    print("🎯 延迟优化测试工具")
    print("此工具将测试不同chunk_size配置下的延迟和性能表现")
    print("测试期间请保持安静，避免影响音频采集")
    print()
    
    input("按回车键开始测试...")
    
    tester = LatencyTester()
    tester.run_comprehensive_test()
    
    print("\n🎉 测试完成! 请根据推荐配置优化您的延迟设置")

if __name__ == "__main__":
    main()
