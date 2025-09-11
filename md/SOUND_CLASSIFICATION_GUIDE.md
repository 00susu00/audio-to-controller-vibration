# 🎯 智能声音识别与差异化震动指南

## ✨ 新功能概述

现在的程序可以智能识别不同类型的声音，并为每种声音类型产生独特的震动模式！

### 🔊 支持的声音类型

| 声音类型 | 频率特征 | 震动特点 | 应用场景 |
|---------|----------|----------|----------|
| **爆炸声** (explosion) | 超低频主导 (20-200Hz) | 强烈左马达震动 + 轻微右马达 | 游戏爆炸、雷声、重击 |
| **金属碰撞** (metal_clash) | 高频主导 (2k-16kHz) | 轻微左马达 + 强烈右马达震动 | 刀剑碰撞、金属撞击 |
| **枪声** (gunshot) | 中高频突发 | 全频段强烈冲击，偏右马达 | 射击游戏、鞭炮声 |
| **鼓声** (drum_hit) | 低频主导 (60-500Hz) | 强化低频震动 | 打击乐器、重击声 |
| **玻璃破碎** (glass_break) | 高频尖锐 | 主要高频震动 | 破碎声、尖锐响声 |
| **普通声音** (normal) | 均匀分布 | 标准映射 | 音乐、人声等 |

## 🚀 使用方法

### 基础启动（推荐）
```bash
# 启动智能声音识别模式
python main.py

# 或指定参数
python main.py --chunk-size 64
```

### 高性能模式
```bash
# 注意：可能需要关闭声音分类以减少延迟
python main.py --chunk-size 64
```

## 🎛️ 高级配置参数

### 1. 冲击增强设置
```python
# 在代码中可以调整这些参数
vibration_mapper.set_impact_settings(
    multiplier=3.0,    # 冲击增强倍数 (1.0-5.0)
    duration=0.15      # 冲击持续时间 (0.05-0.5秒)
)
```

### 2. 声音类型增强
```python
vibration_mapper.set_sound_type_boosts(
    explosion_boost=2.5,  # 爆炸低频增强 (1.0-4.0)
    metal_boost=2.0       # 金属高频增强 (1.0-3.0)
)
```

### 3. 识别敏感度调整
不同声音的识别阈值可以在 `vibration_mapper.py` 中的 `classification_thresholds` 调整：

```python
self.classification_thresholds = {
    'explosion': {
        'sub_bass': 0.3,        # 超低频阈值 (调低=更容易识别)
        'bass': 0.2,            # 低频阈值
        'impact_intensity': 0.4  # 冲击强度阈值
    },
    'metal_clash': {
        'high_mid': 0.25,       # 中高频阈值
        'treble': 0.2,          # 高频阈值  
        'impact_intensity': 0.3
    }
    # ... 其他声音类型
}
```

## 📊 实时监控

程序运行时会显示：
- **当前声音类型**: explosion, metal_clash, gunshot 等
- **冲击检测状态**: 是否检测到瞬时冲击
- **频段分析**: 各频段的能量分布

### GUI界面显示
- 声音类型会在状态栏实时显示
- 冲击事件会在图表中高亮显示
- 不同声音类型会有不同的颜色标识

## 🎮 游戏体验优化

### FPS游戏
```bash
# 强化枪声和爆炸效果
python main.py --preset intense
```
- 枪声：瞬间全频段冲击
- 爆炸：持续强烈低频震动
- 脚步声：轻微低频震动

### 格斗游戏  
```bash
# 突出打击感
python main.py --chunk-size 32
```
- 拳击：中低频冲击
- 金属武器：高频尖锐震动
- 重击：强化冲击增强

### 音乐游戏
```bash
# 平衡模式，避免过度震动
python main.py --preset balanced
```
- 鼓点：低频节拍震动
- 镲片：高频细节震动
- 贝斯：深沉低频震动

## ⚡ 性能优化建议

### 高性能系统
```bash
# 开启所有高级功能
python main.py --chunk-size 32 --high-priority
```

### 中等性能系统  
```bash
# 平衡性能和功能
python main.py --chunk-size 64
```

### 低性能系统
```bash
# 使用较大的chunk-size，减少处理负载
python main.py --chunk-size 256
```

## 🔧 故障排除

### 声音识别不准确
1. **调整识别阈值**：降低 `classification_thresholds` 中的值
2. **检查音频质量**：确保系统音频清晰
3. **优化chunk-size**：较大的chunk-size提供更好的频率分析

### 震动感觉不强烈
1. **增加冲击倍数**：`impact_multiplier` 设为 4.0-5.0
2. **调整声音增强**：提高 `explosion_bass_boost` 和 `metal_treble_boost`
3. **使用intense预设**：`--preset intense`

### 延迟过高
1. **减小chunk-size**：`--chunk-size 64`
2. **关闭声音识别**：在GUI中禁用声音分类
3. **关闭冲击增强**：在GUI中禁用冲击增强

## 📈 技术原理

### 频谱分析
程序将音频分为6个频段：
- **超低频 (20-60Hz)**: 爆炸、雷声的主要成分
- **低频 (60-200Hz)**: 鼓声、重击的核心频段
- **中低频 (200-500Hz)**: 人声和乐器的基础频段
- **中频 (500-2000Hz)**: 人声主体和乐器和谐波
- **中高频 (2000-6000Hz)**: 音色清晰度和细节
- **高频 (6000-16000Hz)**: 金属声、尖锐音的特征频段

### 冲击检测
- **能量突变检测**: 当前帧能量比前一帧增加5倍以上
- **冲击强度计算**: 基于能量比例计算冲击强度
- **衰减曲线**: 使用指数衰减模拟自然震动感

### 声音分类算法
每种声音类型都有独特的"指纹"：
- **频谱特征**: 不同频段的能量分布
- **时域特征**: 冲击强度和持续时间  
- **动态特征**: 能量变化率和主导频段

## 💡 高级技巧

### 自定义声音类型
可以在代码中添加新的声音类型：

```python
# 在 classification_thresholds 中添加
'custom_sound': {
    'target_band': 0.3,
    'impact_intensity': 0.2
}

# 在 _intelligent_vibration_mapping 中添加处理逻辑
elif sound_type == 'custom_sound':
    # 自定义震动逻辑
    enhanced_left = base_left * 1.5
    enhanced_right = base_right * 0.8
    return enhanced_left, enhanced_right
```

### 动态调整阈值
```python
# 运行时调整识别阈值
vibration_mapper.classification_thresholds['explosion']['sub_bass'] = 0.2  # 更敏感
vibration_mapper.classification_thresholds['metal_clash']['treble'] = 0.15  # 更敏感
```

---

现在您的程序具备了真正的"听觉智能"，能够理解不同声音的特征并产生相应的震动反馈，大大增强了沉浸感和打击感！🎯✨
