import sys
import os
import json
from datetime import datetime
from typing import List
import urllib.parse

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
from dot_calendar import DotCalendar
from dingtalk_caldav_client import DingtalkCalDAVClient


def get_todolist_from_calendar_param(calendar_param: str) -> List[str]:
    """Get todo list from calendar parameter"""
    if not calendar_param:
        return []
        
    try:
        calendar = json.loads(calendar_param)
        todolist = []
        is_next_day = False
        next_day_time = int(datetime.strptime(
            datetime.now().strftime('%Y-%m-%d 23:59:59'), 
            '%Y-%m-%d %H:%M:%S'
        ).timestamp() * 1000)
        
        for event in calendar:
            if not is_next_day and event['time'] > next_day_time:
                todolist.append('')
                is_next_day = True
                
            todo = f"{event['timeLabel']} {event['title']}"
            if event.get('location'):
                todo += f"({event['location']})"
                
            if not todolist or todolist[-1] != todo:
                todolist.append(todo)
                
        return todolist
    except (json.JSONDecodeError, KeyError):
        return []


def get_todolist_from_dingtalk() -> List[str]:
    """Get todo list from DingTalk calendar"""
    if not config.DINGTALK_CALDAV_USER or not config.DINGTALK_CALDAV_PASS:
        return []
        
    try:
        client = DingtalkCalDAVClient(config.DINGTALK_CALDAV_USER, config.DINGTALK_CALDAV_PASS)
        events = client.get_all_events(
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            datetime.now().strftime('%Y-%m-%d 00:00:00')
        )
        
        todolist = []
        index_day = datetime.now().day
        
        for event in events:
            if 'SUMMARY' in event and 'DTSTART' in event:
                event_date = datetime.fromtimestamp(event['DTSTART'])
                if event_date.day != index_day:
                    todolist.append("")
                    index_day = event_date.day
                    
                todolist.append(f"{event_date.strftime('%H:%M')} {event['SUMMARY']}")
                
        client.close()
        return todolist
    except Exception:
        return []


def main():
    """Main function"""
    # Parse query parameters (in a real web app, this would come from the request)
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--token', help='Security token')
    parser.add_argument('--calendar', help='Calendar data in JSON format')
    parser.add_argument('--dotsync', type=int, default=0, help='Sync to Dot device')
    parser.add_argument('--device_idx', type=int, default=-1, help='Device index')
    args = parser.parse_args()
    
    # Token verification
    if not args.token or args.token != config.DOT_CALENDAR_TOKEN:
        print('404')
        return
    
    # Get todo list
    todolist = []
    if args.calendar:
        todolist = get_todolist_from_calendar_param(args.calendar)
    elif config.DINGTALK_CALDAV_USER and config.DINGTALK_CALDAV_PASS:
        todolist = get_todolist_from_dingtalk()
    
    # Create calendar
    dot_calendar = DotCalendar(
        config.DOT_DEVICE_ID,
        config.DOT_APP_KEY,
        config.CONFIG_USER_LOCATION,
        config.QWEATHER_HOST,
        config.QWEATHER_KEY,
        todolist
    )
    
    # Load weather data, create image and output
    print("Loading weather data...")
    dot_calendar.load_weather_data()
    print(f"Loaded {len(dot_calendar.data.get('daily', []))} days of weather forecast")
    if dot_calendar.data.get('daily'):
        first_day = dot_calendar.data['daily'][0]
        print(f"First day forecast: {first_day.get('fxDate', 'N/A')} - "
              f"Day: {first_day.get('textDay', 'N/A')}, Night: {first_day.get('textNight', 'N/A')}, "
              f"Temp: {first_day.get('tempMin', 'N/A')}°C ~ {first_day.get('tempMax', 'N/A')}°C")
    print("Creating image...")
    dot_calendar.create_image()
    print("Outputting image...")
    dot_calendar.output(bool(args.dotsync))
    
    print("Calendar generated successfully")


if __name__ == '__main__':
    main()