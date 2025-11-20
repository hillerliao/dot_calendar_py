#!/usr/bin/env python3
"""
Debug script to check why calendar events are not showing in the generated image
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file
load_dotenv()

import config
from dingtalk_caldav_client import DingtalkCalDAVClient
from dot_calendar import DotCalendar

def debug_todolist():
    """Debug the todo list generation process"""
    print("Debugging todo list generation...")
    print("=" * 50)
    
    # Check configuration
    print("Configuration check:")
    print(f"DINGTALK_CALDAV_USER: {'SET' if config.DINGTALK_CALDAV_USER else 'NOT SET'}")
    print(f"DINGTALK_CALDAV_PASS: {'SET' if config.DINGTALK_CALDAV_PASS else 'NOT SET'}")
    print()
    
    if not config.DINGTALK_CALDAV_USER or not config.DINGTALK_CALDAV_PASS:
        print("ERROR: DingTalk credentials not configured!")
        return
    
    try:
        # Test getting events from DingTalk
        print("Testing DingTalk calendar connection...")
        client = DingtalkCalDAVClient(config.DINGTALK_CALDAV_USER, config.DINGTALK_CALDAV_PASS)
        calendars = client.discover_calendars()
        print(f"Found {len(calendars)} calendars")
        
        for i, calendar in enumerate(calendars):
            print(f"  Calendar {i+1}: {calendar['displayname']}")
        
        print()
        
        # Get events
        start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        end_time = datetime.now().replace(day=datetime.now().day + 7).strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"Fetching events from {start_time} to {end_time}")
        events = client.get_all_events(start_time, end_time)
        print(f"Found {len(events)} events")
        
        for i, event in enumerate(events):
            print(f"  Event {i+1}:")
            for key, value in event.items():
                print(f"    {key}: {value}")
            print()
        
        client.close()
        
        # Test todo list generation
        print("Generating todo list...")
        todolist = []
        index_day = datetime.now().day
        
        for event in events:
            if 'SUMMARY' in event and 'DTSTART' in event:
                try:
                    event_date = datetime.fromtimestamp(event['DTSTART'])
                    print(f"Event '{event['SUMMARY']}' on {event_date}")
                    
                    if event_date.day != index_day:
                        todolist.append("")
                        index_day = event_date.day
                        print(f"  Added day separator")
                        
                    todo_item = f"{event_date.strftime('%H:%M')} {event['SUMMARY']}"
                    todolist.append(todo_item)
                    print(f"  Added todo: {todo_item}")
                except Exception as e:
                    print(f"  Error processing event: {e}")
            else:
                print(f"  Skipping event (missing SUMMARY or DTSTART): {event}")
        
        print(f"\nFinal todo list ({len(todolist)} items):")
        for i, item in enumerate(todolist):
            print(f"  {i+1}. '{item}'")
        
        # Test DotCalendar with todo list
        print("\nTesting DotCalendar with todo list...")
        dot_calendar = DotCalendar(
            config.DOT_DEVICE_ID,
            config.DOT_APP_KEY,
            config.CONFIG_USER_LOCATION,
            config.QWEATHER_HOST,
            config.QWEATHER_KEY,
            todolist
        )
        
        print(f"DotCalendar todo list: {dot_calendar.todolist}")
        print(f"Todo list length: {len(dot_calendar.todolist)}")
        
        # Load weather data and create image
        print("\nLoading weather data...")
        dot_calendar.load_weather_data()
        print("Creating image...")
        dot_calendar.create_image()
        print("Saving image...")
        dot_calendar.output(False)  # Save to file, don't sync
        
        print("\nDebug completed. Check output.png for results.")
        
    except Exception as e:
        print(f"Error during debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_todolist()