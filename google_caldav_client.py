import requests
from typing import List, Dict, Any, Optional
import xml.etree.ElementTree as ET
from datetime import datetime
import re

class GoogleCalDAVClient:
    """Simplified CalDAV client for Google calendar"""
    
    def __init__(self, username: str, password: str, caldav_url: str):
        self.base_url = caldav_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.auth = (username, password)
        self.session.headers.update({
            'User-Agent': 'Python Enhanced CalDAV Client/1.0'
        })
        self.calendar_paths = []
        self.discover_calendars()
    
    def discover_calendars(self) -> List[Dict[str, str]]:
        """Discover available calendars"""
        if self.calendar_paths:
            return self.calendar_paths
            
        url = self.base_url
        
        propfind_xml = '''<?xml version="1.0" encoding="utf-8" ?>
<d:propfind xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav" xmlns:cs="http://calendarserver.org/ns/">
  <d:prop>
    <d:resourcetype />
    <d:displayname />
    <c:supported-calendar-component-set />
    <cs:getctag />
  </d:prop>
</d:propfind>'''
        
        try:
            response = self.session.request(
                'PROPFIND',
                url,
                data=propfind_xml.encode('utf-8'),
                headers={
                    'Content-Type': 'application/xml; charset=utf-8',
                    'Depth': '1'
                },
                timeout=30
            )
            
            if response.status_code != 207:
                raise Exception(f"Failed to get calendar list, HTTP status code: {response.status_code}")
            
            self.calendar_paths = self._parse_calendars(response.text)
            return self.calendar_paths
            
        except requests.RequestException as e:
            raise Exception(f"Network error while discovering calendars: {str(e)}")
    
    def _parse_calendars(self, response_text: str) -> List[Dict[str, str]]:
        """Parse calendar discovery response"""
        try:
            root = ET.fromstring(response_text)
            namespaces = {
                'd': 'DAV:',
                'cs': 'http://calendarserver.org/ns/',
                'c': 'urn:ietf:params:xml:ns:caldav'
            }
            
            calendars = []
            for response in root.findall('.//d:response', namespaces):
                href_elem = response.find('./d:href', namespaces)
                if href_elem is None:
                    continue
                    
                href = href_elem.text
                
                # Check if this is a calendar resource
                resourcetype_elem = response.find('./d:propstat/d:prop/d:resourcetype', namespaces)
                if resourcetype_elem is None:
                    continue
                    
                is_calendar = resourcetype_elem.find('./c:calendar', namespaces) is not None
                if not is_calendar:
                    continue
                
                displayname_elem = response.find('./d:propstat/d:prop/d:displayname', namespaces)
                ctag_elem = response.find('.//cs:getctag', namespaces)
                
                displayname = 'Unnamed Calendar'
                if displayname_elem is not None and displayname_elem.text:
                    displayname = displayname_elem.text
                
                calendars.append({
                    'href': href,
                    'displayname': displayname,
                    'ctag': ctag_elem.text if ctag_elem is not None else None
                })
            
            return calendars
            
        except ET.ParseError as e:
            raise Exception(f"Failed to parse calendar discovery response: {str(e)}")
    
    def get_events(self, calendar_path: str, start: Optional[str] = None, end: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get events from a specific calendar"""
        url = self.base_url + calendar_path if not calendar_path.startswith('http') else calendar_path
        
        # Set time range filter
        time_filter = ''
        if start and end:
            # Convert to ISO format for CalDAV
            start_iso = datetime.strptime(start, '%Y-%m-%d %H:%M:%S').strftime('%Y%m%dT%H%M%SZ')
            end_iso = datetime.strptime(end, '%Y-%m-%d %H:%M:%S').strftime('%Y%m%dT%H%M%SZ')
            time_filter = f'<C:time-range start="{start_iso}" end="{end_iso}"/>'
        
        calendar_query_xml = f'''<?xml version="1.0" encoding="utf-8"?>
<C:calendar-query xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav">
  <D:prop>
    <D:getetag/>
    <C:calendar-data/>
  </D:prop>
  <C:filter>
    <C:comp-filter name="VCALENDAR">
      <C:comp-filter name="VEVENT">
        {time_filter}
      </C:comp-filter>
    </C:comp-filter>
  </C:filter>
</C:calendar-query>'''
        
        try:
            response = self.session.request(
                'REPORT',
                url,
                data=calendar_query_xml.encode('utf-8'),
                headers={
                    'Content-Type': 'application/xml; charset=utf-8',
                    'Depth': '1'
                },
                timeout=30
            )
            
            if response.status_code != 207:
                return [{"SUMMARY": f"REPORT request failed, HTTP status code: {response.status_code}"}]
            
            return self._parse_events(response.text)
            
        except requests.RequestException as e:
            raise Exception(f"Network error while getting events: {str(e)}")
    
    def _parse_events(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse events from calendar response"""
        try:
            root = ET.fromstring(response_text)
            namespaces = {'d': 'DAV:', 'c': 'urn:ietf:params:xml:ns:caldav'}
            
            events = []
            for response in root.findall('.//d:response', namespaces):
                calendar_data_elem = response.find('.//c:calendar-data', namespaces)
                if calendar_data_elem is not None and calendar_data_elem.text:
                    ical_data = calendar_data_elem.text
                    events.extend(self._parse_ical(ical_data))
            
            return events
            
        except ET.ParseError as e:
            raise Exception(f"Failed to parse events response: {str(e)}")
    
    def _parse_ical(self, ical_data: str) -> List[Dict[str, Any]]:
        """Parse iCalendar data"""
        events = []
        lines = ical_data.split('\n')
        event = {}
        in_event = False
        key = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('BEGIN:VEVENT'):
                in_event = True
                event = {}
            elif line.startswith('END:VEVENT'):
                in_event = False
                if event:
                    events.append(event)
            elif in_event:
                # Handle continuation lines and key-value pairs
                if ':' in line and not line.startswith(' '):
                    key, value = line.split(':', 1)
                    # Handle parameters in key
                    if ';' in key:
                        main_key = key.split(';')[0]
                        # Extract timezone if present
                        if 'TZID=' in key:
                            tzid_match = re.search(r'TZID=([^;]+)', key)
                            if tzid_match:
                                tzid = tzid_match.group(1)
                                try:
                                    # Try to parse as timestamp with timezone
                                    dt = datetime.strptime(value, "%Y%m%dT%H%M%S")
                                    value = int(dt.timestamp())
                                except ValueError:
                                    pass
                        key = main_key
                    event[key] = value
                elif line.startswith(' ') and key:
                    # Continuation line
                    event[key] += line[1:]
        
        return events
    
    def get_all_events(self, start: Optional[str] = None, end: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all events from all calendars"""
        # Process time format
        start_time = datetime.now()
        end_time = datetime.now()
        
        if start:
            start_time = datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
        if end:
            end_time = datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
        else:
            end_time = start_time.replace(day=start_time.day + 7)  # Default 7 days
        
        events = []
        for calendar in self.calendar_paths:
            calendar_events = self.get_events(calendar['href'], start_time.strftime('%Y-%m-%d %H:%M:%S'), end_time.strftime('%Y-%m-%d %H:%M:%S'))
            events.extend(calendar_events)
        
        # Sort events by start time
        events.sort(key=lambda x: x.get('DTSTART', 0))
        return events
    
    def close(self) -> None:
        """Close the session"""
        self.session.close()