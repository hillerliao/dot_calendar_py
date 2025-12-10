# 天气预报走势图定时任务

## 🚀 功能概述

天气预报走势图定时任务系统提供了完整的自动化解决方案，可以：

- 🌤️ 自动生成天气预报走势图
- 📱 推送到指定的设备
- 🧹 自动清理旧文件
- 📊 支持灵活的配置选项
- 🔔 支持通知推送

## 📁 文件说明

### 核心文件

- **`run_weather_scheduler.sh`** - Shell版本定时任务脚本
- **`weather_scheduler.py`** - Python版本定时任务管理器（推荐）
- **`WEATHER_SCHEDULER_README.md`** - 本使用说明文档

### 配置文件

- **`.env`** - 环境变量配置（API密钥等）
- **`weather_scheduler_config.json`** - 定时任务配置文件（可选）

## 🛠️ 快速开始

### 方法一：使用Shell脚本（简单）

```bash
# 基本使用
./run_weather_scheduler.sh

# 自定义环境变量
WEATHER_FORECAST_DAYS=7 WEATHER_OUTPUT_FILE=my_chart.png ./run_weather_scheduler.sh

# 启用设备推送
WEATHER_ENABLE_DEVICE_PUSH=true WEATHER_DEVICE_IDX=0 ./run_weather_scheduler.sh
```

### 方法二：使用Python管理器（推荐）

```bash
# 基本使用
python3 weather_scheduler.py

# 指定预报天数
python3 weather_scheduler.py --days 7

# 包含昨天数据
python3 weather_scheduler.py --include-yesterday

# 禁用设备推送
python3 weather_scheduler.py --no-device-push

# 指定输出目录
python3 weather_scheduler.py --output-dir ./my_output

# 使用配置文件
python3 weather_scheduler.py --config my_config.json
```

### 方法三：创建配置文件

```bash
# 创建示例配置文件
python3 weather_scheduler.py --create-sample-config

# 编辑配置文件
vim weather_scheduler_config.json

# 使用配置文件运行
python3 weather_scheduler.py --config weather_scheduler_config.json
```

## ⚙️ 环境变量配置

在 `.env` 文件中设置以下变量：

```bash
# 必需配置
DOT_CALENDAR_TOKEN=your_access_token
QWEATHER_KEY=your_qweather_api_key
QWEATHER_HOST=devapi.qweather.com
CONFIG_USER_LOCATION=116.41,39.90  # 北京坐标

# 可选配置
WEATHER_FORECAST_DAYS=7                    # 预报天数
WEATHER_OUTPUT_FILE=weather_chart.png      # 输出文件名
WEATHER_INCLUDE_YESTERDAY=true             # 是否包含昨天数据
WEATHER_ENABLE_DEVICE_PUSH=false           # 是否推送到设备
WEATHER_DEVICE_IDX=0                       # 设备索引
WEATHER_CLEANUP_OLD=true                   # 是否清理旧文件
```

## 📋 配置文件说明

Python版本支持详细的JSON配置文件：

```json
{
  "enabled": true,
  "forecast_days": 7,
  "include_yesterday": true,
  "output_filename": "weather_chart_{date}.png",
  "output_dir": "./output",
  "device_push": {
    "enabled": true,
    "device_idx": 0
  },
  "cleanup": {
    "enabled": true,
    "keep_files": 5
  },
  "notification": {
    "enabled": false,
    "webhook_url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
    "success_message": "天气预报走势图生成成功",
    "error_message": "天气预报走势图生成失败"
  },
  "schedule": {
    "times": ["08:00", "20:00"],
    "timezone": "Asia/Shanghai"
  }
}
```

### 配置字段说明

| 字段 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `enabled` | bool | 是否启用定时任务 | `true` |
| `forecast_days` | int | 预报天数 | `7` |
| `include_yesterday` | bool | 是否包含昨天数据 | `true` |
| `output_filename` | string | 输出文件名模板 | `weather_chart_{date}.png` |
| `output_dir` | string | 输出目录 | `./output` |
| `device_push.enabled` | bool | 是否推送到设备 | `false` |
| `device_push.device_idx` | int | 设备索引 | `-1` |
| `cleanup.enabled` | bool | 是否清理旧文件 | `true` |
| `cleanup.keep_files` | int | 保留文件数量 | `3` |
| `notification.enabled` | bool | 是否发送通知 | `false` |
| `notification.webhook_url` | string | 通知webhook URL | `""` |
| `schedule.times` | array | 每天运行时间 | `["08:00", "20:00"]` |
| `schedule.timezone` | string | 时区 | `"Asia/Shanghai"` |

## 🔧 定时任务设置

### 使用crontab设置定时任务

