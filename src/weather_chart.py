import math
import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont

from utils import W2FileCache


class WeatherChart:
    """天气预报走势图生成器 - 适配 Dot 设备 (296x152)"""
    
    # 图表配置
    CHART_WIDTH = 296
    CHART_HEIGHT = 152
    
    # 边距配置 (紧凑布局)
    MARGIN = 12       # 左右边距
    TOP_MARGIN = 5    # 顶部留白
    BOTTOM_MARGIN = 28 # 底部留给日期和图标
    
    # 字体大小 - 适配小屏幕，像素级对齐
    # 标题通常不需要，或者非常小
    TITLE_FONT_SIZE = 10 
    AXIS_LABEL_FONT_SIZE = 9
    TEMP_FONT_SIZE = 9
    DATE_FONT_SIZE = 9
    ICON_FONT_SIZE = 12
    
    # 颜色配置 (为黑白屏优化，但内部仍使用RGB绘制以便调试，最后转二值)
    BACKGROUND_COLOR = (255, 255, 255)
    TEXT_COLOR = (0, 0, 0)
    GRID_COLOR = (180, 180, 180) # 浅灰网格
    HIGH_TEMP_COLOR = (0, 0, 0)  # 黑色
    LOW_TEMP_COLOR = (0, 0, 0)   # 黑色
    
    # 历史数据颜色 (在二值化后，灰色会变成黑色或白色，这里主要用于逻辑区分，二值化算法可调整)
    HISTORICAL_COLOR = (100, 100, 100) 
    HISTORICAL_TEMP_COLOR = (80, 80, 80)
    
    def __init__(self, location: str = '', qweather_host: str = '', qweather_key: str = ''):
        self.location = location
        self.qweather_host = qweather_host
        self.qweather_key = qweather_key
        
        # 字体路径
        self.fonts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'fonts')
        self.text_font = os.path.join(self.fonts_dir, 'fusion-pixel-12px-monospaced-zh_hans.ttf')
        self.icon_font = os.path.join(self.fonts_dir, 'qweather-icons.ttf')
        
        # 初始化数据
        self.weather_data: List[Dict[str, Any]] = []
        self.image: Optional[Image.Image] = None

    def get_weather_font(self, code: str) -> str:
        """根据天气代码获取天气图标字体字符"""
        weather_code = {
            '100': '\uF101',  # 晴
            '101': '\uF102',  # 多云
            '102': '\uF103',  # 少云
            '103': '\uF104',  # 晴间多云
            '104': '\uF105',  # 阴
            '150': '\uF106',  # 晴
            '151': '\uF107',  # 多云
            '152': '\uF108',  # 少云
            '153': '\uF109',  # 晴间多云
            '154': '\uF105',  # 阴
            '300': '\uF1D5',  # 阵雨
            '301': '\uF1D6',  # 强阵雨
            '302': '\uF1D7',  # 雷阵雨
            '303': '\uF1D8',  # 强雷阵雨
            '304': '\uF1D9',  # 雷阵雨伴有冰雹
            '305': '\uF1DA',  # 小雨
            '306': '\uF1DB',  # 中雨
            '307': '\uF1DC',  # 大雨
            '308': '\uF1DD',  # 极端降雨
            '309': '\uF1DE',  # 毛毛雨/细雨
            '310': '\uF1DF',  # 暴雨
            '311': '\uF1E0',  # 大暴雨
            '312': '\uF1E1',  # 特大暴雨
            '313': '\uF1E2',  # 冻雨
            '314': '\uF1E3',  # 小到中雨
            '315': '\uF1E4',  # 中到大雨
            '316': '\uF1E5',  # 大到暴雨
            '317': '\uF1E6',  # 暴雨到大暴雨
            '318': '\uF1E7',  # 大暴雨到特大暴雨
            '350': '\uF1E8',  # 阵雪
            '351': '\uF1E9',  # 小雪
            '399': '\uF1EA',  # 雨
            '400': '\uF1EB',  # 小雪
            '401': '\uF1EC',  # 中雪
            '402': '\uF1ED',  # 大雪
            '403': '\uF1EE',  # 暴雪
            '404': '\uF1EF',  # 雨夹雪
            '405': '\uF1F0',  # 雨雪天气
            '406': '\uF1F1',  # 阵雨夹雪
            '407': '\uF1F2',  # 阵雪
            '408': '\uF1F3',  # 小到中雪
            '409': '\uF1F4',  # 中到大雪
            '410': '\uF1F5',  # 大到暴雪
            '456': '\uF1F6',  # 阵雨夹雪
            '457': '\uF1F7',  # 阵雪
            '499': '\uF1F8',  # 雪
            '500': '\uF1F9',  # 浮尘
            '501': '\uF1FA',  # 扬沙
            '502': '\uF1FB',  # 沙尘暴
            '503': '\uF1FC',  # 强沙尘暴
            '504': '\uF1FD',  # 尘卷风
            '507': '\uF1FE',  # 沙尘
            '508': '\uF1FF',  # 强沙尘
            '509': '\uF200',  # 浓雾
            '510': '\uF201',  # 强浓雾
            '511': '\uF202',  # 中度霾
            '512': '\uF203',  # 重度霾
            '513': '\uF204',  # 严重霾
            '514': '\uF205',  # 大雾
            '515': '\uF206',  # 特强浓雾
            '900': '\uF207',  # 热
            '901': '\uF208',  # 冷
            '999': '\uF146'   # 未知
        }
        return weather_code.get(code, '\uF146')

    def qweather_get_daily(self, location: str, days: str = '15d') -> Dict[str, Any]:
        """从和风天气API获取每日天气预报数据"""
        cache_key = f'qweather_daily_{location}_{days}'
        data = W2FileCache.get_cache(cache_key)
        if data is not None:
            return data

        try:
            url = f'https://{self.qweather_host}/v7/weather/{days}?location={location}&key={self.qweather_key}'
            response = requests.get(url, timeout=30)
            data = response.json()
            W2FileCache.set_cache(cache_key, data, 60 * 30)  # 缓存30分钟
            return data
        except requests.RequestException as e:
            raise Exception(f"获取天气数据失败: {str(e)}")

    def qweather_get_historical(self, location: str, date: str) -> Dict[str, Any]:
        """从和风天气API获取历史天气数据"""
        cache_key = f'qweather_historical_{location}_{date}'
        data = W2FileCache.get_cache(cache_key)
        if data is not None:
            return data

        try:
            url1 = f'https://{self.qweather_host}/v7/historical/weather?location={location}&date={date}&key={self.qweather_key}'
            try:
                response1 = requests.get(url1, timeout=30)
                if response1.status_code == 200:
                    data = response1.json()
                    if data.get('code') == '200':
                        W2FileCache.set_cache(cache_key, data, 60 * 60 * 6)  
                        print(f"✅ 成功使用API KEY认证获取历史数据")
                        return data
            except:
                pass
            
            # 降级到估算
            return self._fallback_historical_old_api(location, date)
                
        except Exception as e:
            print(f"⚠️ 获取历史天气数据失败，使用降级方案: {str(e)}")
            return self._fallback_historical_old_api(location, date)

    def _fallback_historical_old_api(self, location: str, date: str) -> Dict[str, Any]:
        """降级方案：尝试使用旧的预报API获取估算的历史数据"""
        try:
            url = f'https://{self.qweather_host}/v7/weather/{date}?location={location}&key={self.qweather_key}'
            response = requests.get(url, timeout=30)
            data = response.json()
            
            if data.get('code') == '200' and data.get('daily'):
                daily_data = data['daily'][0] if data['daily'] else {}
                return {
                    'code': '200',
                    'weatherDaily': [daily_data],
                    'isEstimate': True,
                    'message': '估算数据（基于预报模型）'
                }
            else:
                raise Exception(f"降级API也失败: {data.get('code')}")
        except Exception as e:
            raise Exception(f"所有历史数据获取方案都失败: {str(e)}")

    def save_historical_data_cache(self, date: str, weather_data: Dict[str, Any]):
        """保存今日天气数据作为历史缓存"""
        today = datetime.now().strftime('%Y-%m-%d')
        cache_key = f'qweather_historical_real_{self.location}_{today}'
        
        historical_cache = {
            'code': '200',
            'weatherDaily': [weather_data],
            'isRealData': True,
            'savedAt': datetime.now().isoformat()
        }
        W2FileCache.set_cache(cache_key, historical_cache, 60 * 60 * 24)

    def load_weather_data(self, days: int = 15, include_yesterday: bool = True) -> 'WeatherChart':
        """加载天气预报数据"""
        all_data = []
        
        if include_yesterday:
            yesterday = datetime.now() - timedelta(days=1)
            yesterday_str = yesterday.strftime('%Y%m%d')
            
            cache_key = f'qweather_historical_real_{self.location}_{yesterday.strftime("%Y-%m-%d")}'
            cached_historical = W2FileCache.get_cache(cache_key)
            
            historical_success = False
            
            if cached_historical and cached_historical.get('isRealData'):
                historical_data = cached_historical
                if historical_data.get('weatherDaily'):
                    daily_data = historical_data['weatherDaily'][0]
                    yesterday_data = self._create_weather_item(
                        daily_data['fxDate'], daily_data, is_historical=True, source='真实历史(缓存)'
                    )
                    all_data.append(yesterday_data)
                    historical_success = True
            
            if not historical_success:
                try:
                    historical_data = self.qweather_get_historical(self.location, yesterday_str)
                    if historical_data.get('code') == '200' and historical_data.get('weatherDaily'):
                        daily_data = historical_data['weatherDaily'][0]
                        source = '真实历史(API)' if not historical_data.get('isEstimate') else '估算历史'
                        yesterday_data = self._create_weather_item(
                            yesterday.strftime('%Y-%m-%d'), daily_data, 
                            is_historical=True, source=source, 
                            is_estimate=historical_data.get('isEstimate', False)
                        )
                        all_data.append(yesterday_data)
                        historical_success = True
                except:
                    pass
            
            if not historical_success and include_yesterday:
                # 预报估算
                days_str = f'{days}d'
                try:
                    forecast_data = self.qweather_get_daily(self.location, days_str)
                    if forecast_data.get('code') == '200' and forecast_data.get('daily'):
                        first_day_data = forecast_data['daily'][0]
                        yesterday_date = datetime.strptime(first_day_data['fxDate'], '%Y-%m-%d') - timedelta(days=1)
                        yesterday_data = self._create_weather_item(
                            yesterday_date.strftime('%Y-%m-%d'), first_day_data,
                            is_historical=True, is_estimate=True, source='预报估算'
                        )
                        all_data.append(yesterday_data)
                except:
                    pass
        
        # 获取未来预报
        days_str = f'{days}d'
        try:
            forecast_data = self.qweather_get_daily(self.location, days_str)
            if forecast_data.get('code') == '200':
                forecast_daily = forecast_data.get('daily', [])
                for day_data in forecast_daily:
                    day_item = self._create_weather_item(
                        day_data['fxDate'], day_data, is_historical=False, source='预报数据'
                    )
                    all_data.append(day_item)
                    if day_data['fxDate'] == datetime.now().strftime('%Y-%m-%d'):
                        self.save_historical_data_cache(day_data['fxDate'], day_data)
        except Exception as e:
            raise Exception(f"获取预报数据失败: {str(e)}")
        
        self.weather_data = all_data
        return self

    def _create_weather_item(self, date_str, src_data, is_historical=False, is_estimate=False, source=''):
        return {
            'fxDate': date_str,
            'tempMax': src_data.get('tempMax', 'N/A'),
            'tempMin': src_data.get('tempMin', 'N/A'),
            'iconDay': src_data.get('iconDay', '999'),
            'textDay': src_data.get('textDay', ''),
            'iconNight': src_data.get('iconNight', '999'),
            'textNight': src_data.get('textNight', ''),
            'isHistorical': is_historical,
            'isEstimate': is_estimate,
            'source': source
        }

    def calculate_chart_bounds(self) -> Tuple[float, float, float, float]:
        if not self.weather_data:
            return 0, 0, 0, 0
        temps_high = [float(day['tempMax']) for day in self.weather_data]
        temps_low = [float(day['tempMin']) for day in self.weather_data]
        temp_min = min(temps_low)
        temp_max = max(temps_high)
        temp_range = temp_max - temp_min
        if temp_range < 5: temp_range = 5
        temp_min -= 2
        temp_max += 2
        return math.floor(temp_min), math.ceil(temp_max)

    def create_image(self) -> 'WeatherChart':
        if not self.weather_data:
            raise ValueError("没有天气数据")
        
        self.image = Image.new('RGB', (self.CHART_WIDTH, self.CHART_HEIGHT), self.BACKGROUND_COLOR)
        draw = ImageDraw.Draw(self.image)
        
        try:
            # title_font = ImageFont.truetype(self.text_font, self.TITLE_FONT_SIZE)
            label_font = ImageFont.truetype(self.text_font, self.AXIS_LABEL_FONT_SIZE)
            temp_font = ImageFont.truetype(self.text_font, self.TEMP_FONT_SIZE)
            date_font = ImageFont.truetype(self.text_font, self.DATE_FONT_SIZE)
            icon_font = ImageFont.truetype(self.icon_font, self.ICON_FONT_SIZE)
        except:
            label_font = ImageFont.load_default()
            temp_font = ImageFont.load_default()
            date_font = ImageFont.load_default()
            icon_font = ImageFont.load_default()
        
        chart_left = self.MARGIN + 8
        chart_right = self.CHART_WIDTH - self.MARGIN
        chart_top = self.TOP_MARGIN
        chart_bottom = self.CHART_HEIGHT - self.BOTTOM_MARGIN
        chart_width = chart_right - chart_left
        chart_height = chart_bottom - chart_top
        
        temp_min, temp_max = self.calculate_chart_bounds()
        temp_range = temp_max - temp_min
        
        # Y轴网格 (2条线)
        y_steps = 2
        for i in range(y_steps + 1):
            y = chart_top + (chart_height * i / y_steps)
            temp = temp_max - (temp_range * i / y_steps)
            draw.line([(chart_left, y), (chart_right, y)], fill=self.GRID_COLOR, width=1)
            draw.text((2, y - 5), f"{temp:.0f}", fill=self.TEXT_COLOR, font=label_font)
        
        num_days = len(self.weather_data)
        if num_days > 0:
            x_step = chart_width / (num_days - 1) if num_days > 1 else 0
            
            # X轴日期和图标
            for i, day_data in enumerate(self.weather_data):
                x = chart_left + x_step * i if num_days > 1 else chart_left + chart_width // 2
                draw.line([(x, chart_top), (x, chart_bottom)], fill=self.GRID_COLOR, width=1)
                
                # 隔天显示日期，避免拥挤，但始终显示图标
                show_date = True
                if num_days > 10 and i % 2 != 0:
                    show_date = False
                
                if show_date:
                    date_str = datetime.strptime(day_data['fxDate'], '%Y-%m-%d').strftime('%d')
                    text_width = draw.textbbox((0, 0), date_str, font=date_font)[2] - draw.textbbox((0, 0), date_str, font=date_font)[0]
                    draw.text((x - text_width // 2, chart_bottom + 12), date_str, fill=self.TEXT_COLOR, font=date_font)
                
                # 图标
                weather_icon = self.get_weather_font(day_data['iconDay'])
                icon_width = draw.textbbox((0, 0), weather_icon, font=icon_font)[2] - draw.textbbox((0, 0), weather_icon, font=icon_font)[0]
                draw.text((x - icon_width // 2, chart_bottom + 1), weather_icon, fill=self.TEXT_COLOR, font=icon_font)
        
            # 温度曲线
            high_points = []
            low_points = []
            for i, day_data in enumerate(self.weather_data):
                x = chart_left + x_step * i if num_days > 1 else chart_left + chart_width // 2
                high_y = chart_top + chart_height * (temp_max - float(day_data['tempMax'])) / temp_range
                low_y = chart_top + chart_height * (temp_max - float(day_data['tempMin'])) / temp_range
                high_points.append((x, high_y))
                low_points.append((x, low_y))
            
            draw.line(high_points, fill=self.HIGH_TEMP_COLOR, width=1)
            draw.line(low_points, fill=self.LOW_TEMP_COLOR, width=1)
            
            # 点和数值
            for i in range(num_days):
                x, hy = high_points[i]
                x, ly = low_points[i]
                
                draw.rectangle([x-1, hy-1, x+1, hy+1], fill=self.HIGH_TEMP_COLOR)
                draw.rectangle([x-1, ly-1, x+1, ly+1], fill=self.LOW_TEMP_COLOR)
                
                # 数值隔天显示
                if num_days <= 10 or i % 2 == 0:
                    draw.text((x-6, hy-10), f"{self.weather_data[i]['tempMax']}", fill=self.HIGH_TEMP_COLOR, font=temp_font)
                    draw.text((x-6, ly+2), f"{self.weather_data[i]['tempMin']}", fill=self.LOW_TEMP_COLOR, font=temp_font)
        
        return self

    def save_image(self, filename: str = 'weather_chart.png') -> 'WeatherChart':
        if not self.image: raise ValueError("没有生成图像")
        self.image.save(filename, format='PNG')
        print(f"天气预报走势图已保存到 {filename}")
        return self

    def get_image_bytes(self) -> bytes:
        if not self.image: raise ValueError("没有生成图像")
        from io import BytesIO
        buffer = BytesIO()
        self.image.save(buffer, format='PNG')
        return buffer.getvalue()
        
    def blackwhite_image(self, image: Image.Image = None) -> Image.Image:
        """Convert image to black and white"""
        tgt = image if image else self.image
        if not tgt: raise ValueError("没有生成图像")
        
        if tgt.mode != 'RGBA': rgba = tgt.convert('RGBA')
        else: rgba = tgt
        
        bw = Image.new('RGB', rgba.size, (255, 255, 255))
        threshold = 200
        for x in range(rgba.width):
            for y in range(rgba.height):
                r, g, b, a = rgba.getpixel((x, y))
                if a < 128: bw.putpixel((x, y), (255, 255, 255))
                else:
                    gray = int(0.299 * r + 0.587 * g + 0.114 * b)
                    if gray < threshold: bw.putpixel((x, y), (0, 0, 0))
                    else: bw.putpixel((x, y), (255, 255, 255))
        return bw

def main():
    import config
    # 模拟数据
    chart = WeatherChart(config.CONFIG_USER_LOCATION, config.QWEATHER_HOST, config.QWEATHER_KEY)
    print("加载数据...")
    chart.load_weather_data(days=15)
    print("生成图表...")
    chart.create_image()
    chart.save_image('weather_forecast_chart.png')
    print("完成")

if __name__ == '__main__':
    main()