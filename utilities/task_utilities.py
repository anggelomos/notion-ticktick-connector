import logging
import re
from typing import List

from data.regular_expressions.filter_tags import FilterTagsRegex
from data.task_data import TaskData
from dateutil import parser, tz
from data.task_notion_parameters import TaskNotionParameters as tnp
from data.task_ticktick_parameters import TaskTicktickParameters as ttp

class TaskUtilities:
    
    ACTIVE_TASKS_FILE_PATH = "resources/active_tasks.json"
    NOTION_IDS_FILE_PATH = "resources/notion_ids.json"

    @staticmethod
    def compare_tasks(notion_task, ticktick_task):
        tasks_equal = True
        comparing_parameters = [param for param in TaskData if param not in [TaskData.NOTION_ID,
                                                                             TaskData.TICKTICK_ID]]

        for task_parameter in comparing_parameters:
            if "habit" in ticktick_task[TaskData.TAGS] and task_parameter == TaskData.STATUS:
                continue

            tasks_equal &= notion_task[task_parameter] == ticktick_task[task_parameter]
        return tasks_equal

    def are_tasks_synced(self, notion_tasks, ticktick_tasks):
        logging.info(f"Figuring out if notion and ticktick tasks are in sync...")

        tasks_synced = False

        def find_notion_task(ticktick_task):
            for notion_task in notion_tasks:
                if notion_task[TaskData.TICKTICK_ID] == ticktick_task[TaskData.TICKTICK_ID]:
                    return notion_task

        if len(ticktick_tasks) <= len(notion_tasks):
            filtered_notion_tasks = list(filter(None, map(find_notion_task, ticktick_tasks)))
            tasks_synced = all(map(self.compare_tasks, filtered_notion_tasks, ticktick_tasks))

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
            task[TaskData.FOCUS_TIME] = float(properties[tnp.FOCUS_TIME][tnp.NUMBER])
            task[TaskData.DUE_DATE] = properties[tnp.DUE_DATE][tnp.DATE][tnp.START]

            try:
                task[TaskData.TAGS] = list(map(lambda tag: tag[tnp.NAME], properties[tnp.TAGS][tnp.MULTI_SELECT]))
            except KeyError:
                task[TaskData.TAGS] = []

            try:
                task[TaskData.STATUS] = properties[tnp.STATUS][tnp.SELECT][tnp.NAME]
            except (KeyError, TypeError):
                task[TaskData.STATUS] = ""

            notion_tasks.append(task)
        return notion_tasks

    @staticmethod
    def get_task_title(task: dict) -> str:
        return task[ttp.TITLE].strip()

    @staticmethod
    def get_task_points(task: dict) -> int:
        points_tag = next(filter(lambda tag: TaskData.POINTS.value in tag, task[ttp.TAGS]), None)

        if points_tag:
            task_points = int(points_tag.replace(TaskData.POINTS.value+"-", ""))
            return task_points

        return 0

    @staticmethod
    def get_task_energy(task: dict) -> int:
        energy_tag = next(filter(lambda tag: TaskData.ENERGY.value in tag, task[ttp.TAGS]), None)

        if energy_tag:
            task_energy = int(energy_tag.replace(TaskData.ENERGY.value + "-", ""))
            return task_energy

        return 0

    @staticmethod
    def get_task_date(task: dict) -> str:
        task_timezone = tz.gettz(task[ttp.TIMEZONE])
        task_raw_date = parser.parse(task[ttp.START_DATE])

        localized_task_date = task_raw_date.astimezone(task_timezone)
        task_date = localized_task_date.strftime("%Y-%m-%d")

        return task_date

    @staticmethod
    def get_task_focus_time(task: dict) -> float:
        try:
            return round(sum(map(lambda summary: summary[ttp.POMO_DURATION] + summary[ttp.STOPWATCH_DURATION], task[ttp.FOCUS_SUMMARIES])) / 3600, 2)
        except KeyError:
            return 0

    @classmethod
    def get_task_tags(cls, raw_task: dict) -> List[str]:
        raw_tags = raw_task[ttp.TAGS]
        task_tags = []

        for raw_tag in raw_tags:
            valid_tag = all(map(lambda regex: not bool(re.match(regex.value, raw_tag)), FilterTagsRegex))

            if valid_tag:
                task_tags.append(raw_tag)

        return task_tags

    @classmethod
    def is_task_valid(cls, task: dict) -> bool:

        if ttp.START_DATE not in task:
            return False
        return True

    @staticmethod
    def parse_tags(tags: List[str]) -> List[dict]:
        return list(map(lambda tag: {tnp.NAME: tag}, tags))
