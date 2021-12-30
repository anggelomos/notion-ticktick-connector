import logging
from typing import List, Union

from controllers.notion_controller import NotionController
from data.task_ticktick_parameters import TaskTicktickParameters as ttd, TaskTicktickParameters
from controllers.ticktick_api import TicktickAPI
from data.task_data import TaskData as td, TaskData
from utilities.task_utilities import TaskUtilities


class TicktickController:
    
    active_tasks = {}
    notion_ids = {}
    BASE_URL = "/api/v2"
    get_state = BASE_URL + "/batch/check/0"
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
        self.sync()

    def sync(self):
        logging.info(f"Syncing ticktick tasks")
        response = self.ticktick_client.get(self.get_state, token_required=True)

        self.inbox_id = response['inboxId']
        self.project_folders = response['projectGroups']
        self.projects = response['projectProfiles']
        self.tasks = response['syncTaskBean']['update']
        self.tags = response['tags']
        self.get_relevant_tasks()
        self.completed_tasks = self.ticktick_client.get(self.completed_tasks_url, token_required=True)
        self.deleted_tasks = self.ticktick_client.get(self.deleted_tasks_url, token_required=True)["tasks"]
        self.abandoned_tasks = self.ticktick_client.get(self.abandoned_tasks_url, token_required=True)

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
            "work_tasks": "61c62ff88f08c92d058504d5",
            "work_reminders": "5f71cb1e22d45e44fa87113a",
        }

        relevant_tasks = []
        for project_id in project_ids.values():
            relevant_tasks += self.filter_tasks(ttd.PROJECT_ID, project_id)

        relevant_tasks = list(filter(TaskUtilities.is_task_valid, relevant_tasks))
        relevant_tasks = TaskUtilities.parse_ticktick_tasks(relevant_tasks)
        relevant_tasks.sort(key=lambda task: task[td.TITLE])

        self.relevant_tasks = relevant_tasks
        return relevant_tasks

    def is_task_new(self, task: dict, notion_tasks) -> bool:
        logging.info(f"Checking if task was new {task}")
        def condition(notion_task):
            return task[TaskData.TICKTICK_ID] == notion_task[TaskData.TICKTICK_ID]

        return not any(map(condition, notion_tasks))

    def was_task_completed(self, task: dict) -> bool:
        logging.info(f"Checking if task was completed {task}")
        def condition(completed_task):
            return task[td.TICKTICK_ID] == completed_task[ttd.ID] and task[td.DUE_DATE] in completed_task[ttd.START_DATE]

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
            return task[td.TICKTICK_ID] == deleted_task[ttd.ID] and task[td.DUE_DATE] in deleted_task[ttd.START_DATE]

        def condition_abandoned(abandoned_task):
            return task[td.TICKTICK_ID] == abandoned_task[ttd.ID] and task[td.DUE_DATE] in abandoned_task[ttd.START_DATE]

        was_task_deleted = any(map(condition_deleted, self.deleted_tasks))
        was_task_abandoned = any(map(condition_abandoned, self.abandoned_tasks))

        return was_task_deleted or was_task_abandoned

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
                if self.was_date_updated(task, notion.active_tasks):
                    notion.change_task_state(notion_id, active=False)
                    notion.create_task(task)
                else:
                    notion.update_task(notion_id, task)

                self.relevant_tasks.remove(task)

    def add_new_tasks(self, notion):
        logging.info(f"Adding tasks")
        relevant_tasks = self.relevant_tasks.copy()
        for task in relevant_tasks:
            if self.is_task_new(task, notion.active_tasks):
                notion.create_task(task)

                self.relevant_tasks.remove(task)
