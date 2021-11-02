from constants.regex_patterns import RegexPatterns
from constants.task_data import TaskData
from datetime import datetime
import json
import re


class TaskUtilities:
    
    ACTIVE_TASKS_FILE_PATH = "resources/active_tasks.json"
    NOTION_IDS_FILE_PATH = "resources/notion_ids.json"

    @staticmethod
    def get_task_date(task: dict) -> str:
        return re.search('(.+)T', task["startDate"]).group(1)
    
    @staticmethod
    def get_task_points(task: dict) -> int:
        task_has_points = re.search(RegexPatterns.GET_TASK_POINTS.value, task["title"])

        if task_has_points:
            return int(task_has_points.group(1))
        return 0

    @staticmethod
    def clean_task_title(task_title: str) -> str:
        return re.sub(RegexPatterns.GET_TASK_POINTS.value, "", task_title)

    @classmethod
    def is_task_due_to_today(cls, task: dict) -> bool:
        current_date = datetime.today().strftime('%Y-%m-%d')
        try:
            task_due_date = cls.get_task_date(task)
            return current_date == task_due_date
        except KeyError:
            return False

    @classmethod
    def clean_tasks(cls, task: dict) -> tuple:
        task_id = task["id"]

        task_data = {
            TaskData.TITLE.value: cls.clean_task_title(task["title"]),
            TaskData.POINTS.value: cls.get_task_points(task),
            TaskData.DONE.value: task["status"] != 0,
            TaskData.DUE_DATE.value: cls.get_task_date(task),
        }

        return (task_id, task_data)

    @classmethod
    def save_active_tasks(cls, tasks: dict):
        with open(cls.ACTIVE_TASKS_FILE_PATH, 'w') as json_file:
            json.dump(tasks, json_file)

    @classmethod
    def get_active_tasks(cls) -> dict:
        active_tasks = {}
        with open(cls.ACTIVE_TASKS_FILE_PATH) as json_file:
            active_tasks = json.load(json_file)

        return active_tasks

    @classmethod
    def save_notion_ids(cls, notion_ids: dict):
        with open(cls.NOTION_IDS_FILE_PATH, 'w') as json_file:
            json.dump(notion_ids, json_file)

    @classmethod
    def get_notion_ids(cls) -> dict:
        notion_ids = {}
        with open(cls.NOTION_IDS_FILE_PATH) as json_file:
            notion_ids = json.load(json_file)

        return notion_ids
