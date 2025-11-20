#!/usr/bin/env python3
"""
Final debug script to check why calendar events are still not showing in the generated image
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

def final_debug():
    """Final debug of the calendar generation process"""
    print("Final debugging calendar generation...")
    print("=" * 50)
    
    # Test getting events from DingTalk
    print("Testing DingTalk calendar connection...")
    try:
        client = DingtalkCalDAVClient(config.DINGTALK_CALDAV_USER, config.DINGTALK_CALDAV_PASS)
        calendars = client.discover_calendars()
        print(f"Found {len(calendars)} calendars")
        
        for i, calendar in enumerate(calendars):
            print(f"  Calendar {i+1}: {calendar['displayname']}")
        
        # Get events
        start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        end_time = datetime.now().replace(day=datetime.now().day + 7).strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"\nFetching events from {start_time} to {end_time}")
        events = client.get_all_events(start_time, end_time)
        print(f"Found {len(events)} events")
        
        for i, event in enumerate(events):
            print(f"  Event {i+1}:")
            for key, value in event.items():
                print(f"    {key}: {value}")
        
        client.close()
        
        # Test todo list generation
        print("\nGenerating todo list...")
        todolist = []
        last_event_date = None
        
        for event in events:
            if 'SUMMARY' in event and 'DTSTART' in event:
                # Handle different time formats
                if isinstance(event['DTSTART'], int):
                    event_date = datetime.fromtimestamp(event['DTSTART'])
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
                    except ValueError:
                        event_date = datetime.now()
                
                # Add separator if this is a different day
                if last_event_date is None or event_date.date() != last_event_date.date():
                    if todolist:  # Only add separator if there are already items
                        todolist.append("")
                    last_event_date = event_date
                    
                todo_item = f"{event_date.strftime('%H:%M')} {event['SUMMARY']}"
                todolist.append(todo_item)
                print(f"  Added todo: '{todo_item}'")
        
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
        print(f"DotCalendar todo list length: {len(dot_calendar.todolist)}")
        
        # Check if the todolist is actually being passed correctly
        print(f"Checking if todolist is correctly assigned:")
        print(f"  Direct access to todolist: {dot_calendar.todolist}")
        print(f"  Length check: {len(dot_calendar.todolist)}")
        print(f"  Is empty: {not dot_calendar.todolist}")
        
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
        
        # Let's manually test the draw_todos method to see what's happening
        print("\nManually testing draw_todos method...")
        from PIL import Image, ImageDraw, ImageFont
        test_image = Image.new('RGBA', (dot_calendar.BG_WIDTH, dot_calendar.BG_HEIGHT), (255, 255, 255, 255))
        draw = ImageDraw.Draw(test_image)
        
        try:
            font = ImageFont.truetype(dot_calendar.text_font, dot_calendar.TODO_FONT_SIZE)
            print("Font loaded successfully")
        except Exception as e:
            print(f"Error loading font: {e}")
            font = ImageFont.load_default()
        
        # Simulate the draw_todos logic
        print("Simulating draw_todos logic...")
        if not dot_calendar.todolist:
            print("Todolist is empty - would draw '近日无日程'")
            draw.text((30, 10 + dot_calendar.TODO_FONT_SIZE), '近日无日程', fill=(0, 0, 0), font=font)
        else:
            print("Todolist is NOT empty - drawing todo items")
            process_height = 3
            calendar_width = 7 * dot_calendar.GRID_WIDTH
            
            for i, line_text in enumerate(dot_calendar.todolist):
                print(f"  Drawing item {i}: '{line_text}'")
                if i >= dot_calendar.TODO_MAX_LINE:
                    print(f"    Breaking at TODO_MAX_LINE ({dot_calendar.TODO_MAX_LINE})")
                    break
                    
                if line_text == '':
                    print("    Drawing separator line")
                    draw.line([
                        (10, process_height + 3),
                        (dot_calendar.BG_WIDTH - calendar_width - 10, process_height + 3)
                    ], fill=(0, 0, 0), width=1)
                    process_height += 6
                    continue

                try:
                    text_bbox = draw.textbbox((0, 0), line_text, font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_height = text_bbox[3] - text_bbox[1]
                    
                    print(f"    Drawing text '{line_text}' at position (3, {process_height})")
                    draw.text((3, process_height), line_text, fill=(0, 0, 0), font=font)
                except Exception as e:
                    print(f"    Error drawing text: {e}")
                process_height += text_height
                print(f"    Process height updated to: {process_height}")
        
        # Save test image
        print("\nSaving test image...")
        test_image.save('final_debug_output.png')
        print("Test image saved to final_debug_output.png")
        
        # Now save the actual image from dot_calendar
        print("Saving actual image...")
        dot_calendar.output(False)  # Save to file, don't sync
        print("Actual image saved to output.png")
        
        print("\nFinal debug completed.")
        
    except Exception as e:
        print(f"Error during final debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    final_debug()