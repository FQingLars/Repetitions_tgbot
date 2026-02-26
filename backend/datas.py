from datetime import datetime


def to_datetime(date_time: str) -> datetime:
    return datetime.strptime(date_time, "%d.%m.%Y %H:%M")

def normalize_date(raw: str) -> str:
    date_time = datetime.strptime(raw, "%Y-%m-%d %H:%M:%S")
    return date_time.strftime("%d.%m.%Y %H:%M")