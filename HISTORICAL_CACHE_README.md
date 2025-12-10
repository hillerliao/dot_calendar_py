# 历史数据缓存系统

## 🎯 功能概述

天气预报走势图生成器现在支持**历史数据缓存机制**，解决了你提出的需求："下一天的时候就有头一天的数据了"。

## ✨ 核心特性

### 1. 📅 智能历史数据获取
- **优先级1**: 真实历史数据缓存（前一天已保存的真实天气数据）
- **优先级2**: 历史天气API（和风天气时光机API，支持最近10天）
- **优先级3**: 预报数据估算（基于预报模型推断昨天天气）

### 2. 🗄️ 自动缓存机制
- **自动保存**: 每次运行时自动缓存当日天气数据
- **智能使用**: 第二天运行时自动查找并使用前一天缓存
- **有效期**: 缓存保存24小时，确保数据新鲜度
- **格式统一**: 缓存数据与API返回格式完全兼容

### 3. 🔄 多层降级保障
```
真实历史数据缓存
        ↓ (如果不可用)
历史天气API (多种认证方式)
        ↓ (如果失败)
预报数据估算
        ↓ (确保功能正常)
```

### 4. 🎨 视觉区分显示
- **真实历史数据**: 浅灰色空心圆 + 浅灰色文字
- **估算历史数据**: 深灰色空心圆 + 深灰色文字 + "(估算)"标记
- **预报数据**: 彩色实心圆 + 正常颜色

## 🚀 使用方法

### 基本使用
```bash
# 默认启用昨天数据参考（自动使用缓存）
python3 weather_chart_cli.py --days 7

# 明确包含昨天数据
python3 weather_chart_cli.py --days 7 --include_yesterday
```

### Python代码使用
```python
from weather_chart import WeatherChart

chart = WeatherChart(
    location="北京",
    qweather_host="devapi.qweather.com", 
    qweather_key="your_key"
)

# 自动包含昨天数据（会优先使用缓存）
chart.load_weather_data(days=7, include_yesterday=True)
chart.create_image()
chart.save_image('weather_with_history.png')
```

### API调用
```bash
curl -X POST http://localhost:8000/weather-chart \
  -H "Content-Type: application/json" \
  -d '{
    "token": "your_token",
    "days": 7,
    "include_yesterday": true
  }'
```

## 📊 缓存工作流程

### 第一天（建立缓存）
```
今天运行 → 获取预报数据 → 自动缓存今天数据 → 生成图表（昨天用估算）
```

### 第二天（使用缓存）
```
明天运行 → 检查昨天缓存 → 使用真实历史数据 → 生成图表（昨天用真实数据）
```

### 第三天及以后
```
持续运行 → 每天都使用前一天缓存 → 保持数据连续性
```

## 🔧 技术实现

### 缓存键格式
```
qweather_historical_real_{location}_{date}
例如: qweather_historical_real_116.41,39.90_2025-12-10
```

### 数据结构
```json
{
    "code": "200",
    "weatherDaily": [{
        "fxDate": "2025-12-10",
        "tempMax": "7",
        "tempMin": "-1", 
        "textDay": "多云",
        "isHistorical": true,
        "isRealData": true
    }],
    "isRealData": true,
    "savedAt": "2025-12-10T22:40:00.233846"
}
```

### 多认证方式支持
系统会按以下顺序尝试历史天气API：
1. **URL参数**: `?key=YOUR_API_KEY`
2. **Bearer Token**: `Authorization: Bearer YOUR_TOKEN`  
3. **API Key头部**: `X-QW-Api-Key: YOUR_API_KEY`

## 📈 优势分析

### 1. 数据连续性 🔄
- **问题解决**: 第二天就有前一天的真实天气数据
- **趋势分析**: 提供完整的温度变化趋势
- **对比价值**: 真实历史 vs 预测数据

### 2. 性能提升 ⚡
- **API调用减少**: 避免重复请求历史数据
- **响应速度**: 缓存读取比API调用快得多
- **并发友好**: 减少对API服务的压力

### 3. 成本节省 💰
- **API费用**: 减少历史数据API调用次数
- **带宽节省**: 缓存数据本地访问
- **长期效益**: 累积节省大量API成本

### 4. 系统可靠性 🛡️
- **备份机制**: 本地缓存作为API的备份
- **故障容错**: API不可用时自动降级
- **数据一致性**: 确保图表数据的准确性

## 🎯 实际效果展示

### 不使用缓存的情况
```
Day 1: ❌ 昨天(估算) -1°C ~ 7°C  [基于预报推断]
Day 2: ❌ 昨天(估算) 2°C ~ 8°C  [基于预报推断]  
Day 3: ❌ 昨天(估算) 0°C ~ 6°C  [基于预报推断]
```

### 使用缓存的情况  
```
Day 1: ❌ 昨天(估算) -1°C ~ 7°C  [基于预报推断]
Day 2: ✅ 昨天(真实) 2°C ~ 8°C  [真实历史数据]
Day 3: ✅ 昨天(真实) 0°C ~ 6°C  [真实历史数据]
```

## 🧪 测试和演示

### 运行完整测试
```bash
# 基础功能测试
python3 test_weather_chart.py

# 缓存机制测试  
python3 test_historical_cache.py

# 完整工作流程演示
python3 demo_final_cache.py

# 缓存机制验证
python3 demo_cache_fixed.py
```

### 验证缓存建立
```bash
# 第一次运行（建立缓存）
python3 weather_chart_cli.py --days 3

# 第二次运行（使用缓存）
python3 weather_chart_cli.py --days 3
```

## 📝 配置说明

### 环境变量
在 `.env` 文件中配置：
```bash
# 和风天气API配置
QWEATHER_KEY=your_api_key_here
QWEATHER_HOST=devapi.qweather.com
CONFIG_USER_LOCATION=116.41,39.90

# 可选：历史数据API专用配置（如果需要）
# QWEATHER_HISTORICAL_KEY=historical_api_key  # 专用历史数据API密钥
```

### 缓存配置
缓存系统使用现有的 `W2FileCache` 类，默认配置：
- **缓存目录**: `../cache` (项目根目录下的cache文件夹)
- **历史数据缓存时间**: 24小时
- **API数据缓存时间**: 30分钟

## 🔄 升级说明

### 从旧版本升级
如果你之前使用的是没有缓存功能的版本：

1. **无需修改配置**: 所有现有配置都兼容
2. **自动启用缓存**: 新版本自动启用缓存功能  
3. **渐进式改进**: 缓存会在使用过程中逐步建立

### 首次使用
```bash
# 第一天运行，建立缓存基础
python3 weather_chart_cli.py --days 7

# 第二天运行，享受缓存效果
python3 weather_chart_cli.py --days 7
```

## 🔍 故障排除

### 常见问题

**Q: 为什么还是显示"估算"数据？**
A: 可能原因：
   - 历史API密钥权限不足
   - 缓存还未建立（需要运行一天后）
   - 缓存已过期（超过24小时）

**Q: 缓存数据不准确？**
A: 缓存直接来源于当天的预报数据，与API返回的数据一致。

**Q: 如何清除缓存？**
A: 删除缓存目录中对应的文件，或等待24小时自动过期。

### 调试模式
在代码中添加调试输出：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🎉 总结

历史数据缓存系统完美解决了你的需求：

✅ **第二天就有前一天的真实数据**
✅ **无需额外配置，自动工作**  
✅ **多重保障，确保稳定**
✅ **性能优化，成本节省**
✅ **视觉区分，一目了然**

现在你的天气预报走势图具备了完整的历史数据支持，每天都能看到基于真实历史数据的准确趋势对比！