import requests
from requests.api import delete

from constants.task_data import TaskData


class NotionController:
    
    pages_url = "https://api.notion.com/v1/pages/"

    def __init__(self, auth_secret:str, notion_version:str, object_id:str):
        self._auth_secret = auth_secret
        self._notion_version = notion_version
        self.object_id = object_id

    def _get_headers(self) -> dict:
        headers = {'content-type': 'application/json',
            'Notion-Version': f'{self._notion_version}', 
            'Authorization': f'Bearer {self._auth_secret}'}

        return headers

    def _get_create_payload(self, title:str, points:int, done:bool, due_date:str) -> str:
        payload = """{{
                        "parent": {{ "database_id": "{0}" }},
                        "properties": 
                            {{
                                "title": {{"title": [{{"text": {{"content": "{1}"}}}}]}},
                                "Points": {{"number": {2}}},
                                "Done": {{"checkbox": {3}}},
                                "Due date": 
                                    {{"date": {{
                                        "start": "{4}",
                                        "end": null}}
                                    }}
                            }}
                    }}"""
        return payload.format(self.object_id, title, points, str(done).lower(), due_date)

    def _get_update_payload(self, title:str, points:int, done:bool, due_date:str, delete:bool=False) -> str:
        payload = """{{
                        "properties": 
                            {{
                                "title": {{"title": [{{"text": {{"content": "{1}"}}}}]}},
                                "Points": {{"number": {2}}},
                                "Done": {{"checkbox": {3}}},
                                "Due date": 
                                    {{"date": {{
                                        "start": "{4}",
                                        "end": null}}
                                    }}
                            }},
                        "archived": {5}
                    }}"""
        return payload.format(self.object_id, title, points, str(done).lower(), due_date, str(delete).lower())

    def create_task(self, task:tuple) -> str:
        task_data = task[1]
        payload = self._get_update_payload(task_data[TaskData.TITLE.value],
                                           task_data[TaskData.POINTS.value],
                                           task_data[TaskData.DONE.value],
                                           task_data[TaskData.DUE_DATE.value])

        response = requests.post(url=self.pages_url, data=payload, headers=self._get_headers())
        return response.json()["id"]
    
    def update_task(self, page_id, task:tuple):
        task_data = task[1]
        payload = self._get_update_payload(task_data[TaskData.TITLE.value],
                                           task_data[TaskData.POINTS.value],
                                           task_data[TaskData.DONE.value],
                                           task_data[TaskData.DUE_DATE.value])

        requests.patch(url=self.pages_url+page_id, data=payload, headers=self._get_headers())

    def delete_task(self, page_id, task:tuple):
        task_data = task[1]
        payload = self._get_update_payload(task_data[TaskData.TITLE.value],
                                           task_data[TaskData.POINTS.value],
                                           task_data[TaskData.DONE.value],
                                           task_data[TaskData.DUE_DATE.value],
                                           delete=True)

        requests.patch(url=self.pages_url+page_id, data=payload, headers=self._get_headers())
