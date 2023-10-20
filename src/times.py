from datetime import time, timedelta, timezone

est = timezone(timedelta(hours=-4))
midnight = time(0, 0, 0, 0, est)
before_midnight = time(23, 59, 30, 0, est)
nine_pm = time(21, 0, 0, 0, est)
before_nine_pm = time(20, 59, 30, 0, est)
eight_am = time(8, 0, 0, 0, est)
before_eight_am = time(7, 59, 30, 0, est)

