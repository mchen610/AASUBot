from datetime import *
from times import est

x = datetime.now(est)
x = x.replace(hour=2, second=0, microsecond=0, minute=0)
for i in range(10):
    x = x - timedelta(days=1)
    print(x, x.dst())