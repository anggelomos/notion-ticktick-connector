import json
from typing import List

from data.habit_notion_parameters import HabitNotionParameters as hnp
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
    def create_task(object_id, title: str, points: int, energy: int, focus_time: float, tags: List[str], due_date: str, ticktick_id: str, status: str) -> str:
        payload = {
                    "parent": {"database_id": object_id},
                    "properties": {
                                tnp.TITLE: {"title": [{"text": {"content": title}}]},
                                tnp.POINTS: {"number": points},
                                tnp.ENERGY: {"number": energy},
                        tnp.FOCUS_TIME: {"number": focus_time},
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
        if status:
            payload["properties"][tnp.STATUS] = {"select": {"name": status}}

        return json.dumps(payload)

    @staticmethod
    def update_task(title: str, points: int, energy: int, focus_time: float, done: bool, tags: List[str], due_date: str, ticktick_id: str, status: str) -> str:
        payload = {
                    "properties": {
                                tnp.TITLE: {"title": [{"text": {"content": title}}]},
                                tnp.POINTS: {"number": points},
                                tnp.ENERGY: {"number": energy},
                                tnp.FOCUS_TIME: {"number": focus_time},
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

        if status:
            payload["properties"][tnp.STATUS] = {"select": {"name": status}}

        return json.dumps(payload)

    @staticmethod
    def complete_task() -> str:
        payload = {
                    "properties": {
                        tnp.DONE: {"checkbox": True},
                        tnp.STATUS: {"select": {"name": "done"}}
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

    @staticmethod
    def get_habit_entry(habit: str, week_number: int, year: int) -> str:
        payload = {
                "filter": {
                    "and": [
                        {
                            "property": hnp.HABIT,
                            "multi_select": {
                                "contains": habit
                            }
                        },
                        {
                            "property": hnp.WEEK_NUMBER,
                            "number": {
                                "equals": week_number
                            }
                        },
                        {
                            "property": hnp.YEAR,
                            "number": {
                                "equals": year
                            }
                        }
                    ]
                }
            }

        return json.dumps(payload)

    @staticmethod
    def check_habit(day: str) -> str:
        payload = {
                    "properties": {
                        day: {
                            "checkbox": True
                        }
                    }
                }

        return json.dumps(payload)
