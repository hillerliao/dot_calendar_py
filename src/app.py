from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
import json
import io

import config
import main as main_mod
from dot_calendar import DotCalendar
from weather_chart import WeatherChart

app = FastAPI(title="Dot Calendar API")


@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/generate")
async def generate(payload: dict):
    token = payload.get('token')
    if not token or token != config.DOT_CALENDAR_TOKEN:
        raise HTTPException(status_code=403, detail='Forbidden')

    calendar = payload.get('calendar')
    dotsync = bool(payload.get('dotsync', False))

    # Build todolist
    if calendar:
        if not isinstance(calendar, str):
            calendar_param = json.dumps(calendar, ensure_ascii=False)
        else:
            calendar_param = calendar
        todolist = main_mod.get_todolist_from_calendar_param(calendar_param)
    else:
        todolist = main_mod.get_todolist_from_calendar()

    dot_calendar = DotCalendar(
        config.DOT_DEVICE_ID,
        config.DOT_APP_KEY,
        config.CONFIG_USER_LOCATION,
        config.QWEATHER_HOST,
        config.QWEATHER_KEY,
        todolist
    )

    # Generate image
    dot_calendar.load_weather_data()
    dot_calendar.create_image()

    # Convert to black and white and return PNG bytes
    bw = dot_calendar.blackwhite_image(dot_calendar.image)
    buf = io.BytesIO()
    bw.save(buf, format='PNG')
    buf.seek(0)

    # Optionally sync to Dot device (will attempt network calls)
    if dotsync:
        try:
            dot_calendar.output(True)
        except Exception:
            # don't fail the request if device sync fails
            pass

    return Response(content=buf.getvalue(), media_type='image/png')


@app.post("/weather-chart")
async def weather_chart(payload: dict):
    """生成天气预报走势图"""
    token = payload.get('token')
    if not token or token != config.DOT_CALENDAR_TOKEN:
        raise HTTPException(status_code=403, detail='Forbidden')

    days = payload.get('days', 15)  # 默认15天
    include_yesterday = payload.get('include_yesterday', True)  # 默认包含昨天数据
    
    try:
        chart = WeatherChart(
            location=config.CONFIG_USER_LOCATION,
            qweather_host=config.QWEATHER_HOST,
            qweather_key=config.QWEATHER_KEY
        )
        
        # 加载天气数据
        chart.load_weather_data(days=days, include_yesterday=include_yesterday)
        
        # 创建图像
        chart.create_image()
        
        # 转换为黑白图像 (适配墨水屏)
        bw_image = chart.blackwhite_image()
        
        # 获取图像字节流
        buf = io.BytesIO()
        bw_image.save(buf, format='PNG')
        buf.seek(0)
        
        return Response(content=buf.getvalue(), media_type='image/png')
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'生成天气预报走势图失败: {str(e)}')
