from datetime import time
import zoneinfo

bot_tz = zoneinfo.ZoneInfo('America/New_York')

def get_time(hours: int):
    return time(hours, 0, 0, 0, bot_tz)
