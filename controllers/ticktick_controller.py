import logging
import json
from datetime import datetime
from typing import List, Union

from controllers.notion_controller import NotionController
from data.habit_list import HabitList
from data.payloads.ticktick_payloads import TicktickPayloads
from data.task_ticktick_parameters import TaskTicktickParameters as ttp, TaskTicktickParameters
from controllers.ticktick_api import TicktickAPI
from data.task_data import TaskData as td, TaskData
from utilities.habit_utilities import HabitUtilities
from utilities.task_utilities import TaskUtilities


class TicktickController:
    
    active_tasks = {}
    notion_ids = {}
    BASE_URL = "/api/v2"
    get_state = BASE_URL + "/batch/check/0"
    habit_checkins_url = BASE_URL + "/habitCheckins/query"
    completed_tasks_url = BASE_URL + "/project/all/closed?from=&to=&status=Completed"
    abandoned_tasks_url = BASE_URL + "/project/all/closed?from=&to=&status=Abandoned"
    deleted_tasks_url = BASE_URL + "/project/all/trash/pagination?start=0&limit=50"

    def __init__(self, client_id: str, client_secret: str, uri: str, username: str, password: str):
        self.state = {}
        self.inbox_id = None
        self.project_folders = []
        self.projects = []
        self.tasks = []
        self.tags = []
        self.ticktick_client = TicktickAPI(username, password)
        self.relevant_tasks = []
        self.completed_tasks = []
        self.deleted_tasks = []
        self.abandoned_tasks = []

    def sync_tasks(self):
        logging.info("Syncing ticktick tasks")
        response = self.ticktick_client.get(self.get_state, token_required=True)
        self.completed_tasks = self.ticktick_client.get(self.completed_tasks_url, token_required=True)
        self.deleted_tasks = self.ticktick_client.get(self.deleted_tasks_url, token_required=True)["tasks"]
        self.abandoned_tasks = self.ticktick_client.get(self.abandoned_tasks_url, token_required=True)

        self.inbox_id = response['inboxId']
        self.project_folders = response['projectGroups']
        self.projects = response['projectProfiles']
        self.tasks = response['syncTaskBean']['update'] + self.completed_tasks
        self.tags = response['tags']
        self.get_relevant_tasks()

    def get_habits(self):
        logging.info("Getting habits")

        habit_list = {
            "63b3436f824afc1fd1e6e96c": "work-on-resolutions",
            "63b33809824afc1fd1e6ca7b": "read",
            "63b33c35824afc1fd1e6d3ea": "sleep-more-than-7-hours",
            "63b31076824afc436b713c39": "go-to-bed-early",
            "63b33cba824afc1fd1e6d740": "plan-day",
            "63b33ce9824afc1fd1e6d990": "plan-week",
            "63b33d1b824afc1fd1e6dce3": "plan-month",
            "63b33fc0824afc1fd1e6e65e": "meditate",
            "63b33db4824afc1fd1e6e2fb": "exercise",
            "63b33ff5824afc1fd1e6e7b9": "journaling",
            "63b32f82824afc1fd1e6c891": "learn-language"
        }

        checkins_start_date = 20221231
        payload = TicktickPayloads.get_habits_checkins(habit_list, checkins_start_date)
        habit_checkins_raw = self.ticktick_client.post(self.habit_checkins_url,
                                                       payload,
                                                       token_required=True)["checkins"]
        habit_checkins = {habit_id: HabitUtilities.clean_habit_checkins(checkins) for habit_id, checkins in habit_checkins_raw.items()}
        return {habit_list[habit_id]: checkins for habit_id, checkins in habit_checkins.items() if checkins}


    def parse_ticktick_tasks(self, raw_tasks: List[dict]) -> List[dict]:

        column_tags = {
            "61c62f26824afc6c763523ec": "to-do",
            "61c62f34824afc6c763523fb": "analyze",
            "61c62f41824afc6c76352403": "in-progress",
            "61c62f48824afc6c76352411": "review",
            "61c62f4d824afc6c76352419": "done",
            "2afe1c885d4e4164bacc22d582ba50b8": "to-do",
            "36725d09fd3b46569f1e8dbbd2e4c1f3": "analyze",
            "fdd54b4fc75c435190a9e87617dd6bab": "in-progress",
            "b19e1b221573467baef4378e2dbf0571": "review",
            "e09901cc2b2d4fad99bccfbf539189f8": "done"
        }

        ticktick_tasks = []
        for raw_task in raw_tasks:
            task = dict()
            task[TaskData.TICKTICK_ID] = raw_task[ttp.ID]
            task[TaskData.NOTION_ID] = None
            task[TaskData.TITLE] = TaskUtilities.get_task_title(raw_task)
            task[TaskData.DUE_DATE] = TaskUtilities.get_task_date(raw_task)
            task[TaskData.FOCUS_TIME] = TaskUtilities.get_task_focus_time(raw_task)
            task[TaskData.DONE] = self.was_task_completed(task)

            task[TaskData.TAGS] = []
            task[TaskData.POINTS] = 0
            task[TaskData.ENERGY] = 0
            if ttp.TAGS in raw_task:
                task[TaskData.TAGS] = TaskUtilities.get_task_tags(raw_task)
                task[TaskData.POINTS] = TaskUtilities.get_task_estimation(raw_task, TaskData.POINTS)
                task[TaskData.ENERGY] = TaskUtilities.get_task_estimation(raw_task, TaskData.ENERGY)

            try:
                task[TaskData.STATUS] = column_tags[raw_task[ttp.COLUMN_ID]]
            except KeyError:
                task[TaskData.STATUS] = ""

            ticktick_tasks.append(task)

        return ticktick_tasks

    def filter_tasks(self, parameter: TaskTicktickParameters, value: Union[str, int, bool]) -> List[dict]:
        logging.info(f"Getting filtered tasks {parameter}: {value}")
        return list(filter(lambda task: task[parameter] == value, self.tasks))

    def get_relevant_tasks(self) -> List[dict]:
        """Return relevant tasks from ticktick as a dictionary

        Returns:
            relevant tasks (dict[str, dict]): The keys of the dictionary are the task ids (str) and the values are the task data (TaskData)
        """
        logging.info(f"Getting ticktick relevant tasks")
        project_ids = {
            "inbox_tasks": "inbox114478622",
            "life_kanban": "61c62f198f08c92d0584f678",
            "current_backlog": "61c634f58f08c92d058540ba",
            "tasks_backlog": "637a952f8f0812477fbdf0a6",
            "work_tasks": "61c62ff88f08c92d058504d5",
            "work_reminders": "5f71cb1e22d45e44fa87113a",
            "habits": "617f4bd08f08c83aa52559e0",
        }

        relevant_tasks = []
        for project_id in project_ids.values():
            relevant_tasks += self.filter_tasks(ttp.PROJECT_ID, project_id)

        relevant_tasks = list(filter(TaskUtilities.is_task_valid, relevant_tasks))
        relevant_tasks = self.parse_ticktick_tasks(relevant_tasks)
        relevant_tasks.sort(key=lambda task: task[td.TITLE])

        self.relevant_tasks = relevant_tasks
        return relevant_tasks

    def is_task_new(self, task: dict, notion_tasks) -> bool:
        logging.info(f"Checking if task was new {task}")

        def condition(notion_task):
            return task[TaskData.TICKTICK_ID] == notion_task[TaskData.TICKTICK_ID]

        return not any(map(condition, notion_tasks))

    def was_task_completed(self, task: dict) -> bool:
        def condition(completed_task):
            try:
                return task[td.TICKTICK_ID] == completed_task[ttp.ID] and task[td.DUE_DATE] in completed_task[ttp.START_DATE]
            except KeyError:
                return False

        return any(map(condition, self.completed_tasks))

    def was_task_updated(self, task: dict, notion_tasks: List[dict]) -> bool:
        logging.info(f"Checking if task was updated {task}")

        def condition(notion_task):
            if task[TaskData.TICKTICK_ID] == notion_task[TaskData.TICKTICK_ID]:
                tasks_equal = True
                for task_parameter in [parameter for parameter in TaskData if parameter not in [TaskData.NOTION_ID]]:
                    parameters_comparison = notion_task[task_parameter] == task[task_parameter]
                    tasks_equal &= parameters_comparison
                return not tasks_equal
            return False

        return any(map(condition, notion_tasks))

    def was_date_updated(self, task, notion_tasks: List[dict]):
        logging.info(f"Checking if date was updated {task}")

        def condition(notion_task):
            if task[TaskData.TICKTICK_ID] == notion_task[TaskData.TICKTICK_ID]:
                return notion_task[TaskData.DUE_DATE] != task[TaskData.DUE_DATE]
            return False

        return any(map(condition, notion_tasks))

    def was_task_deleted(self, task: dict) -> bool:
        logging.info(f"Checking if task was deleted {task}")

        def condition_deleted(deleted_task):
            if ttp.START_DATE in deleted_task:
                return task[td.TICKTICK_ID] == deleted_task[ttp.ID] and task[td.DUE_DATE] in deleted_task[ttp.START_DATE]

        def condition_abandoned(abandoned_task):
            if ttp.START_DATE in abandoned_task:
                return task[td.TICKTICK_ID] == abandoned_task[ttp.ID] and task[td.DUE_DATE] in abandoned_task[ttp.START_DATE]

        was_task_deleted = any(map(condition_deleted, self.deleted_tasks))
        was_task_abandoned = any(map(condition_abandoned, self.abandoned_tasks))
        is_reading_habit = set(task[td.TAGS]) == {"read", "habit"}

        return was_task_deleted or was_task_abandoned and not is_reading_habit

    def complete_tasks(self, notion: NotionController):
        logging.info(f"Completing tasks")
        relevant_tasks = notion.active_tasks.copy()
        for task in relevant_tasks:
            if self.was_task_completed(task):
                notion_id = notion.get_notion_id(task[td.TICKTICK_ID])
                notion.complete_task(notion_id)

    def delete_tasks(self, notion: NotionController):
        logging.info(f"Deleting tasks")
        relevant_tasks = notion.active_tasks.copy()
        for task in relevant_tasks:
            if self.was_task_deleted(task):
                notion_id = notion.get_notion_id(task[td.TICKTICK_ID])
                notion.delete_task(notion_id)

    def update_tasks(self, notion: NotionController):
        logging.info(f"Updating tasks")
        relevant_tasks = self.relevant_tasks.copy()
        for task in relevant_tasks:
            if self.was_task_updated(task, notion.active_tasks):
                notion_id = notion.get_notion_id(task[td.TICKTICK_ID])
                notion.update_task(notion_id, task)
                self.relevant_tasks.remove(task)

    def add_new_tasks(self, notion):
        logging.info(f"Adding tasks")
        relevant_tasks = self.relevant_tasks.copy()
        for task in relevant_tasks:
            if self.is_task_new(task, notion.active_tasks):
                created_task_data = notion.create_task(task)

                self.relevant_tasks.remove(task)

                if self.was_task_completed(task):
                    notion_id = created_task_data["id"]
                    notion.complete_task(notion_id)

    def get_checked_habits(self) -> List[dict]:

        def habits_filter(task):
            if ttp.TAGS in task:
                return "habit" in task[ttp.TAGS] and len(task[ttp.TAGS]) >= 4
            return False

        raw_checked_habits = list(filter(habits_filter, self.completed_tasks))
        checked_habits = self.parse_ticktick_tasks(raw_checked_habits)

        return checked_habits
