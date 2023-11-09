from datetime import time, datetime, timezone, timedelta
from dateutil import tz

bot_tz = tz.gettz('America/New_York')

def get_utc_offset(_tz=bot_tz) -> int:
    """Get the number of hours that UTC is ahead of the given timezone."""
    
    now = datetime.now(_tz)
    offset = _tz.utcoffset(now).total_seconds() // 3600
    return -int(offset)

def get_offset_naive_time(hours: int, _tz=bot_tz):
    """Get an offset-naive time object for the given hour in the given timezone."""
    
    offset = get_utc_offset(_tz)
    naive_tz = timezone(timedelta(hours=-offset))
    return time(hours % 24, 0, 0, 0, naive_tz)
