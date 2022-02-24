import datetime

from data.habit_list import HabitList
from data.task_data import TaskData


class HabitUtilities:

    @classmethod
    def parse_habit_date(cls, date: str) -> tuple:
        parsed_date = datetime.datetime.strptime(date, "%Y-%m-%d")

        day = parsed_date.strftime("%a").lower()
        week_number = int(parsed_date.strftime("%W"))
        year = int(parsed_date.strftime("%Y"))

        return day, week_number, year

    @classmethod
    def parse_habit_task(cls, habit: dict) -> tuple:
        clean_habit_tags = list(filter(lambda tag: tag != HabitList.HABIT.value, habit[TaskData.TAGS]))

        return clean_habit_tags[0], habit[TaskData.DUE_DATE]
