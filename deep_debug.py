#!/usr/bin/env python3
"""
Deep debug script to check why calendar events are not showing in the generated image
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

def deep_debug():
    """Deep debug the calendar generation process"""
    print("Deep debugging calendar generation...")
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
                print(f"    {key}: {value} (type: {type(value)})")
            print()
        
        client.close()
        
        # Test todo list generation with detailed logging
        print("Generating todo list with detailed logging...")
        todolist = []
        last_event_date = None
        
        print(f"Processing {len(events)} events")
        for i, event in enumerate(events):
            print(f"  Processing event {i+1}:")
            print(f"    Event keys: {list(event.keys())}")
            
            if 'SUMMARY' in event and 'DTSTART' in event:
                print(f"    Has SUMMARY and DTSTART")
                
                # Handle different time formats
                if isinstance(event['DTSTART'], int):
                    event_date = datetime.fromtimestamp(event['DTSTART'])
                    print(f"    DTSTART is timestamp: {event['DTSTART']} -> {event_date}")
                else:
                    # Try to parse as string date
                    try:
                        # Handle different formats
                        if 'T' in str(event['DTSTART']) and 'Z' in str(event['DTSTART']):
                            event_date = datetime.strptime(event['DTSTART'], '%Y%m%dT%H%M%SZ')
                        elif 'T' in str(event['DTSTART']):
                            event_date = datetime.strptime(event['DTSTART'], '%Y%m%dT%H%M%S')
                        else:
                            event_date = datetime.strptime(event['DTSTART'], '%Y%m%d')
                        print(f"    DTSTART is string: {event['DTSTART']} -> {event_date}")
                    except ValueError as ve:
                        print(f"    Error parsing DTSTART: {ve}")
                        event_date = datetime.now()
                
                # Add separator if this is a different day
                print(f"    Last event date: {last_event_date}")
                print(f"    Current event date: {event_date}")
                if last_event_date is None or event_date.date() != last_event_date.date():
                    if todolist:  # Only add separator if there are already items
                        todolist.append("")
                        print(f"    Added day separator")
                    last_event_date = event_date
                    print(f"    Updated last_event_date to: {last_event_date}")
                    
                todo_item = f"{event_date.strftime('%H:%M')} {event['SUMMARY']}"
                todolist.append(todo_item)
                print(f"    Added todo: '{todo_item}'")
            else:
                print(f"    Missing SUMMARY or DTSTART, skipping")
        
        print(f"\nFinal todo list ({len(todolist)} items):")
        for i, item in enumerate(todolist):
            print(f"  {i+1}. '{item}' (type: {type(item)})")
        
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
        print(f"DotCalendar todo list length: {len(dot_calendar.todolist)}")
        print(f"DotCalendar todo list types: {[type(item) for item in dot_calendar.todolist]}")
        
        # Let's manually check the draw_todos method
        print("\nManually checking draw_todos logic...")
        if not dot_calendar.todolist:
            print("  todolist is empty")
        else:
            print("  todolist is not empty")
            for i, item in enumerate(dot_calendar.todolist):
                print(f"    Item {i}: '{item}' (empty: {not item})")
        
        # Load weather data and create image
        print("\nLoading weather data...")
        dot_calendar.load_weather_data()
        print("Creating image...")
        dot_calendar.create_image()
        
        # Let's check the image was created
        if dot_calendar.image:
            print("Image created successfully")
            print(f"Image size: {dot_calendar.image.size}")
            print(f"Image mode: {dot_calendar.image.mode}")
        else:
            print("ERROR: Image was not created")
        
        print("Saving image...")
        dot_calendar.output(False)  # Save to file, don't sync
        
        print("\nDeep debug completed. Check output.png for results.")
        
    except Exception as e:
        print(f"Error during deep debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    deep_debug()