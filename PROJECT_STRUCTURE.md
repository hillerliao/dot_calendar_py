# 项目结构说明

## 📁 核心功能文件

### 主要模块
- `main.py` - 主程序入口，处理日历和天气数据
- `app.py` - FastAPI Web服务，提供HTTP接口
- `dot_calendar.py` - 原有的点阵日历生成器
- `weather_chart.py` - 🌟 新增的天气预报走势图生成器
- `config.py` - 配置管理
- `models.py` - 数据模型定义
- `utils.py` - 工具函数和缓存

### CalDAV 客户端
- `dingtalk_caldav_client.py` - 钉钉日历客户端
- `icloud_caldav_client.py` - iCloud日历客户端  
- `google_caldav_client.py` - Google日历客户端

## 🛠️ 工具和脚本

### 命令行工具
- `weather_chart_cli.py` - 天气预报走势图命令行工具
- `run_weather_scheduler.sh` - Shell版定时任务脚本
- `weather_scheduler.py` - Python版定时任务管理器（推荐）

### 测试脚本
- `test_weather_chart.py` - 天气图表测试
- `test_main.py` - 主程序测试
- `test_*.py` - 其他各种功能测试

## 📄 示例输出

- `weather_forecast_chart.png` - 天气预报走势图示例
- `output.png` - 点阵日历示例
- `test_output.png` - 测试输出示例
- `test_output_empty.png` - 空日程示例

## 📚 文档

- `README.md` - 项目主文档
- `WEATHER_CHART_README.md` - 天气预报走势图功能文档
- `HISTORICAL_CACHE_README.md` - 历史数据缓存系统文档
- `WEATHER_SCHEDULER_README.md` - 定时任务系统使用文档
- `PROJECT_STRUCTURE.md` - 本文件，项目结构说明

## ⚙️ 配置和部署

- `.env` - 环境变量配置（包含API密钥等）
- `.env.sample` - 配置模板文件
- `.gitignore` - Git忽略文件配置
- `Dockerfile` - Docker容器配置
- `Pipfile` / `Pipfile.lock` - Python依赖管理
- `requirements.txt` - 依赖包列表
- `run_scheduler.sh` - 定时任务运行脚本

## 🎨 资源文件

- `fonts/` - 字体文件目录
  - `fusion-pixel-12px-monospaced-zh_hans.ttf` - 中文字体
  - `qweather-icons.ttf` - 天气图标字体

## ✨ 核心功能特性

### 1. 点阵日历生成器
- 支持多种日历源（钉钉、iCloud、Google）
- 天气信息集成
- 自动生成点阵图像
- 设备同步支持

### 2. 天气预报走势图生成器 🌟
- 横轴：日期（支持多天预报）
- 纵轴：温度（最高温和最低温）
- 天气图标显示
- **历史数据缓存机制**：
  - 自动缓存每日天气数据
  - 第二天即可使用前一天的真实数据
  - 多层降级保障系统稳定性

## 🚀 快速开始

### 生成天气预报走势图
```bash
# 基本使用（默认15天，包含昨天数据）
python3 weather_chart_cli.py

# 自定义天数和输出文件
python3 weather_chart_cli.py --days 7 --output my_chart.png

# 测试功能
python3 test_weather_chart.py
```

### 运行定时任务
```bash
# Shell版本（简单）
./run_weather_scheduler.sh

# Python版本（推荐，功能更丰富）
python3 weather_scheduler.py

# 使用配置文件
python3 weather_scheduler.py --config weather_scheduler_config.json

# 创建示例配置文件
python3 weather_scheduler.py --create-sample-config
```

### 启动Web服务
```bash
# 使用uvicorn启动
uvicorn app:app --host 0.0.0.0 --port 8000

# 或使用pipenv
pipenv run uvicorn app:app --host 0.0.0.0 --port 8000
```

### 运行定时任务
```bash
# 设置定时执行
./run_scheduler.sh
```

## 📊 API端点

### 主要接口
- `POST /generate` - 生成点阵日历图像
- `POST /weather-chart` - 🌟 生成天气预报走势图
- `GET /` - 健康检查接口

## ⏰ 定时任务系统 🌟

### Shell版本特性
- ✅ 简单易用，环境变量配置
- ✅ 支持设备推送开关
- ✅ 自动清理旧文件
- ✅ 完整的错误处理

### Python版本特性
- ✅ JSON配置文件支持
- ✅ 灵活的参数覆盖
- ✅ 完整的日志记录
- ✅ 通知系统集成
- ✅ 智能文件管理
- ✅ 计划任务支持

### 推荐使用方式
1. **日常使用**: Shell版本 (`./run_weather_scheduler.sh`)
2. **高级配置**: Python版本 (`python3 weather_scheduler.py --config config.json`)
3. **系统集成**: systemd cron + Python版本
4. **监控场景**: Python版本 + 通知功能

### 天气走势图API示例
```bash
curl -X POST http://localhost:8000/weather-chart \
  -H "Content-Type: application/json" \
  -d '{
    "token": "your_token",
    "days": 7,
    "include_yesterday": true
  }'
```

## 🗂️ 推荐的项目结构

如果你想进一步整理，可以考虑以下结构：

```
dot_calendar_py/
├── src/                    # 源代码目录
│   ├── core/              # 核心功能
│   │   ├── calendar.py     # 日历相关
│   │   └── weather.py      # 天气相关
│   ├── clients/            # 各种客户端
│   │   ├── caldav/        # CalDAV客户端
│   │   └── weather.py      # 天气API客户端
│   └── utils/              # 工具函数
├── tests/                  # 测试文件
├── docs/                   # 文档目录
├── examples/               # 示例输出
├── resources/              # 资源文件
│   └── fonts/            # 字体文件
├── config/                 # 配置文件
├── scripts/                # 脚本文件
└── output/                 # 输出文件目录
```

## 💡 开发建议

1. **保持核心文件简洁**: 主要功能文件应该专注单一职责
2. **测试文件归类**: 可以创建 `tests/` 目录存放所有测试文件
3. **文档集中**: 所有文档放在 `docs/` 目录
4. **输出分离**: 创建 `output/` 目录存放生成的图像
5. **配置分离**: 敏感配置使用环境变量，模板文件单独管理

## 🔧 维护说明

- **定期清理**: 定期删除临时测试文件和过期的缓存
- **依赖更新**: 定期检查和更新依赖包版本
- **文档同步**: 功能变更时及时更新相关文档
- **测试覆盖**: 确保新功能有对应的测试文件

这个项目现在具备了完整的天气信息处理和可视化功能，支持多种数据源和部署方式！