import logging
from typing import List

import requests
from data.payloads.notion_payloads import NotionPayloads
from data.task_data import TaskData as td, TaskData
from utilities.task_utilities import TaskUtilities


class NotionController:
    
    base_url = "https://api.notion.com/v1"

    def __init__(self, auth_secret: str, notion_version: str, object_id: str):
        self._auth_secret = auth_secret
        self._notion_version = notion_version
        self.object_id = object_id
        self.active_tasks = []
        self.get_active_tasks()

    def get_active_tasks(self) -> List[dict]:
        logging.info("Getting notion active tasks")
        payload = NotionPayloads.get_active_tasks()
        response = requests.post(url=self.base_url+"/databases/"+self.object_id+"/query",
                                 data=payload,
                                 headers=NotionPayloads.get_headers(self._notion_version, self._auth_secret))

        raw_tasks = response.json()["results"]
        notion_tasks = TaskUtilities.parse_notion_tasks(raw_tasks)
        notion_tasks.sort(key=lambda task: task[TaskData.TITLE])

        self.active_tasks = notion_tasks
        return notion_tasks

    def get_notion_id(self, ticktick_id: str) -> str:
        notion_id = list(filter(lambda task: task[td.TICKTICK_ID] == ticktick_id, self.active_tasks))[0][td.NOTION_ID]
        logging.info(f"Got notion id {notion_id} from ticktick id {ticktick_id}")
        return notion_id

    def create_task(self, task: dict) -> dict:
        logging.info(f"Creating task {task}")
        payload = NotionPayloads.create_task(self.object_id,
                                             task[TaskData.TITLE],
                                             task[TaskData.POINTS],
                                             task[TaskData.ENERGY],
                                             task[TaskData.TAGS],
                                             task[TaskData.DUE_DATE],
                                             task[TaskData.TICKTICK_ID],
                                             task[TaskData.STATUS])

        response = requests.post(url=self.base_url+"/pages",
                                 data=payload,
                                 headers=NotionPayloads.get_headers(self._notion_version, self._auth_secret))
        return response.json()
    
    def update_task(self, page_id: str, task: dict):
        logging.info(f"Updating task {page_id} with info {task}")
        payload = NotionPayloads.update_task(task[TaskData.TITLE],
                                             task[TaskData.POINTS],
                                             task[TaskData.ENERGY],
                                             task[TaskData.DONE],
                                             task[TaskData.TAGS],
                                             task[TaskData.DUE_DATE],
                                             task[TaskData.TICKTICK_ID],
                                             task[TaskData.STATUS])

        requests.patch(url=self.base_url+"/pages/"+page_id,
                       data=payload,
                       headers=NotionPayloads.get_headers(self._notion_version, self._auth_secret))

    def complete_task(self, page_id: str):
        logging.info(f"Marking task {page_id} as completed")
        payload = NotionPayloads.complete_task()

        requests.patch(url=self.base_url+"/pages/"+page_id,
                       data=payload,
                       headers=NotionPayloads.get_headers(self._notion_version, self._auth_secret))

    def delete_task(self, page_id: str):
        logging.info(f"Deleting task {page_id}")
        payload = NotionPayloads.delete_task()

        requests.patch(url=self.base_url+"/pages/"+page_id,
                       data=payload,
                       headers=NotionPayloads.get_headers(self._notion_version, self._auth_secret))

    def change_task_state(self, page_id: str, active: bool):
        logging.info(f"Changing task {page_id} state to {active}")
        payload = NotionPayloads.change_task_state(active)

        requests.patch(url=self.base_url+"/pages/"+page_id,
                       data=payload,
                       headers=NotionPayloads.get_headers(self._notion_version, self._auth_secret))
