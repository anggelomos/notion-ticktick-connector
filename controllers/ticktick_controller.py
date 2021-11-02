
from typing import Dict, List
from ticktick.api import TickTickClient
from ticktick.oauth2 import OAuth2
from constants.task_data import TaskData
from constants.task_status import TaskStatus
from task_utilities import TaskUtilities


class TicktickController:
    
    active_tasks = {}
    notion_ids = {}
    completed_tasks_url = "https://api.ticktick.com/api/v2/project/all/closed?from=&to=&status=Completed"
    abandoned_tasks_url = "https://api.ticktick.com/api/v2/project/all/closed?from=&to=&status=Abandoned"
    deleted_tasks_url = "https://api.ticktick.com/api/v2/project/all/trash/pagination?start=0&limit=50"

    def __init__(self, client_id:str, client_secret:str, uri:str, username:str, password:str):
        _auth_client = OAuth2(client_id=client_id,
                     client_secret=client_secret,
                     redirect_uri=uri)

        self.ticktick_client = TickTickClient(username, password, _auth_client)
        self.active_tasks = TaskUtilities.get_active_tasks()
        self.notion_ids = TaskUtilities.get_notion_ids()

    def _search_tasks_by_projectid(self, project_id:str) -> List[str]:
        tasks = self.ticktick_client.get_by_fields(projectId=project_id)
       
        if isinstance(tasks, list):
            return tasks
        return [tasks]
    
    def sniff_tasks(self) -> Dict[str, dict]:
        """Return relevant tasks from ticktick as a dictionary

        Returns:
            relevant tasks (dict[str, dict]): The keys of the dictionary are the task ids (str) and the values are the task data (TaskData)
        """
        project_ids = {
            "inbox_tasks": "inbox114478622",
            "groomed_tasks": "60c7672d8f08a0970bd3f062",
            "work_tasks": "5f71cb0a22d45e44fa871139",
            "work_reminders": "5f71cb1e22d45e44fa87113a",
            "personal_routines": "5e57221d22d41cd6340b091f",
            "housekeep_routines": "5f15ad0622d4198163ac8d06",
            "goal_milestones": "5ffb376f8f08237f3cf9d929",
            "housekeep_reminders": "5f15ad1a22d4198163ac8d07",
        }

        relevant_tasks = []
        for project_id in project_ids.values():
            relevant_tasks += self._search_tasks_by_projectid(project_id)

        relevant_tasks = list(filter(TaskUtilities.is_task_due_to_today, relevant_tasks))
        relevant_tasks = dict(map(TaskUtilities.clean_tasks, relevant_tasks))

        return relevant_tasks
 
    def get_new_task_status(self, task: tuple) -> TaskStatus:

        if self.is_task_new(task):
            task_status = TaskStatus.NEW
        elif self.was_task_modified(task):
            task_status = TaskStatus.UPDATED
        else:
            task_status = TaskStatus.NO_CHANGE

        return [task, task_status]

    def get_existing_task_status(self, task: tuple) -> TaskStatus:

        if self.was_task_completed(task):
            task_status = TaskStatus.COMPLETED
        elif self.was_task_deleted(task):
            task_status = TaskStatus.DELETED
        else:
            task_status = TaskStatus.NO_CHANGE

        return [task, task_status]
        
    def does_task_already_exists(self, task: tuple) -> bool:
        return any(map(lambda existing_task: existing_task==task, self.active_tasks.items()))

    def is_task_new(self, task: tuple) -> bool:
        return all(map(lambda existing_task: existing_task[0]!=task[0], self.active_tasks.items()))

    def was_task_completed(self, task: tuple) -> bool:
        completed_tasks = self.ticktick_client.http_get(self.completed_tasks_url, cookies=self.ticktick_client.cookies)

        def recurring_task_condition(existing_task:dict) -> bool:
            try:
                return existing_task["repeatTaskId"] == task[0] and task[1][TaskData.DUE_DATE.value] in existing_task["completedTime"]
            except KeyError:
                return False

        recurring_task_completed = any(map(recurring_task_condition, completed_tasks))
        regular_task_completed = any(map(lambda existing_task: (existing_task["id"] == task[0]), completed_tasks))

        return regular_task_completed or recurring_task_completed

    def was_task_modified(self, task: tuple) -> bool:
        condition = lambda existing_task: existing_task[0]==task[0] and existing_task[1]!=task[1]
        return any(map(condition, self.active_tasks.items()))

    def was_task_deleted(self, task: tuple) -> bool:
        deleted_tasks = self.ticktick_client.http_get(self.deleted_tasks_url, cookies=self.ticktick_client.cookies)
        abandoned_tasks = self.ticktick_client.http_get(self.abandoned_tasks_url, cookies=self.ticktick_client.cookies)
        
        was_task_abandoned = any(map(lambda existing_task: existing_task["id"]==task[0], deleted_tasks["tasks"]))
        was_task_deleted = any(map(lambda existing_task: existing_task["id"]==task[0], abandoned_tasks))

        return was_task_deleted or was_task_abandoned
    