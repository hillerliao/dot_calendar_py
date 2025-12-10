#!/usr/bin/env python3
"""
天气预报走势图命令行工具
"""

import sys
import os
import argparse

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
from weather_chart import WeatherChart


def main():
    """命令行主函数"""
    parser = argparse.ArgumentParser(description='天气预报走势图生成器')
    parser.add_argument('--days', type=int, default=15, help='预报天数 (默认: 15)')
    parser.add_argument('--output', '-o', default='weather_forecast_chart.png', help='输出文件名')
    parser.add_argument('--location', help='位置信息 (覆盖配置文件中的设置)')
    parser.add_argument('--include-yesterday', action='store_true', default=True, help='包含昨天数据作为参考 (默认: True)')
    parser.add_argument('--no-yesterday', action='store_true', help='不包含昨天数据')
    
    args = parser.parse_args()
    
    # 检查配置
    if not args.location and not config.CONFIG_USER_LOCATION:
        print("错误: 请在配置文件中设置 CONFIG_USER_LOCATION 或使用 --location 参数")
        sys.exit(1)
    
    if not config.QWEATHER_KEY:
        print("错误: 请在配置文件中设置 QWEATHER_KEY")
        sys.exit(1)
    
    if not config.QWEATHER_HOST:
        print("错误: 请在配置文件中设置 QWEATHER_HOST")
        sys.exit(1)
    
    location = args.location or config.CONFIG_USER_LOCATION
    
    print(f"📍 位置: {location}")
    print(f"📅 预报天数: {args.days}")
    print(f"📁 输出文件: {args.output}")
    
    try:
        # 创建天气预报走势图
        chart = WeatherChart(
            location=location,
            qweather_host=config.QWEATHER_HOST,
            qweather_key=config.QWEATHER_KEY
        )
        
        # 加载天气数据
        include_yesterday = args.include_yesterday and not args.no_yesterday
        print("\n🌤️ 正在加载天气数据...")
        chart.load_weather_data(days=args.days, include_yesterday=include_yesterday)
        
        # 统计历史数据和预测数据
        historical_days = sum(1 for day in chart.weather_data if day.get('isHistorical', False))
        forecast_days = len(chart.weather_data) - historical_days
        
        print(f"✅ 已加载历史数据 {historical_days} 天，预报数据 {forecast_days} 天")
        print(f"📊 总计 {len(chart.weather_data)} 天数据")
        
        # 显示天气概况
        if chart.weather_data:
            temps_high = [float(day['tempMax']) for day in chart.weather_data]
            temps_low = [float(day['tempMin']) for day in chart.weather_data]
            avg_high = sum(temps_high) / len(temps_high)
            avg_low = sum(temps_low) / len(temps_low)
            
            print(f"📊 温度范围: {min(temps_low):.0f}°C ~ {max(temps_high):.0f}°C")
            print(f"📈 平均高温: {avg_high:.1f}°C, 平均低温: {avg_low:.1f}°C")
        
        # 创建图像
        print("\n🎨 正在生成天气预报走势图...")
        chart.create_image()
        
        # 保存图像
        chart.save_image(args.output)
        
        print(f"\n🎉 天气预报走势图生成完成！")
        print(f"📁 文件已保存到: {args.output}")
        
    except Exception as e:
        print(f"\n❌ 生成天气预报走势图时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()