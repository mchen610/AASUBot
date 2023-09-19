
 

def main():

    service = build('calendar', 'v3', developerKey=API_KEY)

    today = datetime.today()
    today.replace(hour=0, minute=0, second=0, microsecond=0)
    inOneMonth = today + timedelta(days=30)

    timeMin = today.isoformat() + 'Z'
    timeMax = inOneMonth.isoformat() + 'Z'
    
    events_result = service.events().list(calendarId='aasu