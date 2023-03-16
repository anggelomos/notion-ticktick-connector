import logging
from typing import List
from controllers.notion_api import NotionAPI
from data.payloads.notion_payloads import NotionPayloads
from data.task_data import TaskData as td, TaskData
from utilities.habit_utilities import HabitUtilities
from utilities.task_utilities import TaskUtilities


class NotionController:

    base_url = "https://api.notion.com/v1"
    tasks_table_id = "811f2937421e488793c3441b8ca65509"
    habits_table_id = "b19a57ac5bd14747bcf4eb0d98adef10"

    def __init__(self, auth_secret: str, notion_version: str):
        self.notion_client = NotionAPI(auth_secret, notion_version)
        self.active_tasks = []

    def get_active_tasks(self) -> List[dict]:
        logging.info("Getting notion active tasks")
        payload = NotionPayloads.get_active_tasks()

        raw_tasks = self.notion_client.query_table(self.tasks_table_id, payload)
        notion_tasks = TaskUtilities.parse_notion_tasks(raw_tasks)
        notion_tasks.sort(key=lambda task: task[TaskData.TITLE])

        self.active_tasks = notion_tasks
        return notion_tasks

    def get_notion_id(self, ticktick_id: str) -> str:
        notion_id = list(filter(lambda task: task[td.TICKTICK_ID] == ticktick_id, self.active_tasks))[0][td.NOTION_ID]
        logging.info(f"Got notion id {notion_id} from ticktick id {ticktick_id}")
        return notion_id

    def is_task_already_created(self, ticktick_id: str, due_date: str) -> bool:
        logging.info(f"Checking if task with ticktick id {ticktick_id} is already created in notion")
        payload = NotionPayloads.get_task_by_ticktick_id(ticktick_id, due_date)
        raw_tasks = self.notion_client.query_table(self.tasks_table_id, payload)
        return len(raw_tasks) > 0

    def create_task(self, task: dict) -> dict:
        logging.info(f"Creating task {task}")

        if task[TaskData.DONE]:
            task[TaskData.STATUS] = "done"

        payload = NotionPayloads.create_task(self.tasks_table_id,
                                             task[TaskData.TITLE],
                                             task[TaskData.POINTS],
                                             task[TaskData.ENERGY],
                                             task[TaskData.FOCUS_TIME],
                                             task[TaskData.TAGS],
                                             task[TaskData.DUE_DATE],
                                             task[TaskData.TICKTICK_ID],
                                             task[TaskData.STATUS],
                                             task[TaskData.RECURRENT_ID])

        if not self.is_task_already_created(task[TaskData.TICKTICK_ID], task[TaskData.DUE_DATE]):
            return self.notion_client.create_table_entry(payload)

    def update_task(self, page_id: str, task: dict):
        logging.info(f"Updating task {page_id} with info {task}")

        if task[TaskData.DONE]:
            task[TaskData.STATUS] = "done"

        payload = NotionPayloads.update_task(task[TaskData.TITLE],
                                             task[TaskData.POINTS],
                                             task[TaskData.ENERGY],
                                             task[TaskData.FOCUS_TIME],
                                             task[TaskData.DONE],
                                             task[TaskData.TAGS],
                                             task[TaskData.DUE_DATE],
                                             task[TaskData.TICKTICK_ID],
                                             task[TaskData.STATUS],
                                             task[TaskData.RECURRENT_ID])

        self.notion_client.update_table_entry(page_id, payload)

    def delete_task(self, page_id: str):
        logging.info(f"Deleting task {page_id}")
        payload = NotionPayloads.delete_task()

        self.notion_client.update_table_entry(page_id, payload)

    def change_task_state(self, page_id: str, active: bool):
        logging.info(f"Changing task {page_id} state to {active}")
        payload = NotionPayloads.change_task_state(active)

        self.notion_client.update_table_entry(page_id, payload)

    def clean_habit_checkins(self, habit: str, year: int, week: int):
        logging.info("Cleaning habit checkins")
        payload = NotionPayloads.get_habit_entry(habit, year, week)
        entry = self.notion_client.query_table(self.habits_table_id, payload)[0]
        self.notion_client.update_table_entry(entry["id"], NotionPayloads.clean_habit_checkins())

    def get_habit_checkins(self, habit: str, year: int) -> int:
        payload = NotionPayloads.get_habit_entry(habit, year)
        habit_entries = self.notion_client.query_table(self.habits_table_id, payload)

        amount_checkins = 0
        for entry in habit_entries:
            amount_checkins += entry["properties"]["Amount checks"]["formula"]["number"]

        return amount_checkins

    def check_habits(self, habits_to_check: dict):
        logging.info("Checking habits in Notion")

        for habit, checkins in habits_to_check.items():
            logging.info(f"Checking habit {habit}")
            _, last_checkin_week, last_checkin_year = HabitUtilities.parse_habit_date(checkins[-1])
            current_checkins = self.get_habit_checkins(habit, last_checkin_year)
            if current_checkins == len(checkins):
                continue

            self.clean_habit_checkins(habit, last_checkin_year, last_checkin_week-1)
            self.clean_habit_checkins(habit, last_checkin_year, last_checkin_week)
            for date in checkins:
                day, week_number, year = HabitUtilities.parse_habit_date(date)

                if week_number < last_checkin_week-1:
                    continue

                habit_entry_payload = NotionPayloads.get_habit_entry(habit, year, week_number)
                habit_entry_id = self.notion_client.query_table(self.habits_table_id, habit_entry_payload)[0]["id"]

                check_habit_payload = NotionPayloads.check_habit(day)
                self.notion_client.update_table_entry(habit_entry_id, check_habit_payload)