```bash
# 编辑crontab
crontab -e

# 添加定时任务（每天8点和20点运行）
0 8 * * * cd /path/to/dot_calendar_py && ./run_weather_scheduler.sh >> /var/log/weather_scheduler.log 2>&1
0 20 * * * cd /path/to/dot_calendar_py && ./run_weather_scheduler.sh >> /var/log/weather_scheduler.log 2>&1

# 或者使用Python版本
0 8 * * * cd /path/to/dot_calendar_py && /usr/bin/python3 weather_scheduler.py >> /var/log/weather_scheduler.log 2>&1
0 20 * * * cd /path/to/dot_calendar_py && /usr/bin/python3 weather_scheduler.py >> /var/log/weather_scheduler.log 2>&1
```

### 使用systemd服务（推荐）

创建服务文件：

```bash
sudo vim /etc/systemd/system/weather-scheduler.service
```

内容如下：

```ini
[Unit]
Description=Weather Chart Scheduler
After=network.target

[Service]
Type=oneshot
User=your_username
WorkingDirectory=/path/to/dot_calendar_py
ExecStart=/usr/bin/python3 weather_scheduler.py
Environment=PATH=/usr/local/bin:/usr/bin:/bin
StandardOutput=append:/var/log/weather_scheduler.log
StandardError=append:/var/log/weather_scheduler.log

[Install]
WantedBy=multi-user.target
```

创建定时器：

```bash
sudo vim /etc/systemd/system/weather-scheduler.timer
```

内容如下：

```ini
[Unit]
Description=Run Weather Chart Scheduler twice daily
Requires=weather-scheduler.service

[Timer]
OnCalendar=*-*-* 08:00:00
OnCalendar=*-*-* 20:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

启用和启动：

```bash
sudo systemctl enable weather-scheduler.timer
sudo systemctl start weather-scheduler.timer
sudo systemctl status weather-scheduler.timer
```

## 📱 设备推送配置

### 启用设备推送

1. 确保设备已配置并可连接
2. 在 `.env` 文件中设置设备相关配置
3. 设置环境变量 `WEATHER_ENABLE_DEVICE_PUSH=true`
4. 或在配置文件中设置 `device_push.enabled = true`

### 设备索引说明

- `0`: 第一个设备
- `1`: 第二个设备
- `-1`: 默认设备

## 📊 输出文件管理

### 文件命名规则

- Shell脚本：`weather_chart_scheduled.png`（固定名称）
- Python脚本：`weather_chart_YYYYMMDD_HHMM.png`（时间戳）

### 自动清理

- 默认保留最近3个文件
- 可通过配置文件调整保留数量
- 清理基于文件修改时间

## 🔔 通知功能

### 支持的通知方式

- Slack Webhook
- 钉钉机器人
- 企业微信机器人
- 自定义HTTP通知

### 配置示例

```json
{
  "notification": {
    "enabled": true,
    "webhook_url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
    "success_message": "🌤️ 天气预报走势图生成成功",
    "error_message": "❌ 天气预报走势图生成失败"
  }
}
```

## 🐛 故障排除

### 常见问题

**Q: 脚本执行失败，提示权限错误**
```bash
# 添加执行权限
chmod +x run_weather_scheduler.sh
chmod +x weather_scheduler.py
```

**Q: 找不到 .env 文件**
```bash
# 确保在项目根目录下运行
cd /path/to/dot_calendar_py
ls -la .env
```

**Q: 天气API调用失败**
- 检查 `QWEATHER_KEY` 是否正确
- 检查网络连接
- 查看API配额是否用完

**Q: 设备推送失败**
- 检查设备是否在线
- 检查设备配置是否正确
- 查看设备连接状态

**Q: 字体文件缺失**
- 确保 `fonts/` 目录存在
- 下载必要的字体文件到fonts目录

### 日志查看

```bash
# 查看详细日志
tail -f weather_scheduler.log

# 查看最近的错误
grep ERROR weather_scheduler.log

# 查看系统日志（使用systemd）
journalctl -u weather-scheduler.service -f
```

## 📈 性能优化

### 建议配置

- 预报天数：7-15天（过多会影响性能）
- 清理策略：保留3-5个文件
- 运行频率：每天2次（早晚各一次）
- 缓存策略：启用历史数据缓存

### 监控指标

- API调用次数
- 生成时间
- 文件大小
- 推送成功率

## 🎉 总结

天气预报走势图定时任务系统提供了完整的自动化解决方案：

✅ **灵活配置** - 支持Shell和Python两种方式
✅ **自动推送** - 支持推送到指定设备  
✅ **智能清理** - 自动管理输出文件
✅ **通知集成** - 支持多种通知方式
✅ **日志记录** - 完整的执行日志
✅ **错误处理** - 优雅的异常处理

选择适合你需求的方式，享受自动化的天气预报走势图服务！