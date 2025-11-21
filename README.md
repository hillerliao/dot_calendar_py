# Python Version of Dot Calendar

This is a Python implementation of the [Dot Calendar](https://github.com/wanyaxing/dot_calendar) application, which generates weather calendar images for the Dot/Quote device.

## Features

- Generates a 30-day weather calendar using QWeather API
- Displays upcoming events/todo items
- Supports syncing with DingTalk calendar via CalDAV
- Outputs images that can be sent to Dot/Quote devices

## Requirements

- Python 3.7+
- Dependencies listed in [requirements.txt](requirements.txt)

## Installation

1. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

2. Copy the `.env.example` file to `.env` and configure your settings:
   ```
   cp .env.example ../.env
   # Edit ../.env with your configuration
   ```

**Environment Variables & Docker**

- **Prefer environment variables**: `config.py` reads configuration from environment variables (and will also load a local `.env` file if present). When running in Docker, pass secrets via environment variables rather than committing them to the image.
- **Example: run with Docker and environment variables**

   ```bash
   docker build -t dot-calendar .
   docker run -p 8000:8000 \
      -e DOT_CALENDAR_TOKEN=your_token_here \
      -e QWEATHER_KEY=your_qweather_key \
      -e CONFIG_USER_LOCATION=116.41,39.90 \
      --rm dot-calendar
   ```

- **Example: `docker run` with one-off generate call** (call the HTTP API from host):

   ```bash
   curl -X POST -H "Content-Type: application/json" \
      -d '{"token":"your_token_here"}' \
      http://localhost:8000/generate --output output.png
   ```

- **Example: enable `dotsync` to push image to Dot device** (requires `DOT_DEVICE_ID` and `DOT_APP_KEY` set in env):

   ```bash
   curl -X POST -H "Content-Type: application/json" \
      -d '{"token":"your_token_here","dotsync":true}' \
      http://localhost:8000/generate --output output.png
   ```

- **Docker Compose**: you can also set environment variables in `docker-compose.yml`, or mount a `.env` file.
## Usage

Run the main script with appropriate parameters:

```bash
python main.py --token YOUR_TOKEN --dotsync 1
```

### Parameters

- `--token`: Security token (required)
- `--calendar`: Calendar data in JSON format (optional)
- `--dotsync`: Sync to Dot device (1 = sync, 0 = no sync)
- `--device_idx`: Device index for configuration switching (optional)

## Project Structure

- `main.py`: Entry point
- `config.py`: Configuration loading
- `dot_calendar.py`: Main calendar generation logic
- `dingtalk_caldav_client.py`: DingTalk CalDAV client
- `utils.py`: Utility functions including file cache
- `models.py`: Data models

## API Integration

### QWeather API

This project uses the QWeather API to get weather forecasts. You'll need to:

1. Register at [QWeather Console](https://console.qweather.com/)
2. Get your API key and host
3. Configure them in the `.env` file

### DingTalk Calendar

To integrate with DingTalk calendar:

1. Get your CalDAV credentials using the [DingtalkCalDAVClient](https://github.com/wanyaxing/DingtalkCalDAVClient) guide
2. Configure the credentials in the `.env` file

### Dot/Quote Device

To send images to your Dot/Quote device:

1. Get your device ID and app key from the [Dot Image API](https://dot.mindreset.tech/docs/server/template/api/image_api)
2. Configure them in the `.env` file

## Differences from PHP Version

This Python version aims to replicate the functionality of the PHP version with these differences:

1. Uses Python instead of PHP
2. Uses requests library instead of curl
3. Uses Pillow instead of GD library for image manipulation
4. Maintains the same caching mechanism with file-based storage
5. Same configuration approach using .env files

## License

This project maintains the same license as the original Dot Calendar project.