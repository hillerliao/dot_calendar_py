import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Configuration constants
DOT_CALENDAR_TOKEN = os.getenv('DOT_CALENDAR_TOKEN')
QWEATHER_KEY = os.getenv('QWEATHER_KEY')
QWEATHER_HOST = os.getenv('QWEATHER_HOST', 'devapi.qweather.com')
CONFIG_USER_LOCATION = os.getenv('CONFIG_USER_LOCATION')
DOT_DEVICE_ID = os.getenv('DOT_DEVICE_ID')
DOT_APP_KEY = os.getenv('DOT_APP_KEY')
DINGTALK_CALDAV_USER = os.getenv('DINGTALK_CALDAV_USER')
DINGTALK_CALDAV_PASS = os.getenv('DINGTALK_CALDAV_PASS')

# Calendar source configuration
CALENDAR_SOURCE = os.getenv('CALENDAR_SOURCE', 'dingtalk')  # Options: 'dingtalk', 'icloud', 'google'

# iCloud Calendar configuration
ICLOUD_CALDAV_URL = os.getenv('ICLOUD_CALDAV_URL')
ICLOUD_CALDAV_USER = os.getenv('ICLOUD_CALDAV_USER')
ICLOUD_CALDAV_PASS = os.getenv('ICLOUD_CALDAV_PASS')

# Google Calendar configuration
GOOGLE_CALDAV_URL = os.getenv('GOOGLE_CALDAV_URL')
GOOGLE_CALDAV_USER = os.getenv('GOOGLE_CALDAV_USER')
GOOGLE_CALDAV_PASS = os.getenv('GOOGLE_CALDAV_PASS')

# Cache path
CACHE_PATH = os.path.join(os.path.dirname(__file__), '..', 'cache')