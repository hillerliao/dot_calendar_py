from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
import json
import io

import config
import main as main_mod
from dot_calendar import DotCalendar

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
