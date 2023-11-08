from datetime import time, datetime
from dateutil import tz

est = tz.gettz('America/New_York')

def get_utc_offset(_tz=est) -> int:
    """Get the number of hours that UTC is ahead of the given timezone."""
    
    now = datetime.now(_tz)
    offset = _tz.utcoffset(now).total_seconds() // 3600
    return -int(offset)

def get_offset_naive_time(hours: int, _tz=est):
    """Get an offset-naive time object for the given hour in the given timezone."""
    
    offset = get_utc_offset(_tz)
    return time(hours % 24 + offset, 0, 0, 0)
