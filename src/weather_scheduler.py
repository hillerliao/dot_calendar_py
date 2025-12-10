#!/usr/bin/env python3
"""
天气预报走势图定时任务管理器
支持多种推送方式和灵活的配置选项
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
from weather_chart import WeatherChart
from dot_calendar import DotCalendar

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('weather_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class WeatherScheduler:
    """天气预报走势图定时任务管理器"""
    
    def __init__(self, config_file=None):
        """初始化调度器"""
        self.config = self.load_config(config_file)
        self.setup_logging()
        
    def load_config(self, config_file=None):
        """加载配置"""
        # 默认配置
        default_config = {
            "enabled": True,
            "forecast_days": 7,
            "include_yesterday": True,
            "output_filename": "weather_chart_{date}.png",
            "output_dir": "./output",
            "device_push": {
                "enabled": False,
                "device_idx": -1
            },
            "cleanup": {
                "enabled": True,
                "keep_files": 3
            },
            "notification": {
                "enabled": False,
                "webhook_url": "",
                "success_message": "天气预报走势图生成成功",
                "error_message": "天气预报走势图生成失败"
            },
            "schedule": {
                "times": ["08:00", "20:00"],  # 每天运行时间
                "timezone": "Asia/Shanghai"
            }
        }
        
        # 如果指定了配置文件，尝试加载
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                # 合并配置
                default_config.update(user_config)
                logger.info(f"已加载配置文件: {config_file}")
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
        
        return default_config
    
    def setup_logging(self):
        """设置日志"""
        log_level = logging.INFO if self.config.get("enabled", True) else logging.WARNING
        logging.getLogger().setLevel(log_level)
    
    def ensure_output_dir(self):
        """确保输出目录存在"""
        output_dir = Path(self.config["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir
    
    def generate_weather_chart(self):
        """生成天气预报走势图"""
        try:
            logger.info("开始生成天气预报走势图...")
            
            # 创建输出目录
            output_dir = self.ensure_output_dir()
            
            # 生成输出文件名
            date_str = datetime.now().strftime("%Y%m%d_%H%M")
            filename = self.config["output_filename"].format(date=date_str)
            output_path = output_dir / filename
            
            # 创建天气图表生成器
            chart = WeatherChart(
                location=config.CONFIG_USER_LOCATION,
                qweather_host=config.QWEATHER_HOST,
                qweather_key=config.QWEATHER_KEY
            )
            
            # 加载天气数据
            logger.info(f"加载 {self.config['forecast_days']} 天的天气预报数据...")
            chart.load_weather_data(
                days=self.config['forecast_days'],
                include_yesterday=self.config['include_yesterday']
            )
            
            # 生成图表
            logger.info("正在生成图表...")
            chart.create_image()
            chart.save_image(str(output_path))
            
            logger.info(f"图表已保存到: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"生成天气预报走势图失败: {e}")
            raise
    
    def push_to_device(self, image_path):
        """推送到设备"""
        if not self.config["device_push"]["enabled"]:
            logger.info("设备推送已禁用")
            return False
            
        try:
            logger.info("正在推送天气走势图到设备...")
            logger.info(f"图片文件: {image_path}")
            
            # 导入设备推送工具
            from device_push import push_image_to_device
            
            # 获取设备配置
            device_idx = self.config["device_push"]["device_idx"]
            
            # 处理设备ID
            if device_idx >= 0 and config.DOT_DEVICE_ID:
                # 从逗号分隔的设备ID列表中选择指定索引的设备
                device_ids = [d.strip() for d in config.DOT_DEVICE_ID.split(',')]
                if device_idx < len(device_ids):
                    target_device_id = device_ids[device_idx]
                else:
                    target_device_id = device_ids[0]  # 默认使用第一个设备
                    logger.warning(f"设备索引 {device_idx} 超出范围，使用第一个设备")
            else:
                target_device_id = config.DOT_DEVICE_ID
            
            # 检查是否需要调整图片尺寸
            resize_for_device = self.config.get("device_push", {}).get("resize_for_device", True)
            
            if resize_for_device:
                logger.info("调整图片尺寸以适配设备 (296x152)...")
                from PIL import Image
                from device_push import blackwhite_image
                import base64
                import requests
                from io import BytesIO
                
                # 加载并调整图片
                image = Image.open(image_path)
                resized_image = image.resize((296, 152), Image.Resampling.LANCZOS)
                
                # 转换为黑白
                bw_image = blackwhite_image(resized_image)
                
                # 推送到设备
                img_buffer = BytesIO()
                bw_image.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                image_content = img_buffer.getvalue()
                
                # 发送请求
                url = 'https://dot.mindreset.tech/api/open/image'
                payload = {
                    "deviceId": target_device_id,
                    "image": base64.b64encode(image_content).decode('utf-8'),
                    "refreshNow": True,
                    "border": 0,
                    "ditherType": "NONE",
                    "link": "https://dot.mindreset.tech"
                }
                
                headers = {
                    'Authorization': f'Bearer {config.DOT_APP_KEY}',
                    'Content-Type': 'application/json'
                }
                
                response = requests.post(url, json=payload, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    logger.info(f"设备推送成功 (设备: {target_device_id})")
                    return True
                else:
                    logger.error(f"设备推送失败: {response.status_code} - {response.text}")
                    return False
            else:
                # 推送原始尺寸图片
                success = push_image_to_device(image_path, target_device_id, config.DOT_APP_KEY)
                if success:
                    logger.info("设备推送成功")
                return success
            
        except Exception as e:
            logger.error(f"设备推送失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def cleanup_old_files(self):
        """清理旧文件"""
        if not self.config["cleanup"]["enabled"]:
            logger.info("文件清理已禁用")
            return
            
        try:
            output_dir = Path(self.config["output_dir"])
            keep_files = self.config["cleanup"]["keep_files"]
            
            # 获取所有PNG文件，按修改时间排序
            png_files = list(output_dir.glob("weather_chart_*.png"))
            png_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # 删除多余的文件
            if len(png_files) > keep_files:
                files_to_delete = png_files[keep_files:]
                for file in files_to_delete:
                    file.unlink()
                    logger.info(f"已删除旧文件: {file}")
                    
        except Exception as e:
            logger.error(f"清理旧文件失败: {e}")
    
    def send_notification(self, success, message="", image_path=""):
        """发送通知"""
        if not self.config["notification"]["enabled"]:
            return
            
        try:
            webhook_url = self.config["notification"]["webhook_url"]
            if not webhook_url:
                logger.warning("通知已启用但未配置webhook URL")
                return
                
            import requests
            
            if success:
                text = self.config["notification"]["success_message"]
                color = "good"
            else:
                text = self.config["notification"]["error_message"]
                color = "danger"
                
            if message:
                text += f"\n详情: {message}"
                
            # 构建通知内容
            payload = {
                "text": f"🌤️ 天气预报走势图通知",
                "attachments": [
                    {
                        "color": color,
                        "fields": [
                            {
                                "title": "状态",
                                "value": "✅ 成功" if success else "❌ 失败",
                                "short": True
                            },
                            {
                                "title": "时间",
                                "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "short": True
                            }
                        ],
                        "text": text
                    }
                ]
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info("通知发送成功")
            else:
                logger.warning(f"通知发送失败: {response.status_code}")
                
        except Exception as e:
            logger.error(f"发送通知失败: {e}")
    
    def run(self):
        """运行定时任务"""
        if not self.config.get("enabled", True):
            logger.info("定时任务已禁用")
            return
            
        start_time = datetime.now()
        logger.info("=" * 50)
        logger.info("🌤️ 天气预报走势图定时任务开始执行")
        logger.info(f"⏰ 开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"📍 位置: {config.CONFIG_USER_LOCATION}")
        logger.info(f"📅 预报天数: {self.config['forecast_days']}")
        logger.info(f"📁 输出目录: {self.config['output_dir']}")
        logger.info("=" * 50)
        
        success = False
        image_path = ""
        error_message = ""
        
        try:
            # 生成天气图表
            image_path = self.generate_weather_chart()
            
            # 推送到设备
            if self.config["device_push"]["enabled"]:
                push_success = self.push_to_device(image_path)
                if not push_success:
                    logger.warning("设备推送失败，但图表生成成功")
            
            # 清理旧文件
            self.cleanup_old_files()
            
            success = True
            logger.info("✅ 定时任务执行成功")
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"❌ 定时任务执行失败: {error_message}")
            
        finally:
            # 发送通知
            self.send_notification(success, error_message, image_path)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info("=" * 50)
            logger.info(f"⏰ 结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"⏱️ 执行时长: {duration:.2f} 秒")
            logger.info(f"📁 图表文件: {image_path if success else '未生成'}")
            logger.info("🎉 定时任务执行完成")
            logger.info("=" * 50)
    
    def create_sample_config(self, output_path="weather_scheduler_config.json"):
        """创建示例配置文件"""
        sample_config = {
            "enabled": True,
            "forecast_days": 7,
            "include_yesterday": True,
            "output_filename": "weather_chart_{date}.png",
            "output_dir": "./output",
            "device_push": {
                "enabled": True,
                "device_idx": 0,
                "resize_for_device": True
            },
            "cleanup": {
                "enabled": True,
                "keep_files": 5
            },
            "notification": {
                "enabled": False,
                "webhook_url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
                "success_message": "天气预报走势图生成并推送成功",
                "error_message": "天气预报走势图生成失败，请检查日志"
            },
            "schedule": {
                "times": ["08:00", "20:00"],
                "timezone": "Asia/Shanghai"
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(sample_config, f, ensure_ascii=False, indent=2)
            
        print(f"示例配置文件已创建: {output_path}")
        print("请根据需要修改配置，然后运行:")
        print(f"python3 {__file__} --config {output_path}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='天气预报走势图定时任务管理器')
    parser.add_argument('--config', help='配置文件路径')
    parser.add_argument('--create-sample-config', action='store_true', 
                       help='创建示例配置文件')
    parser.add_argument('--days', type=int, default=7,
                       help='预报天数 (默认: 7)')
    parser.add_argument('--include-yesterday', action='store_true',
                       help='包含昨天数据')
    parser.add_argument('--no-device-push', action='store_true',
                       help='禁用设备推送')
    parser.add_argument('--output-dir', default='./output',
                       help='输出目录 (默认: ./output)')
    
    args = parser.parse_args()
    
    # 创建示例配置文件
    if args.create_sample_config:
        scheduler = WeatherScheduler()
        scheduler.create_sample_config()
        return
    
    # 创建调度器
    scheduler = WeatherScheduler(args.config)
    
    # 命令行参数覆盖配置
    if args.days:
        scheduler.config['forecast_days'] = args.days
    if args.include_yesterday:
        scheduler.config['include_yesterday'] = True
    if args.no_device_push:
        scheduler.config['device_push']['enabled'] = False
    if args.output_dir:
        scheduler.config['output_dir'] = args.output_dir
    
    # 运行任务
    scheduler.run()


if __name__ == '__main__':
    main()