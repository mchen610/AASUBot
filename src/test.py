from config import *
from datetime import *
from dateutil.parser import parse as date_parse

today = datetime.utcnow() - timedelta(hours=9) - timedelta(minutes=54)
time_min = today.isoformat() + 'Z'
time_max = (today + timedelta(days=90)).isoformat() + 'Z'

raw_events = google_service.events().list(calendarId='aasu.uf@gmail.com', timeMin=time_min, timeMax=time_max, singleEvents=True, orderBy='startTime').execute().get('items', [])

for event in raw_events:
    print(event['start'])
    break
