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
    def get_active_tasks() -> dict:
        return {
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

    @staticmethod
    def create_task(database_id, title: str, points: int, energy: int, focus_time: float, tags: List[str],
                    due_date: str, ticktick_id: str, status: str, recurrent_id: str) -> str:
        payload = {
            "parent": {"database_id": database_id},
            "properties": {
                tnp.TITLE: {"title": [{"text": {"content": title}}]},
                tnp.POINTS: {"number": points},
                tnp.ENERGY: {"number": energy},
                tnp.FOCUS_TIME: {"number": focus_time},
                tnp.DONE: {"checkbox": False},
                tnp.ACTIVE: {"checkbox": True},
                tnp.RECURRENT_ID: {"rich_text": [{"text": {"content": recurrent_id}}]},
                tnp.TAGS: {
                    tnp.MULTI_SELECT: TaskUtilities.parse_tags(tags)
                },
                tnp.TICKTICK_ID: {"rich_text": [{"text": {"content": ticktick_id}}]}
            }
        }
        if status:
            payload["properties"][tnp.STATUS] = {"select": {"name": status}}

        if due_date:
            payload["properties"][tnp.DUE_DATE] = {
                tnp.DATE: {
                    tnp.START: due_date
                }
            }

        return json.dumps(payload)

    @staticmethod
    def add_expense(database_id, title: str, amount: float, date: str) -> str:
        payload = {
            "parent": {"database_id": database_id},
            "properties": {
                    "producto": {"title": [{"text": {"content": title}}]},
                    "egresos": {"number": amount},
                    "fecha": {tnp.DATE: {tnp.START: date}}
            }
        }

        return json.dumps(payload)

    @staticmethod
    def update_task(title: str, points: int, energy: int, focus_time: float, done: bool, tags: List[str], due_date: str,
                    ticktick_id: str, status: str, recurrent_id: bool) -> str:
        payload = {
            "properties": {
                tnp.TITLE: {"title": [{"text": {"content": title}}]},
                tnp.POINTS: {"number": points},
                tnp.ENERGY: {"number": energy},
                tnp.FOCUS_TIME: {"number": focus_time},
                tnp.DONE: {"checkbox": done},
                tnp.ACTIVE: {"checkbox": True},
                tnp.RECURRENT_ID: {"rich_text": [{"text": {"content": recurrent_id}}]},
                tnp.TAGS: {
                    tnp.MULTI_SELECT: TaskUtilities.parse_tags(tags)
                },
                tnp.DUE_DATE: {
                    tnp.DATE: None
                },
                tnp.TICKTICK_ID: {"rich_text": [{"text": {"content": ticktick_id}}]}
            },
            "archived": False
        }

        if due_date:
            payload["properties"][tnp.DUE_DATE][tnp.DATE] = {tnp.START: due_date}

        if status:
            payload["properties"][tnp.STATUS] = {"select": {"name": status}}

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
    def get_habit_entry(habit: str, year: int, week_number: int = None) -> dict:
        filters = [
            {
                "property": hnp.HABIT,
                "multi_select": {
                    "contains": habit
                }
            },
            {
                "property": hnp.YEAR,
                "number": {
                    "equals": year
                }
            }
        ]

        if week_number:
            filters.append({
                "property": hnp.WEEK_NUMBER,
                "number": {
                    "equals": week_number
                }
            })

        payload = {
            "filter": {
                "and": filters
            }
        }

        return payload

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

    @staticmethod
    def clean_habit_checkins() -> str:
        payload = {
            "properties": {
                "mon": {"checkbox": False},
                "tue": {"checkbox": False},
                "wed": {"checkbox": False},
                "thu": {"checkbox": False},
                "fri": {"checkbox": False},
                "sat": {"checkbox": False},
                "sun": {"checkbox": False}
            }
        }

        return json.dumps(payload)

    @staticmethod
    def get_task_by_ticktick_id(ticktick_id: str, due_date: str = None) -> dict:
        filters = [
            {
                "property": "Ticktick Id",
                "rich_text": {
                    "equals": ticktick_id
                }
            }
        ]

        if due_date:
            filters.append({
                "property": "Due date",
                "date": {
                    "equals": due_date
                }
            })
        else:
            filters.append({
                "property": "Due date",
                "date": {
                    "is_empty": True
                }
            })

        payload = {
            "filter": {
                "and": filters
            }
        }

        return payload
