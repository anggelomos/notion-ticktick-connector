import json
from typing import List

from data.task_notion_parameters import TaskNotionParameters as tnp
from utilities.task_utilities import TaskUtilities


class NotionPayloads:

    @staticmethod
    def get_headers(notion_version: str, auth_secret: str) -> dict:
        headers = {
                    "content-type": "application/json",
                    "Notion-Version": f"{notion_version}",
                    "Authorization": f"Bearer {auth_secret}"
                }
        return headers

    @staticmethod
    def get_active_tasks():
        payload = {
                        "filter": {
                            "and": [
                                {
                                    "property": "Active",
                                    "checkbox": {
                                        "equals": True
                                    }
                                }
                            ]
                        }
                    }
        return json.dumps(payload)

    @staticmethod
    def create_task(object_id, title: str, points: int, energy: int, tags: List[str], due_date: str, ticktick_id: str) -> str:
        payload = {
                    "parent": {"database_id": object_id},
                    "properties": {
                                tnp.TITLE: {"title": [{"text": {"content": title}}]},
                                tnp.POINTS: {"number": points},
                                tnp.ENERGY: {"number": energy},
                                tnp.DONE: {"checkbox": False},
                                tnp.ACTIVE: {"checkbox": True},
                                tnp.TAGS: {
                                        tnp.MULTI_SELECT: TaskUtilities.parse_tags(tags)
                                    },
                                tnp.DUE_DATE: {
                                    tnp.DATE: {
                                        tnp.START: due_date
                                    }
                                },
                                tnp.TICKTICK_ID: {"rich_text": [{"text": {"content": ticktick_id}}]}
                            }
                    }

        return json.dumps(payload)

    @staticmethod
    def update_task(title: str, points: int, energy: int, done: bool, tags: List[str], due_date: str, ticktick_id: str) -> str:
        payload = {
                    "properties": {
                                tnp.TITLE: {"title": [{"text": {"content": title}}]},
                                tnp.POINTS: {"number": points},
                                tnp.ENERGY: {"number": energy},
                                tnp.DONE: {"checkbox": done},
                                tnp.ACTIVE: {"checkbox": True},
                                tnp.TAGS: {
                                        tnp.MULTI_SELECT: TaskUtilities.parse_tags(tags)
                                    },
                                tnp.DUE_DATE: {
                                    tnp.DATE: {
                                        tnp.START: due_date
                                    }
                                },
                                tnp.TICKTICK_ID: {"rich_text": [{"text": {"content": ticktick_id}}]}
                            },
                    "archived": False
                    }

        return json.dumps(payload)

    @staticmethod
    def complete_task() -> str:
        payload = {
                    "properties": {
                        tnp.DONE: {
                            "checkbox": True
                        }
                    }
                }

        return json.dumps(payload)

    @staticmethod
    def delete_task() -> str:
        payload = {
                    "archived": True
                }

        return json.dumps(payload)

    @staticmethod
    def change_task_state(active: bool) -> str:
        payload = {
                    "properties": {
                        tnp.ACTIVE: {
                            "checkbox": active
                        }
                    }
                }

        return json.dumps(payload)
