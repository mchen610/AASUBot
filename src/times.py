from datetime import time, datetime, timedelta
from dateutil import tz

est = tz.gettz('America/New_York')
dst = datetime.now(est)

midnight = time(0, 0, 0, 0, est)
eight_am = time(8, 0, 0, 0, est)
nine_pm = time(21, 0, 0, 0, est)

def get_utc_offset(__dt: datetime) -> int:
    """Get the UTC offset of the current time in hours."""
    
    now = datetime.now(est)
    return est.utcoffset(now).total_seconds() // 3600
