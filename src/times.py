from datetime import time, datetime, timedelta
from dateutil import tz

est = tz.gettz('America/New_York')

midnight = time(0, 0, 0, 0, est)
eight_am = time(8, 0, 0, 0, est)
nine_pm = time(21, 0, 0, 0, est)

def get_utc_offset(__tz = est) -> int:
    """Get the number of hours that UTC is ahead of the given timezone."""
    
    now = datetime.now(__tz)
    offset = __tz.utcoffset(now).total_seconds() // 3600
    return -int(offset)
