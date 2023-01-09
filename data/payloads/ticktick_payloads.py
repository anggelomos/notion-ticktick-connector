import json
from typing import List

from data.habit_notion_parameters import HabitNotionParameters as hnp
from data.task_notion_parameters import TaskNotionParameters as tnp
from utilities.task_utilities import TaskUtilities


class TicktickPayloads:

    @staticmethod
    def get_habits_checkins(habit_list: dict, after_stamp: int) -> dict:
        return {
                "habitIds": list(habit_list.keys()),
                "afterStamp": after_stamp
                }
