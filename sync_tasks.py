import os
import re
import json
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

service_account_info = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])

SCOPES = ['https://www.googleapis.com/auth/calendar']
credentials = service_account.Credentials.from_service_account_info(
    service_account_info, scopes=SCOPES)

service = build('calendar', 'v3', credentials=credentials)

CALENDAR_ID = 'primary'

SCHEDULED_REGEX = r"⏳ (\d{4}-\d{2}-\d{2})"
DUE_REGEX = r"📅 (\d{4}-\d{2}-\d{2})"

def parse_tasks(file_path):
    tasks = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if "- [ ]" not in line:
                continue

            title = line.strip()

            scheduled = re.search(SCHEDULED_REGEX, line)
            due = re.search(DUE_REGEX, line)

            if scheduled:
                date = scheduled.group(1)
                start_dt = datetime.strptime(date + " 09:00", "%Y-%m-%d %H:%M")

                tasks.append({
                    "summary": title,
                    "start": start_dt.isoformat(),
                    "end": start_dt.isoformat(),
                    "date": date
                })

            elif due:
                date = due.group(1)

                tasks.append({
                    "summary": "[마감] " + title,
                    "date": date
                })

    return tasks

def event_exists(summary, date):
    events = service.events().list(
        calendarId=CALENDAR_ID,
        q=summary,
        timeMin=f"{date}T00:00:00Z",
        timeMax=f"{date}T23:59:59Z"
    ).execute()

    return len(events.get('items', [])) > 0

def create_event(task):
    if "start" in task:
        event = {
            'summary': task["summary"],
            'start': {'dateTime': task["start"], 'timeZone': 'Asia/Seoul'},
            'end': {'dateTime': task["end"], 'timeZone': 'Asia/Seoul'},
        }
    else:
        event = {
            'summary': task["summary"],
            'start': {'date': task["date"]},
            'end': {'date': task["date"]},
        }

    service.events().insert(calendarId=CALENDAR_ID, body=event).execute()

def main():
    for root, _, files in os.walk("./"):
        for file in files:
            if file.endswith(".md"):
                path = os.path.join(root, file)
                tasks = parse_tasks(path)

                for task in tasks:
                    if not event_exists(task["summary"], task["date"]):
                        create_event(task)

if __name__ == "__main__":
    main()
