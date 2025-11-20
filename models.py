from dataclasses import dataclass
from typing import List, Optional

@dataclass
class WeatherInfo:
    """Weather information for a day"""
    date: str
    week: int
    day: int
    line: int
    font_icon: str
    dx: int
    dy: int

@dataclass
class Event:
    """Calendar event"""
    summary: str
    start_time: int
    location: Optional[str] = None

@dataclass
class WeatherDaily:
    """Daily weather forecast"""
    fx_date: str
    icon_day: str
    icon_night: str
    text_day: str
    text_night: str
    temp_max: str
    temp_min: str