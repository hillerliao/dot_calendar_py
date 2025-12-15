#!/bin/bash

# 天气预报走势图定时任务脚本
# 用于生成天气预报走势图并推送到设备

cd "$(dirname "$0")/.."

# 检查pipenv是否安装 (using full path)
if [ ! -x "$HOME/.local/bin/pipenv" ]; then
    echo "pipenv 未安装，请先安装 pipenv"
    echo "Expected location: $HOME/.local/bin/pipenv"
    exit 1
fi

# Use the full path for pipenv
PIPENV_CMD="$HOME/.local/bin/pipenv"

# 从.env文件读取token（忽略注释行和空行）
if [ -f ".env" ]; then
    while IFS= read -r line; do
        # 跳过注释行和空行
        [[ $line =~ ^[[:space:]]*# ]] && continue
        [[ -z "${line// }" ]] && continue
        # 只导出包含=的行
        if [[ $line == *"="* ]]; then
            export "$line"
        fi
    done < .env
else
    echo "错误：找不到 .env 文件"
    exit 1
fi

# 检查必要的环境变量
if [ -z "$DOT_CALENDAR_TOKEN" ]; then
    echo "错误：.env 文件中未设置 DOT_CALENDAR_TOKEN"
    exit 1
fi

if [ -z "$QWEATHER_KEY" ]; then
    echo "错误：.env 文件中未设置 QWEATHER_KEY"
    exit 1
fi

# 设置默认参数
WEATHER_DAYS=${WEATHER_FORECAST_DAYS:-10}  # 默认7天预报
WEATHER_OUTPUT_FILE=${WEATHER_OUTPUT_FILE:-"weather_chart_scheduled.png"}
WEATHER_LOCATION=${CONFIG_USER_LOCATION:-"北京"}
INCLUDE_YESTERDAY=${WEATHER_INCLUDE_YESTERDAY:-"false"}  # 默认不包含昨天数据（避免估算显示）
WEATHER_ENABLE_DEVICE_PUSH=${WEATHER_ENABLE_DEVICE_PUSH:-"false"}  # 默认禁用设备推送
WEATHER_DEVICE_IDX=${WEATHER_DEVICE_IDX:--1}  # 默认设备索引

# 显示配置信息
echo "=========================================="
echo "🌤️  天气预报走势图定时任务"
echo "=========================================="
echo "📍 位置: $WEATHER_LOCATION"
echo "📅 预报天数: $WEATHER_DAYS 天"
echo "📁 输出文件: $WEATHER_OUTPUT_FILE"
echo "📅 包含昨天数据: $INCLUDE_YESTERDAY"
echo "📱 设备推送: $([ "$WEATHER_ENABLE_DEVICE_PUSH" = "true" ] && echo "✅ 已启用 (设备索引: $WEATHER_DEVICE_IDX)" || echo "❌ 已禁用")"
echo "⏰ 运行时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

# 检查fonts目录
if [ ! -d "fonts" ]; then
    echo "⚠️  警告: fonts 目录不存在，天气图标可能无法正常显示"
fi

# 运行天气预报走势图生成器
echo "🌤️ 正在生成天气预报走势图..."
ARGS=""
ARGS="$ARGS --location \"$WEATHER_LOCATION\""
ARGS="$ARGS --days $WEATHER_DAYS"
ARGS="$ARGS --output \"$WEATHER_OUTPUT_FILE\""

if [ "$INCLUDE_YESTERDAY" = "true" ]; then
    ARGS="$ARGS --include-yesterday"
else
    ARGS="$ARGS --no-yesterday"
fi

eval $PIPENV_CMD run python src/weather_chart_cli.py $ARGS

# 检查是否生成成功
if [ $? -eq 0 ] && [ -f "$WEATHER_OUTPUT_FILE" ]; then
    echo "✅ 天气预报走势图生成成功！"
    echo "📁 文件路径: $(pwd)/$WEATHER_OUTPUT_FILE"
    
    # 如果启用了设备推送，推送天气走势图到设备
    if [ "${WEATHER_ENABLE_DEVICE_PUSH:-false}" = "true" ]; then
        echo "📱 正在推送天气走势图到设备..."
        
        # 设置设备ID
        TARGET_DEVICE_ID="$DOT_DEVICE_ID"
        if [ "$WEATHER_DEVICE_IDX" -ge 0 ] && [ -n "$DOT_DEVICE_ID" ]; then
            # 从逗号分隔的设备ID列表中选择指定索引的设备
            DEVICE_ARRAY=(${DOT_DEVICE_ID//,/ })
            if [ $WEATHER_DEVICE_IDX -lt ${#DEVICE_ARRAY[@]} ]; then
                TARGET_DEVICE_ID="${DEVICE_ARRAY[$WEATHER_DEVICE_IDX]}"
                echo "🔧 选择设备索引 $WEATHER_DEVICE_IDX: $TARGET_DEVICE_ID"
            else
                echo "⚠️  设备索引 $WEATHER_DEVICE_IDX 超出范围，使用第一个设备"
                TARGET_DEVICE_ID="${DEVICE_ARRAY[0]}"
            fi
        fi
        
        # 检查是否需要调整图片尺寸以适配设备
        if [ "${WEATHER_RESIZE_FOR_DEVICE:-true}" = "true" ]; then
            echo "🔧 调整图片尺寸以适配设备 (296x152)..."
            $PIPENV_CMD run python src/device_push.py "$WEATHER_OUTPUT_FILE" --resize 296x152 --device-id "$TARGET_DEVICE_ID"
        else
            echo "📱 推送原始尺寸图片..."
            $PIPENV_CMD run python src/device_push.py "$WEATHER_OUTPUT_FILE" --device-id "$TARGET_DEVICE_ID"
        fi
        
        if [ $? -eq 0 ]; then
            echo "📱 设备推送成功！"
        else
            echo "❌ 设备推送失败！"
        fi
    else
        echo "ℹ️  设备推送已禁用，仅生成本地图表"
    fi
    
    # 可选：清理旧的图表文件
    if [ "${WEATHER_CLEANUP_OLD:-true}" = "true" ]; then
        echo "🧹 正在清理旧文件..."
        # 保留最近3个文件
        ls -t weather_chart_*.png 2>/dev/null | tail -n +4 | xargs rm -f 2>/dev/null || true
    fi
    
else
    echo "❌ 天气预报走势图生成失败！"
    exit 1
fi

echo "=========================================="
echo "🎉 定时任务执行完成！"
echo "⏰ 完成时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="