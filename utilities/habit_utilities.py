import datetime
from typing import List

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

        def get_clean_habit_tag(habit_tags: List[str]) -> str:
            unnecessary_habit_tags = [HabitList.HABIT.value, TaskData.POINTS.value, TaskData.ENERGY.value]

            for tag in habit_tags:
                valid_tag = all(map(lambda un_tag: not (un_tag in tag), unnecessary_habit_tags))

                if valid_tag:
                    return tag

        cleaned_habit_tag = get_clean_habit_tag(habit[TaskData.TAGS])
        return cleaned_habit_tag, habit[TaskData.DUE_DATE]
