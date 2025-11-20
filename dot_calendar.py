import math
import os
import requests
import json
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont
import base64
from io import BytesIO

from utils import W2FileCache
from models import WeatherInfo, Event, WeatherDaily


class DotCalendar:
    """Main DotCalendar class for generating weather calendar images"""

    # Constants
    BG_WIDTH = 296
    BG_HEIGHT = 152
    CALENDAR_START_LEFT = 2
    CALENDAR_START_TOP = -3
    GRID_WIDTH = 18
    GRID_HEIGHT = 25.5  # Reduced from 27 to 24 to allow more compact layout
    HEADER_HEIGHT = 17
    HEADER_FONT_SIZE = 9
    DAY_FONT_SIZE = 9
    DAY_ICON_MARGIN = 2
    ICON_FONT_SIZE = 10
    TODO_FONT_SIZE = 10
    TODO_MAX_LINE = 5

    def __init__(self, dot_device_id: str = '', dot_appkey: str = '', location: str = '',
                 qweather_host: str = '', qweather_key: str = '', todolist: List[str] = None):
        self.location = location
        self.qweather_host = qweather_host
        self.qweather_key = qweather_key
        self.dot_device_id = dot_device_id
        self.dot_appkey = dot_appkey
        self.todolist = todolist or []

        # Font paths
        self.fonts_dir = os.path.join(os.path.dirname(__file__), 'fonts')
        self.text_font = os.path.join(self.fonts_dir, 'fusion-pixel-12px-monospaced-zh_hans.ttf')
        self.number_font = os.path.join(self.fonts_dir, 'fusion-pixel-12px-monospaced-zh_hans.ttf')
        self.icon_font = os.path.join(self.fonts_dir, 'qweather-icons.ttf')

        # Initialize data
        self.params: List[WeatherInfo] = []
        self.data: Dict[str, Any] = {}
        self.image: Optional[Image.Image] = None

    def get_weather_font(self, code: str) -> str:
        """Get weather icon font character by code"""
        weather_code = {
            '100': '\uF101',
            '101': '\uF102',
            '102': '\uF103',
            '103': '\uF104',
            '104': '\uF105',
            '150': '\uF106',
            '151': '\uF107',
            '152': '\uF108',
            '153': '\uF109',
            '300': '\uF1D5',
            '301': '\uF1D6',
            '302': '\uF1D7',
            '303': '\uF1D8',
            '304': '\uF1D9',
            '305': '\uF1DA',
            '306': '\uF1DB',
            '307': '\uF1DC',
            '308': '\uF1DD',
            '309': '\uF1DE',
            '310': '\uF1DF',
            '311': '\uF1E0',
            '312': '\uF1E1',
            '313': '\uF1E2',
            '314': '\uF1E3',
            '315': '\uF1E4',
            '316': '\uF1E5',
            '317': '\uF1E6',
            '318': '\uF1E7',
            '350': '\uF1E8',
            '351': '\uF1E9',
            '399': '\uF1EA',
            '400': '\uF1EB',
            '401': '\uF1EC',
            '402': '\uF1ED',
            '403': '\uF1EE',
            '404': '\uF1EF',
            '405': '\uF1F0',
            '406': '\uF1F1',
            '407': '\uF1F2',
            '408': '\uF1F3',
            '409': '\uF1F4',
            '410': '\uF1F5',
            '456': '\uF1F6',
            '457': '\uF1F7',
            '499': '\uF1F8',
            '500': '\uF1F9',
            '501': '\uF1FA',
            '502': '\uF1FB',
            '503': '\uF1FC',
            '504': '\uF1FD',
            '507': '\uF1FE',
            '508': '\uF1FF',
            '509': '\uF200',
            '510': '\uF201',
            '511': '\uF202',
            '512': '\uF203',
            '513': '\uF204',
            '514': '\uF205',
            '515': '\uF206',
            '900': '\uF207',
            '901': '\uF208',
            '999': '\uF146'
        }
        return weather_code.get(code, '\uF1CC')

    def qweather_get_daily(self, location: str, days: str = '30d') -> Dict[str, Any]:
        """Get daily weather data from QWeather API"""
        cache_key = f'qweather_daily_{location}_{days}'
        data = W2FileCache.get_cache(cache_key)
        if data is not None:
            return data

        try:
            url = f'https://{self.qweather_host}/v7/weather/{days}?location={location}&key={self.qweather_key}'
            response = requests.get(url, timeout=30)
            data = response.json()
            W2FileCache.set_cache(cache_key, data, 60 * 5)  # Cache for 5 minutes
            return data
        except requests.RequestException as e:
            raise Exception(f"Failed to get weather data: {str(e)}")

    def load_weather_data(self, days: str = '30d') -> 'DotCalendar':
        """Load weather data"""
        self.data = self.qweather_get_daily(self.location, days)
        self.process_weather_data()
        return self

    def process_weather_data(self) -> None:
        """Process weather data for calendar display"""
        line = 0
        for i, forecast in enumerate(self.data.get('daily', [])):
            param = WeatherInfo(
                date=forecast['fxDate'],
                week=datetime.strptime(forecast['fxDate'], '%Y-%m-%d').weekday() + 1,
                day=int(datetime.strptime(forecast['fxDate'], '%Y-%m-%d').strftime('%d')),
                line=0,
                font_icon='',
                dx=0,
                dy=0
            )

            if param.week == 1 and i > 0:
                if line == 4:  # Maximum 5 lines
                    break
                line += 1

            # In PHP version, 0 represents Sunday, but in Python weekday() 6 represents Sunday
            # So we need to check if week is 7 (Sunday) and convert it to 7 for consistency
            # This condition should never be true with weekday() + 1, but keeping it for clarity
            if param.week == 0:
                param.week = 7

            param.line = line
            param.font_icon = self.get_weather_font(forecast['iconDay'])
            
            # If night weather has rain/snow/thunderstorm/fog, use night icon
            if any(char in forecast['textNight'] for char in ['雨', '雪', '雷', '雾']):
                param.font_icon = self.get_weather_font(forecast['iconNight'])
            elif (forecast['fxDate'] == datetime.now().strftime('%Y-%m-%d') and 
                  datetime.now().hour >= 17):
                # If today and after 5PM, use night icon
                param.font_icon = self.get_weather_font(forecast['iconNight'])

            param.dx = (param.week - 1) * self.GRID_WIDTH + 1
            param.dy = (param.line + 1) * self.GRID_HEIGHT - 3  # Reduced vertical spacing

            self.params.append(param)

        # Fill up to Sunday if needed
        if self.params:
            last_week = self.params[-1].week
            if last_week != 7:
                last_date = self.params[-1].date
                for i in range(last_week + 1, 8):
                    date_obj = datetime.strptime(last_date, '%Y-%m-%d')
                    new_date = date_obj.replace(day=date_obj.day + (i - last_week))
                    param = WeatherInfo(
                        date=new_date.strftime('%Y-%m-%d'),
                        week=i,
                        day=int(new_date.strftime('%d')),
                        line=line,
                        font_icon=self.get_weather_font('999'),
                        dx=(i - 1) * self.GRID_WIDTH + 1,
                        dy=(line + 1) * self.GRID_HEIGHT - 3  # Reduced vertical spacing
                    )
                    self.params.append(param)

    def create_image(self) -> 'DotCalendar':
        """Create the calendar image"""
        # Calculate calendar dimensions
        calendar_width = 7 * self.GRID_WIDTH
        max_line = max([p.line for p in self.params]) if self.params else 0
        calendar_height = self.HEADER_HEIGHT + ((max_line + 1) * self.GRID_HEIGHT)

        # Create transparent background
        self.image = Image.new('RGBA', (self.BG_WIDTH, self.BG_HEIGHT), (0, 0, 0, 0))
        
        # Draw calendar header
        self.draw_calendar_header(calendar_width)
        
        # Draw days and icons
        self.draw_days_and_icons(calendar_width)
        
        # Draw todos
        self.draw_todos(calendar_width)
        
        # Add weather info
        self.add_weather_info(calendar_width)
        
        return self

    def draw_calendar_header(self, calendar_width: int) -> None:
        """Draw calendar header with weekdays"""
        if not self.image:
            return
            
        draw = ImageDraw.Draw(self.image)
        try:
            font = ImageFont.truetype(self.text_font, self.HEADER_FONT_SIZE)
        except:
            font = ImageFont.load_default()

        header = ['一', '二', '三', '四', '五', '六', '日']
        for i, day in enumerate(header):
            x = self.BG_WIDTH - calendar_width + self.CALENDAR_START_LEFT + i * self.GRID_WIDTH + 1
            y = self.CALENDAR_START_TOP + self.HEADER_HEIGHT - 3
            try:
                draw.text((x, y), day, fill=(0, 0, 0), font=font)
            except UnicodeEncodeError:
                # Fallback to ASCII if Unicode is not supported
                ascii_day = ['M', 'T', 'W', 'T', 'F', 'S', 'S'][i]
                draw.text((x, y), ascii_day, fill=(0, 0, 0), font=font)

    def draw_days_and_icons(self, calendar_width: int) -> None:
        """Draw days and weather icons"""
        if not self.image:
            return
            
        draw = ImageDraw.Draw(self.image)
        
        try:
            number_font = ImageFont.truetype(self.number_font, self.DAY_FONT_SIZE)
            icon_font = ImageFont.truetype(self.icon_font, self.ICON_FONT_SIZE)
        except:
            number_font = ImageFont.load_default()
            icon_font = ImageFont.load_default()

        for param in self.params:
            # Draw day number
            day_x = (self.BG_WIDTH - calendar_width + self.CALENDAR_START_LEFT + param.dx + 
                     (4 if param.day < 10 else 0) + str(param.day).count('1') * 2)
            day_y = self.CALENDAR_START_TOP + self.HEADER_HEIGHT + param.dy
            try:
                draw.text((day_x, day_y), str(param.day), fill=(0, 0, 0), font=number_font)
            except UnicodeEncodeError:
                # Skip drawing if Unicode is not supported
                pass
            
            # Draw weather icon
            icon_x = self.BG_WIDTH - calendar_width + self.CALENDAR_START_LEFT + param.dx
            icon_y = (self.CALENDAR_START_TOP + self.HEADER_HEIGHT + param.dy - 
                      self.DAY_FONT_SIZE - self.DAY_ICON_MARGIN)
            try:
                draw.text((icon_x, icon_y), param.font_icon, fill=(0, 0, 0), font=icon_font)
            except UnicodeEncodeError:
                # Skip drawing if Unicode is not supported
                pass

    def draw_todos(self, calendar_width: int) -> int:
        """Draw todo list"""
        if not self.image:
            return 0
            
        draw = ImageDraw.Draw(self.image)
        try:
            font = ImageFont.truetype(self.text_font, self.TODO_FONT_SIZE)
        except:
            font = ImageFont.load_default()

        process_height = 3
        line_spacing = 3  # Increased from 2 to 3 for better line separation
        char_spacing = 1  # Add character spacing

        if not self.todolist:
            try:
                draw.text((30, 10 + self.TODO_FONT_SIZE), '近日无日程', fill=(0, 0, 0), font=font)
            except UnicodeEncodeError:
                # Fallback to ASCII if Unicode is not supported
                draw.text((30, 10 + self.TODO_FONT_SIZE), 'No schedule', fill=(0, 0, 0), font=font)
            process_height = 10 + self.TODO_FONT_SIZE + 10
        else:
            for i, line_text in enumerate(self.todolist):
                if i >= self.TODO_MAX_LINE:
                    break
                    
                if line_text == '':
                    # Draw separator line
                    draw.line([
                        (10, process_height + 3),
                        (self.BG_WIDTH - calendar_width - 10, process_height + 3)
                    ], fill=(0, 0, 0), width=1)
                    process_height += 6
                    continue

                # Create a separate image for the text line like PHP version does
                # This is a simplified approach to match the PHP version's textToImage function
                try:
                    # Draw text with character spacing
                    x_position = 3
                    for char in line_text:
                        draw.text((x_position, process_height), char, fill=(0, 0, 0), font=font)
                        # Calculate character width and add spacing
                        char_bbox = draw.textbbox((0, 0), char, font=font)
                        char_width = char_bbox[2] - char_bbox[0]
                        x_position += char_width + char_spacing
                except UnicodeEncodeError:
                    # Skip drawing if Unicode is not supported
                    pass
                # Calculate text height for line spacing
                text_bbox = draw.textbbox((0, 0), line_text, font=font)
                text_height = text_bbox[3] - text_bbox[1]
                # Increase line spacing - add both text height and additional spacing
                process_height += text_height + line_spacing

        return process_height

    def add_weather_info(self, calendar_width: int) -> None:
        """Add additional weather information"""
        process_height = self.draw_todos(calendar_width)
        
        if (process_height < self.BG_HEIGHT / 2 and 
            self.data and 'daily' in self.data and self.data['daily']):
            
            # Get precipitation info and temperature info
            extra_info = self.get_precipitation_info()
            warning_types = self.add_temperature_info()
            
            if warning_types and len(warning_types) > 2 and warning_types[2]:
                extra_info = warning_types[2] + extra_info
                
            if extra_info and self.image:
                # Draw extra weather info in the bottom right corner of the calendar area
                try:
                    font = ImageFont.truetype(self.text_font, self.TODO_FONT_SIZE)
                    draw = ImageDraw.Draw(self.image)
                    
                    # Calculate text dimensions
                    text_bbox = draw.textbbox((0, 0), extra_info, font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_height = text_bbox[3] - text_bbox[1]
                    
                    # Position in bottom right of calendar area (matching PHP version position)
                    # PHP version uses: self::BG_WIDTH - $calendarWidth - imagesx($extraImage) - 5
                    #                   self::BG_HEIGHT - 10 - 15 - 15 - imagesy($extraImage)
                    x = self.BG_WIDTH - calendar_width - text_width - 5
                    y = self.BG_HEIGHT - 10 - 15 - 15 - text_height
                    
                    # Ensure we don't exceed the image boundaries
                    x = max(0, min(x, self.BG_WIDTH - text_width - 2))  # Keep within image bounds
                    y = max(0, min(y, self.BG_HEIGHT - text_height - 2))  # Keep within image bounds
                    
                    try:
                        draw.text((x, y), extra_info, fill=(0, 0, 0), font=font)
                    except UnicodeEncodeError:
                        # Skip drawing if Unicode is not supported
                        pass
                except:
                    pass  # Font loading failed

    def get_precipitation_info(self) -> str:
        """Get precipitation information"""
        if not self.data or 'daily' not in self.data or not self.data['daily']:
            return ''
            
        forecast = self.data['daily'][0]
        
        # Check if today has rain/snow/thunderstorm/fog
        if any(char in forecast['textDay'] for char in ['雨', '雪', '雷', '雾']) or \
           any(char in forecast['textNight'] for char in ['雨', '雪', '雷', '雾']):
            # In a full implementation, we'd get recent precipitation data from the API
            # For now, we'll return a simple message
            return '今日有雨'
        
        # Check for future precipitation
        unsunny_tip = ''
        week = datetime.now().weekday()
        # Adjust week_label to match PHP's date('w') indexing (0=Sunday, 1=Monday, ...)
        week_label = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
        # Convert Python weekday to PHP format for correct indexing
        php_week = (week + 1) % 7  # Python: 0=Monday -> PHP: 1=Monday
        day_label = []
        is_next_week = False
        
        for i in range(14):  # Check next 14 days
            if (php_week + i) % 7 == 1:  # Monday is 1 in PHP date('w') format
                if not is_next_week:
                    is_next_week = True
                else:
                    break
            
            if i == 0:
                day_label.append('今天')
            elif i == 1:
                day_label.append('明天')
            elif i == 2:
                day_label.append('后天')
            else:
                prefix = '下' if is_next_week else ''
                day_label.append(prefix + week_label[(php_week + i) % 7])
        
        # Check forecasts
        for index, forecast in enumerate(self.data['daily']):
            day_str = day_label[index] if index < len(day_label) else f'{index}天后'
            
            if any(char in forecast['textDay'] for char in ['雨', '雪', '雷', '雾']):
                return day_str + '有' + forecast['textDay']
            elif any(char in forecast['textNight'] for char in ['雨', '雪', '雷', '雾']):
                return day_str + '夜间' + forecast['textNight']
        
        return unsunny_tip

    def add_temperature_info(self) -> List[str]:
        """Add temperature information"""
        if not self.data or 'daily' not in self.data or not self.data['daily']:
            return ['', '', '']
            
        forecast = self.data['daily'][0]
        
        # Placeholder for warning types (in a full implementation, this would call the warning API)
        warning_types = ['', '', '']
        
        # Determine which icon to show (day or night)
        if (any(char in forecast['textNight'] for char in ['雨', '雪', '雷', '雾']) or 
            datetime.now().hour >= 17):
            icon_today = self.get_weather_font(forecast['iconNight'])
        else:
            icon_today = self.get_weather_font(forecast['iconDay'])
        
        # Draw the large weather icon
        if self.image:
            draw = ImageDraw.Draw(self.image)
            try:
                icon_font = ImageFont.truetype(self.icon_font, 35)
                # Make sure the icon is within bounds (35 is the font size)
                y_position = self.BG_HEIGHT - 35 - 2  # Reduced margin from 5 to 2
                draw.text((3, y_position), icon_today, fill=(0, 0, 0), font=icon_font)
            except:
                pass  # Font loading failed
        
        # Draw min temperature info
        try:
            text_font = ImageFont.truetype(self.text_font, 10)
            temp_font = ImageFont.truetype(self.text_font, 20)
            
            # Calculate proper Y positions to keep text within bounds
            text_height = 10  # Approximate height of text with font size 10
            temp_height = 20  # Approximate height of text with font size 20
            
            # Ensure we have enough space at the bottom with proper margin
            margin = 2  # Reduced margin from 5 to 2
            base_y = self.BG_HEIGHT - max(text_height, temp_height) - margin
            
            # Min temperature label
            if self.image:
                draw = ImageDraw.Draw(self.image)
                draw.text((3 + 50, base_y - text_height), '最', fill=(0, 0, 0), font=text_font)
                draw.text((3 + 50, base_y), '低', fill=(0, 0, 0), font=text_font)
                # Min temperature value
                draw.text((3 + 50 + 15, base_y), f"{forecast['tempMin']}°", fill=(0, 0, 0), font=temp_font)
                
                # Max temperature label
                draw.text((3 + 50 + 15 + 45, base_y - text_height), '最', fill=(0, 0, 0), font=text_font)
                draw.text((3 + 50 + 15 + 45, base_y), '高', fill=(0, 0, 0), font=text_font)
                # Max temperature value
                draw.text((3 + 50 + 15 + 45 + 15, base_y), f"{forecast['tempMax']}°", fill=(0, 0, 0), font=temp_font)
        except:
            pass  # Font loading failed
        
        return warning_types

    def output(self, dotsync: bool = False) -> 'DotCalendar':
        """Output the image either to HTTP response or to Dot device"""
        if not self.image:
            return self
            
        # Convert to black and white
        bw_image = self.blackwhite_image(self.image)
        
        if dotsync and self.dot_device_id and self.dot_appkey:
            # Save image to bytes
            img_buffer = BytesIO()
            bw_image.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            image_content = img_buffer.getvalue()
            
            # Send to Dot devices
            for device_id in self.dot_device_id.split(','):
                try:
                    url = 'https://dot.mindreset.tech/api/open/image'
                    payload = {
                        "deviceId": device_id.strip(),
                        "image": base64.b64encode(image_content).decode('utf-8'),
                        "refreshNow": True,
                        "border": 0,
                        "ditherType": "NONE",
                        "link": "https://dot.mindreset.tech"
                    }
                    
                    headers = {
                        'Authorization': f'Bearer {self.dot_appkey}',
                        'Content-Type': 'application/json'
                    }
                    
                    response = requests.post(url, json=payload, headers=headers, timeout=30)
                    # Could add logging here if needed
                    
                except requests.RequestException:
                    # Silent fail like in PHP version
                    pass
                    
        else:
            # Save to file for demonstration
            bw_image.save('output.png', format='PNG')
            print("Image saved to output.png")
            
        return self

    def blackwhite_image(self, image: Image.Image) -> Image.Image:
        """Convert image to black and white"""
        # Work with RGBA image to properly handle transparency
        if image.mode != 'RGBA':
            rgba_image = image.convert('RGBA')
        else:
            rgba_image = image
        
        # Create new image with white background
        bw_image = Image.new('RGB', rgba_image.size, (255, 255, 255))
        
        # Threshold for determining black vs white
        threshold = 200
        
        # Process each pixel
        for x in range(rgba_image.width):
            for y in range(rgba_image.height):
                r, g, b, a = rgba_image.getpixel((x, y))
                # If pixel is transparent, keep it white
                if a < 128:  # Transparent or semi-transparent
                    continue
                # If pixel is dark enough, make it black
                if (r + g + b) / 3 < threshold:
                    bw_image.putpixel((x, y), (0, 0, 0))
                    
        return bw_image