from datetime import datetime, date, timezone, timedelta
from typing import Optional
import pytz


LOCAL_TIMEZONE = pytz.timezone("Asia/Shanghai")
UTC_TIMEZONE = pytz.UTC


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


def get_local_now() -> datetime:
    return datetime.now(LOCAL_TIMEZONE)


def utc_to_local(dt: datetime) -> datetime:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC_TIMEZONE)
    return dt.astimezone(LOCAL_TIMEZONE)


def local_to_utc(dt: datetime) -> datetime:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = LOCAL_TIMEZONE.localize(dt)
    return dt.astimezone(UTC_TIMEZONE)


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    if dt is None:
        return None
    local_dt = utc_to_local(dt)
    return local_dt.strftime(format_str)


def format_date(d: date, format_str: str = "%Y-%m-%d") -> str:
    if d is None:
        return None
    return d.strftime(format_str)


def parse_date(date_str: str, format_str: str = "%Y-%m-%d") -> Optional[date]:
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, format_str).date()
    except ValueError:
        return None


def parse_datetime(datetime_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
    if not datetime_str:
        return None
    try:
        dt = datetime.strptime(datetime_str, format_str)
        return LOCAL_TIMEZONE.localize(dt)
    except ValueError:
        return None


def get_today_local() -> date:
    return get_local_now().date()


def get_date_range(days: int = 7) -> tuple[date, date]:
    today = get_today_local()
    end_date = today + timedelta(days=days)
    return today, end_date


def is_same_day(dt1: datetime, dt2: datetime) -> bool:
    if dt1 is None or dt2 is None:
        return False
    local_dt1 = utc_to_local(dt1)
    local_dt2 = utc_to_local(dt2)
    return local_dt1.date() == local_dt2.date()


def get_day_of_week(d: date) -> int:
    return d.weekday()


def time_to_minutes(time_str: str) -> int:
    if not time_str:
        return 0
    try:
        hours, minutes = map(int, time_str.split(":"))
        return hours * 60 + minutes
    except (ValueError, AttributeError):
        return 0


def minutes_to_time(minutes: int) -> str:
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"
