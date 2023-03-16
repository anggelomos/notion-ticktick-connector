import json
from typing import List

import requests
from data.payloads.notion_payloads import NotionPayloads


class NotionAPI:

    base_url = "https://api.notion.com/v1"

    def __init__(self, auth_secret: str, notion_version: str):
        self._auth_secret = auth_secret
        self._notion_version = notion_version

    def _default_headers(self) -> dict:
        return NotionPayloads.get_headers(self._notion_version, self._auth_secret)

    def query_table(self, table_id: str, query: dict) -> List[dict]:
        next_page_id = None
        first_request = True
        all_results = []

        while next_page_id or first_request:
            first_request = False

            response = requests.post(url=self.base_url + "/databases/" + table_id + "/query",
                                     data=json.dumps(query),
                                     headers=self._default_headers()).json()

            all_results += response.get("results")
            next_page_id = response.get("next_cursor")

            if next_page_id:
                query["start_cursor"] = next_page_id

        return all_results

    def create_table_entry(self, payload: str) -> dict:
        response = requests.post(url=self.base_url + "/pages",
                                 data=payload,
                                 headers=self._default_headers())
        return response.json()

    def update_table_entry(self, page_id: str, payload: str):
        requests.patch(url=self.base_url + "/pages/" + page_id,
                       data=payload,
                       headers=self._default_headers())
