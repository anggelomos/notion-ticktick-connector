import logging
from typing import List

from data.regex_patterns import RegexPatterns
from data.task_data import TaskData
import re

from data.task_notion_parameters import TaskNotionParameters as tnp
from data.task_ticktick_parameters import TaskTicktickParameters as ttp


class TaskUtilities:
    
    ACTIVE_TASKS_FILE_PATH = "resources/active_tasks.json"
    NOTION_IDS_FILE_PATH = "resources/notion_ids.json"

    @staticmethod
    def are_tasks_synced(notion_tasks, ticktick_tasks):
        tasks_synced = False
        if len(notion_tasks) == len(ticktick_tasks):
            def compare_tasks(notion_task, ticktick_task):
                tasks_equal = True
                for task_parameter in [parameter for parameter in TaskData if parameter not in [TaskData.NOTION_ID]]:
                    tasks_equal &= notion_task[task_parameter] == ticktick_task[task_parameter]
                return tasks_equal

            tasks_synced = all(map(compare_tasks, notion_tasks, ticktick_tasks))
        logging.info(f"Are tasks synced: {tasks_synced}")
        return tasks_synced

    @staticmethod
    def parse_notion_tasks(raw_tasks: List[dict]) -> List[dict]:
        notion_tasks = []
        for raw_task in raw_tasks:
            properties = raw_task[tnp.PROPERTIES]
            task = {}
            task[TaskData.TICKTICK_ID] = properties[tnp.TICKTICK_ID][tnp.RICH_TEXT][0][tnp.PLAIN_TEXT]
            task[TaskData.NOTION_ID] = raw_task[tnp.ID]
            task[TaskData.DONE] = properties[tnp.DONE][tnp.CHECKBOX]
            task[TaskData.TITLE] = properties[tnp.TASK][tnp.TITLE][0][tnp.PLAIN_TEXT]
            task[TaskData.POINTS] = properties[tnp.POINTS][tnp.NUMBER]
            task[TaskData.ENERGY] = properties[tnp.ENERGY][tnp.NUMBER]
            task[TaskData.DUE_DATE] = properties[tnp.DUE_DATE][tnp.DATE][tnp.START]
            try:
                task[TaskData.TAGS] = list(map(lambda tag: tag[tnp.NAME], properties[tnp.TAGS][tnp.MULTI_SELECT]))
            except KeyError:
                task[TaskData.TAGS] = []

            notion_tasks.append(task)
        return notion_tasks

    @classmethod
    def parse_ticktick_tasks(cls, raw_tasks: List[dict]) -> List[dict]:
        ticktick_tasks = []
        for raw_task in raw_tasks:
            task = {}
            task[TaskData.TICKTICK_ID] = raw_task[ttp.ID]
            task[TaskData.NOTION_ID] = None
            task[TaskData.DONE] = False
            task[TaskData.TITLE] = cls.get_task_title(raw_task)
            task[TaskData.POINTS] = cls.get_task_points(raw_task)
            task[TaskData.ENERGY] = cls.get_task_energy(raw_task)
            task[TaskData.DUE_DATE] = cls.get_task_date(raw_task)
            try:
                task[TaskData.TAGS] = raw_task[ttp.TAGS]
            except KeyError:
                task[TaskData.TAGS] = []

            ticktick_tasks.append(task)
        return ticktick_tasks

    @staticmethod
    def get_task_title(task: dict) -> str:
        return re.search(RegexPatterns.GET_TASK_TITLE, task[ttp.TITLE]).group(1)

    @staticmethod
    def get_task_points(task: dict) -> int:
        task_has_points = re.search(RegexPatterns.GET_TASK_POINTS, task[ttp.TITLE])

        if task_has_points:
            return int(task_has_points.group(1))
        return 0

    @staticmethod
    def get_task_energy(task: dict) -> int:
        task_has_energy = re.search(RegexPatterns.GET_TASK_ENERGY, task[ttp.TITLE])

        if task_has_energy:
            return int(task_has_energy.group(1))
        return 0

    @staticmethod
    def get_task_date(task: dict) -> str:
        try:
            return re.search(RegexPatterns.GET_TASK_DATE, task[ttp.START_DATE]).group(1)
        except KeyError:
            return ""

    @classmethod
    def is_task_valid(cls, task: dict) -> bool:

        if not cls.get_task_date(task):
            return False

        if not cls.get_task_points(task):
            return False

        if not cls.get_task_energy(task):
            return False

        return True

    @staticmethod
    def parse_tags(tags: List[str]) -> List[dict]:
        return list(map(lambda tag: {tnp.NAME: tag}, tags))
