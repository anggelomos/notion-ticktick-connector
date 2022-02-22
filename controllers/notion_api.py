import logging
from typing import List

import requests
from data.payloads.notion_payloads import NotionPayloads
from data.task_data import TaskData as td, TaskData
from utilities.task_utilities import TaskUtilities


class NotionAPI:
    
    base_url = "https://api.notion.com/v1"
    
    def __init__(self, auth_secret: str, notion_version: str):
        self._auth_secret = auth_secret
        self._notion_version = notion_version

    def _default_headers(self) -> dict:
        return NotionPayloads.get_headers(self._notion_version, self._auth_secret)
    
    def query_table(self, table_id: str, query: str) -> List[dict]:
        response = requests.post(url=self.base_url + "/databases/" + table_id + "/query",
                                 data=query,
                                 headers=self._default_headers())

        return response.json()["results"]

    def create_table_entry(self, payload: str) -> dict:
        response = requests.post(url=self.base_url + "/pages",
                                 data=payload,
                                 headers=self._default_headers())
        return response.json()

    def update_table_entry(self, page_id: str, payload: str):
        requests.patch(url=self.base_url + "/pages/" + page_id,
                       data=payload,
                       headers=self._default_headers())
