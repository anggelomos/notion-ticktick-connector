import re
from typing import List

from data.regular_expressions.filter_tags import FilterTagsRegex
from data.task_data import TaskData
from dateutil import parser, tz
from data.task_notion_parameters import TaskNotionParameters as tnp
from data.task_ticktick_parameters import TaskTicktickParameters as ttp


class TaskUtilities:

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

            try:
                task[TaskData.DUE_DATE] = properties[tnp.DUE_DATE][tnp.DATE][tnp.START]
            except (KeyError, TypeError):
                task[TaskData.DUE_DATE] = ""

            try:
                task[TaskData.TAGS] = list(map(lambda tag: tag[tnp.NAME], properties[tnp.TAGS][tnp.MULTI_SELECT]))
            except KeyError:
                task[TaskData.TAGS] = []

            try:
                task[TaskData.STATUS] = properties[tnp.STATUS][tnp.SELECT][tnp.NAME]
            except (KeyError, TypeError):
                task[TaskData.STATUS] = ""

            try:
                task[TaskData.RECURRENT_ID] = properties[tnp.RECURRENT_ID][tnp.RICH_TEXT][0][tnp.PLAIN_TEXT]
            except (IndexError, KeyError):
                task[TaskData.RECURRENT_ID] = ""

            notion_tasks.append(task)
        return notion_tasks

    @staticmethod
    def get_task_title(task: dict) -> str:
        return task[ttp.TITLE].strip()

    @staticmethod
    def get_task_estimation(task: dict, field: TaskData) -> int:
        estimation_tag = next(filter(lambda tag: field.value in tag, task[ttp.TAGS]), None)

        if estimation_tag:
            task_estimation = int(estimation_tag.replace(field.value, ""))
            return task_estimation

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
        focus_time = 0

        if ttp.FOCUS_SUMMARIES in task:
            raw_focus_time = map(lambda summary: summary[ttp.POMO_DURATION] + summary[ttp.STOPWATCH_DURATION],
                                 task[ttp.FOCUS_SUMMARIES])
            focus_time = round(sum(raw_focus_time) / 3600, 2)

        return focus_time

    @classmethod
    def get_task_tags(cls, raw_task: dict) -> List[str]:
        raw_tags = raw_task[ttp.TAGS]
        task_tags = []

        for raw_tag in raw_tags:
            valid_tag = all(map(lambda regex, value=raw_tag: not bool(re.match(regex.value, value)), FilterTagsRegex))

            if valid_tag:
                task_tags.append(raw_tag)

        return task_tags

    @classmethod
    def is_task_valid(cls, task: dict) -> bool:
        return not task[TaskData.TITLE].startswith("$")

    @staticmethod
    def parse_tags(tags: List[str]) -> List[dict]:
        return list(map(lambda tag: {tnp.NAME: tag}, tags))
