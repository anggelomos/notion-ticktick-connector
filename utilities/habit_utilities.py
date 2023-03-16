from datetime import datetime
from typing import List


class HabitUtilities:

    @classmethod
    def clean_habit_checkins(cls, checkins: List[dict]) -> List[str]:

        if not checkins:
            return []

        def parse_date(date: str) -> str:
            return datetime.strptime(str(date), '%Y%m%d').strftime('%Y-%m-%d')

        return [parse_date(checkin["checkinStamp"]) for checkin in checkins if checkin["status"] == 2]

    @classmethod
    def parse_habit_date(cls, date: str) -> tuple:
        parsed_date = datetime.strptime(date, "%Y-%m-%d")

        day = parsed_date.strftime("%a").lower()
        week_number = int(parsed_date.strftime("%W"))
        year = int(parsed_date.strftime("%Y"))

        return day, week_number, year
