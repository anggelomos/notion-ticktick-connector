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
        raw_habit = habit.copy()
        raw_habit[TaskData.TAGS].remove(HabitList.HABIT.value)

        return raw_habit[TaskData.TAGS][0], raw_habit[TaskData.DUE_DATE]
