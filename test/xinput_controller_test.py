#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用XInput库的手柄震动测试程序
针对pygame震动功能不工作的替代方案
"""

import time
import sys

try:
    import XInput
except ImportError:
    print("错误：XInput-Python库未安装")
    print("请运行：pip install XInput-Python")
    sys.exit(1)

class XInputControllerTest:
    def __init__(self):
        """初始化XInput手柄"""
        print("初始化XInput控制器...")
        
        # 检查连接的手柄
        self.connected_controllers = []
        for i in range(4):  # XInput最多支持4个控制器
            try:
                state = XInput.get_state(i)
                self.connected_controllers.append(i)
                print(f"检测到控制器 {i}")
            except:
                continue
        
        if not self.connected_controllers:
            print("未检测到XInput兼容的控制器")
            print("请确保：")
            print("1. 手柄已正确连接")
            print("2. 手柄为Xbox系列或XInput兼容手柄")
            print("3. 手柄驱动已正确安装")
            return
        
        # 使用第一个连接的控制器
        self.controller_id = self.connected_controllers[0]
        print(f"使用控制器 {self.controller_id}")
        
        # 测试震动功能
        self.test_vibration_support()
    
    def test_vibration_support(self):
        """测试XInput震动功能支持"""
        print("\n测试XInput震动功能...")
        try:
            # 短暂测试震动
            XInput.set_vibration(self.controller_id, 16384, 16384)  # 50% 强度
            time.sleep(0.2)
            XInput.set_vibration(self.controller_id, 0, 0)  # 停止震动
            print("✓ XInput震动功能正常")
            self.vibration_supported = True
        except Exception as e:
            print(f"❌ XInput震动功能测试失败: {e}")
            self.vibration_supported = False
    
    def test_left_vibration(self, intensity=0.8, duration=1.0):
        """测试左侧震动（低频马达）"""
        print(f"测试左侧震动 - 强度: {intensity}, 持续时间: {duration}秒")
        
        if not self.vibration_supported:
            print("⚠️  震动功能不支持，跳过测试")
            return
        
        try:
            # XInput震动值范围：0-65535
            left_motor = int(intensity * 65535)
            right_motor = 0
            
            print(f"设置震动值 - 左马达: {left_motor}, 右马达: {right_motor}")
            XInput.set_vibration(self.controller_id, left_motor, right_motor)
            
            print("等待震动完成...")
            time.sleep(duration)
            
            print("停止震动...")
            XInput.set_vibration(self.controller_id, 0, 0)
            print("✓ 左侧震动测试完成")
            
        except Exception as e:
            print(f"❌ 左侧震动测试失败: {e}")
    
    def test_right_vibration(self, intensity=0.8, duration=1.0):
        """测试右侧震动（高频马达）"""
        print(f"测试右侧震动 - 强度: {intensity}, 持续时间: {duration}秒")
        
        if not self.vibration_supported:
            print("⚠️  震动功能不支持，跳过测试")
            return
        
        try:
            # XInput震动值范围：0-65535
            left_motor = 0
            right_motor = int(intensity * 65535)
            
            print(f"设置震动值 - 左马达: {left_motor}, 右马达: {right_motor}")
            XInput.set_vibration(self.controller_id, left_motor, right_motor)
            
            print("等待震动完成...")
            time.sleep(duration)
            
            print("停止震动...")
            XInput.set_vibration(self.controller_id, 0, 0)
            print("✓ 右侧震动测试完成")
            
        except Exception as e:
            print(f"❌ 右侧震动测试失败: {e}")
    
    def test_both_vibration(self, intensity=0.8, duration=1.0):
        """测试双侧震动"""
        print(f"测试双侧震动 - 强度: {intensity}, 持续时间: {duration}秒")
        
        if not self.vibration_supported:
            print("⚠️  震动功能不支持，跳过测试")
            return
        
        try:
            # XInput震动值范围：0-65535
            motor_value = int(intensity * 65535)
            
            print(f"设置震动值 - 左马达: {motor_value}, 右马达: {motor_value}")
            XInput.set_vibration(self.controller_id, motor_value, motor_value)
            
            print("等待震动完成...")
            time.sleep(duration)
            
            print("停止震动...")
            XInput.set_vibration(self.controller_id, 0, 0)
            print("✓ 双侧震动测试完成")
            
        except Exception as e:
            print(f"❌ 双侧震动测试失败: {e}")
    
    def test_pattern_vibration(self):
        """测试震动模式"""
        print("开始震动模式测试...")
        
        if not self.vibration_supported:
            print("⚠️  震动功能不支持，跳过测试")
            return
        
        try:
            # 渐强震动
            print("1. 渐强震动测试")
            for i in range(1, 6):
                intensity = i * 0.2
                motor_value = int(intensity * 65535)
                print(f"  强度: {intensity} ({motor_value})")
                XInput.set_vibration(self.controller_id, motor_value, motor_value)
                time.sleep(0.5)
            
            XInput.set_vibration(self.controller_id, 0, 0)
            time.sleep(0.5)
            
            # 左右交替震动
            print("2. 左右交替震动测试")
            motor_value = int(0.8 * 65535)
            
            for i in range(4):
                # 左侧
                print("  左侧震动")
                XInput.set_vibration(self.controller_id, motor_value, 0)
                time.sleep(0.3)
                
                XInput.set_vibration(self.controller_id, 0, 0)
                time.sleep(0.1)
                
                # 右侧
                print("  右侧震动")
                XInput.set_vibration(self.controller_id, 0, motor_value)
                time.sleep(0.3)
                
                XInput.set_vibration(self.controller_id, 0, 0)
                time.sleep(0.1)
            
            print("震动模式测试完成")
            
        except Exception as e:
            print(f"❌ 震动模式测试失败: {e}")
    
    def custom_vibration_test(self):
        """自定义震动强度测试"""
        if not self.vibration_supported:
            print("⚠️  震动功能不支持，跳过测试")
            return
            
        try:
            print("\n自定义震动测试")
            left_intensity = float(input("左侧震动强度 (0.0-1.0): "))
            right_intensity = float(input("右侧震动强度 (0.0-1.0): "))
            duration = float(input("震动持续时间 (秒): "))
            
            # 限制数值范围
            left_intensity = max(0.0, min(1.0, left_intensity))
            right_intensity = max(0.0, min(1.0, right_intensity))
            duration = max(0.1, min(10.0, duration))
            
            # 转换为XInput格式
            left_motor = int(left_intensity * 65535)
            right_motor = int(right_intensity * 65535)
            
            print(f"开始自定义震动 - 左: {left_intensity} ({left_motor}), 右: {right_intensity} ({right_motor}), 时长: {duration}秒")
            XInput.set_vibration(self.controller_id, left_motor, right_motor)
            time.sleep(duration)
            XInput.set_vibration(self.controller_id, 0, 0)
            print("自定义震动测试完成")
            
        except ValueError:
            print("输入格式错误，请输入有效的数字")
        except Exception as e:
            print(f"自定义震动测试失败: {e}")
    
    def show_controller_info(self):
        """显示控制器详细信息"""
        print("\n" + "="*50)
        print("XInput控制器信息")
        print("="*50)
        
        for controller_id in self.connected_controllers:
            try:
                print(f"\n控制器 {controller_id}:")
                state = XInput.get_state(controller_id)
                
                # 获取按钮状态
                buttons = XInput.get_button_values(state)
                print(f"  连接状态: 已连接")
                print(f"  数据包编号: {state.dwPacketNumber}")
                
                # 显示当前按钮状态（如果有按钮被按下）
                pressed_buttons = [name for name, pressed in buttons.items() if pressed]
                if pressed_buttons:
                    print(f"  当前按下的按钮: {', '.join(pressed_buttons)}")
                
                # 显示摇杆位置
                trigger_values = XInput.get_trigger_values(state)
                thumb_values = XInput.get_thumb_values(state)
                
                if trigger_values['left'] > 0 or trigger_values['right'] > 0:
                    print(f"  扳机值: 左={trigger_values['left']:.3f}, 右={trigger_values['right']:.3f}")
                
                if abs(thumb_values['left_x']) > 0.1 or abs(thumb_values['left_y']) > 0.1:
                    print(f"  左摇杆: X={thumb_values['left_x']:.3f}, Y={thumb_values['left_y']:.3f}")
                
                if abs(thumb_values['right_x']) > 0.1 or abs(thumb_values['right_y']) > 0.1:
                    print(f"  右摇杆: X={thumb_values['right_x']:.3f}, Y={thumb_values['right_y']:.3f}")
                
            except Exception as e:
                print(f"  控制器 {controller_id}: 读取状态失败 - {e}")
        
        print("="*50)
    
    def run_interactive_test(self):
        """交互式测试菜单"""
        if not self.connected_controllers:
            return
        
        while True:
            print("\n" + "="*50)
            print("XInput手柄震动测试菜单")
            print("="*50)
            print("1. 测试左侧震动（低频马达）")
            print("2. 测试右侧震动（高频马达）")
            print("3. 测试双侧震动")
            print("4. 测试震动模式")
            print("5. 自定义震动强度测试")
            print("6. 显示控制器详细信息")
            print("0. 退出")
            print("="*50)
            
            try:
                choice = input("请选择测试项目 (0-6): ").strip()
                
                if choice == '0':
                    print("退出测试程序")
                    break
                elif choice == '1':
                    self.test_left_vibration()
                elif choice == '2':
                    self.test_right_vibration()
                elif choice == '3':
                    self.test_both_vibration()
                elif choice == '4':
                    self.test_pattern_vibration()
                elif choice == '5':
                    self.custom_vibration_test()
                elif choice == '6':
                    self.show_controller_info()
                else:
                    print("无效选择，请重新输入")
                    
            except KeyboardInterrupt:
                print("\n程序被用户中断")
                break
            except Exception as e:
                print(f"发生错误: {e}")
        
        # 确保退出时停止震动
        try:
            if hasattr(self, 'controller_id'):
                XInput.set_vibration(self.controller_id, 0, 0)
        except:
            pass

def main():
    """主函数"""
    print("="*60)
    print("XInput手柄震动测试程序")
    print("="*60)
    print("程序功能：")
    print("- 使用XInput库直接控制Xbox手柄")
    print("- 支持精确的震动强度控制（0-65535）")
    print("- 兼容Xbox 360、Xbox One、Xbox Series手柄")
    print("- 解决pygame震动功能兼容性问题")
    print("="*60)
    
    try:
        tester = XInputControllerTest()
        if hasattr(tester, 'connected_controllers') and tester.connected_controllers:
            tester.run_interactive_test()
        else:
            print("没有可用的控制器，程序退出")
    except Exception as e:
        print(f"程序运行出错: {e}")

if __name__ == "__main__":
    main()
