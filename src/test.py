from discord.ext import tasks
from datetime import *
from times import *

test_t = datetime.utcnow().time()
new_s = (test_t.second + 6) % 60
new_m = test_t.minute + (test_t.second + 6) // 60
test_t = test_t.replace(second=new_s, minute=new_m, microsecond=0)
@tasks.loop(time=test_t)
async def test():
    global test_t
    print(datetime.utcnow(), test_t)
    new_s = (test_t.second + 2) % 60
    new_m = test_t.minute + (test_t.second + 2) // 60
    test_t = test_t.replace(second=new_s, minute=new_m, microsecond=0)
    test.change_interval(time=test_t)


start = datetime(2024, 3, 10, 2, 0, 0, 0, bot_tz)
new = start + timedelta(seconds=1)
old = start - timedelta(seconds=1)

print(old.dst(), new.dst(), start.dst())