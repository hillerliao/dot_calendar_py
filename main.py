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

# Try to import optional calendar clients
try:
    from icloud_caldav_client import ICloudCalDAVClient
    ICLOUD_AVAILABLE = True
except ImportError:
    ICloudCalDAVClient = None
    ICLOUD_AVAILABLE = False

try:
    from google_caldav_client import GoogleCalDAVClient
    GOOGLE_AVAILABLE = True
except ImportError:
    GoogleCalDAVClient = None
    GOOGLE_AVAILABLE = False


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
        # Match PHP version time range: -2 hours to +2 days
        from datetime import timedelta
        start_time = (datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')
        end_time = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')
        
        events = client.get_all_events(start_time, end_time)
        
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
    except Exception as e:
        print(f"Error getting DingTalk events: {e}")
        return []


def get_todolist_from_icloud() -> List[str]:
    """Get todo list from iCloud calendar"""
    if not ICLOUD_AVAILABLE:
        print("iCloud CalDAV client not available. Please install required dependencies.")
        return []
        
    if not config.ICLOUD_CALDAV_URL or not config.ICLOUD_CALDAV_USER or not config.ICLOUD_CALDAV_PASS:
        return []
        
    try:
        client = ICloudCalDAVClient(config.ICLOUD_CALDAV_USER, config.ICLOUD_CALDAV_PASS, config.ICLOUD_CALDAV_URL)
        events = client.get_all_events(
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            datetime.now().strftime('%Y-%m-%d 00:00:00')
        )
        
        todolist = []
        index_day = datetime.now().day
        
        for event in events:
            if 'SUMMARY' in event and 'DTSTART' in event:
                # Handle different time formats
                if isinstance(event['DTSTART'], int):
                    event_date = datetime.fromtimestamp(event['DTSTART'])
                else:
                    # Try to parse as string date
                    try:
                        event_date = datetime.strptime(event['DTSTART'], '%Y%m%dT%H%M%S')
                    except ValueError:
                        event_date = datetime.now()
                        
                if event_date.day != index_day:
                    todolist.append("")
                    index_day = event_date.day
                    
                todolist.append(f"{event_date.strftime('%H:%M')} {event['SUMMARY']}")
                
        client.close()
        return todolist
    except Exception as e:
        print(f"Error fetching iCloud calendar events: {e}")
        return []


def get_todolist_from_google() -> List[str]:
    """Get todo list from Google calendar"""
    if not GOOGLE_AVAILABLE:
        print("Google CalDAV client not available. Please install required dependencies.")
        return []
        
    if not config.GOOGLE_CALDAV_URL or not config.GOOGLE_CALDAV_USER or not config.GOOGLE_CALDAV_PASS:
        return []
        
    try:
        client = GoogleCalDAVClient(config.GOOGLE_CALDAV_USER, config.GOOGLE_CALDAV_PASS, config.GOOGLE_CALDAV_URL)
        events = client.get_all_events(
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            datetime.now().strftime('%Y-%m-%d 00:00:00')
        )
        
        todolist = []
        index_day = datetime.now().day
        
        for event in events:
            if 'SUMMARY' in event and 'DTSTART' in event:
                # Handle different time formats
                if isinstance(event['DTSTART'], int):
                    event_date = datetime.fromtimestamp(event['DTSTART'])
                else:
                    # Try to parse as string date
                    try:
                        event_date = datetime.strptime(event['DTSTART'], '%Y%m%dT%H%M%S')
                    except ValueError:
                        event_date = datetime.now()
                        
                if event_date.day != index_day:
                    todolist.append("")
                    index_day = event_date.day
                    
                todolist.append(f"{event_date.strftime('%H:%M')} {event['SUMMARY']}")
                
        client.close()
        return todolist
    except Exception as e:
        print(f"Error fetching Google calendar events: {e}")
        return []


def get_todolist_from_calendar() -> List[str]:
    """Get todo list from configured calendar source"""
    calendar_source = config.CALENDAR_SOURCE.lower()
    
    if calendar_source == 'dingtalk':
        return get_todolist_from_dingtalk()
    elif calendar_source == 'icloud':
        return get_todolist_from_icloud()
    elif calendar_source == 'google':
        return get_todolist_from_google()
    else:
        # Default to dingtalk for backward compatibility
        return get_todolist_from_dingtalk()


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
    else:
        todolist = get_todolist_from_calendar()
    

    
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