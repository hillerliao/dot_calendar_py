# 天气预报走势图生成器

## 功能介绍

天气预报走势图生成器是一个基于和风天气API的图表生成工具，可以生成包含以下元素的天气预报走势图：

- 📅 **横轴**: 日期（支持多天预报）
- 🌡️ **纵轴**: 温度（最高温和最低温）
- 🌤️ **天气图标**: 每天的天气状况图标
- 📊 **温度曲线**: 红色高温曲线，蓝色低温曲线
- 🎨 **专业图表**: 包含网格、图例和清晰的标注
- 📈 **昨天数据参考**: 智能包含昨天数据作为对比基准

### ✨ 新增功能：昨天数据作为参考

- 📅 **智能日期对齐**: 以 today-1（昨天）作为起始日
- 🔍 **三种数据源**:
  - **历史实际数据**: 如果可用，获取昨天的真实天气数据
  - **估算数据**: 如果历史数据不可用，使用预报数据估算昨天的天气
  - **预报数据**: 未来的天气预报
- 🎨 **视觉区分**: 
  - 历史数据用灰色空心圆和灰色文字表示
  - 估算数据用灰色标记 "(估算)"
  - 预测数据用彩色实心圆和正常颜色
- 📈 **趋势对比**: 方便你对比昨天的实际/估算数据与未来预报的趋势

## 文件说明

### 核心模块
- `weather_chart.py` - 天气预报走势图生成器核心类
- `weather_chart_cli.py` - 命令行工具
- `test_weather_chart.py` - 测试脚本

### API端点
在 `app.py` 中新增了天气预报走势图端点：
- `POST /weather-chart` - 生成天气预报走势图

## 使用方法

### 1. 命令行使用

```bash
# 基本用法（默认15天预报，自动包含昨天数据作为参考）
python3 weather_chart_cli.py

# 指定天数（包含昨天数据）
python3 weather_chart_cli.py --days 7

# 指定输出文件
python3 weather_chart_cli.py --days 10 --output my_weather_chart.png

# 指定位置（覆盖配置文件设置）
python3 weather_chart_cli.py --location "北京" --days 5

# 运行完整演示（包含昨天数据功能）
python3 demo_with_yesterday.py
```

### 2. Python代码使用

```python
from weather_chart import WeatherChart
import config

# 创建图表生成器
chart = WeatherChart(
    location=config.CONFIG_USER_LOCATION,
    qweather_host=config.QWEATHER_HOST,
    qweather_key=config.QWEATHER_KEY
)

# 加载天气数据（包含昨天数据作为参考）
chart.load_weather_data(days=15, include_yesterday=True)
chart.create_image()
chart.save_image('my_weather_chart.png')

# 或者不包含昨天数据
chart.load_weather_data(days=15, include_yesterday=False)
chart.create_image()
chart.save_image('forecast_only_chart.png')
```

### 3. API调用

```bash
# 包含昨天数据（默认）
curl -X POST http://localhost:8000/weather-chart \
  -H "Content-Type: application/json" \
  -d '{
    "token": "your_token",
    "days": 7,
    "include_yesterday": true
  }'

# 不包含昨天数据
curl -X POST http://localhost:8000/weather-chart \
  -H "Content-Type: application/json" \
  -d '{
    "token": "your_token",
    "days": 7,
    "include_yesterday": false
  }'
```

## 图表特点

- **专业外观**: 清晰的网格线和坐标轴
- **直观展示**: 红色高温线，蓝色低温线
- **天气图标**: 使用和风天气官方图标字体
- **温度标注**: 每个数据点都有具体温度值
- **响应式设计**: 支持不同天数的预报展示
- **智能昨天数据**: 自动包含昨天数据作为对比基准
- **视觉区分**: 历史/估算/预测数据用不同样式区分
- **趋势对比**: 方便观察温度变化趋势

## 配置要求

确保在 `.env` 文件中配置了以下参数：

```bash
QWEATHER_KEY=你的和风天气API密钥
QWEATHER_HOST=devapi.qweather.com
CONFIG_USER_LOCATION=你的位置坐标或城市名
DOT_CALENDAR_TOKEN=你的访问令牌（API调用需要）
```

## 依赖项

天气预报走势图生成器使用以下依赖项（已包含在 `requirements.txt` 中）：

- `requests` - HTTP请求库
- `Pillow` - 图像处理库
- `python-dotenv` - 环境变量管理

## 输出示例

生成的图表包含：
- 800x400像素的专业图表
- 温度范围自动调整
- 天气图标和日期标注
- 高温/低温曲线和数据点
- 清晰的图例说明

## 故障排除

1. **API密钥错误**: 检查 `.env` 文件中的 `QWEATHER_KEY` 是否正确
2. **位置参数错误**: 确认 `CONFIG_USER_LOCATION` 格式正确（坐标或城市名）
3. **字体缺失**: 确保 `fonts/` 目录中有必要的字体文件
4. **权限问题**: 确保有写入权限保存输出文件

## 示例输出

运行成功后，你将看到类似以下的输出：

```
📍 位置: 116.41,39.90
📅 预报天数: 7
📁 输出文件: 7_day_weather_chart.png

🌤️ 正在加载天气数据...
✅ 已加载 7 天的天气预报数据
📊 温度范围: -8°C ~ 7°C
📈 平均高温: 3.1°C, 平均低温: -5.6°C

🎨 正在生成天气预报走势图...
🎉 天气预报走势图生成完成！
📁 文件已保存到: 7_day_weather_chart.png
```