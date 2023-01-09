from datetime import datetime
from typing import List

from data.habit_list import HabitList
from data.task_data import TaskData


class HabitUtilities:

    @classmethod
    def get_habit_checkins_date(cls, checkins: List[dict]) -> List[str]:

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
