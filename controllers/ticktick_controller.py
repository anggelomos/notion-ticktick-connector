import logging
import datetime
from typing import List

from config import CHECKINS_START_DATE
from data.payloads.ticktick_payloads import TicktickPayloads
from data.task_ticktick_parameters import TaskTicktickParameters as ttp
from controllers.ticktick_api import TicktickAPI
from data.task_data import TaskData as td, TaskData
from data.ticktick_ids import TicktickIds
from utilities.habit_utilities import HabitUtilities
from utilities.task_utilities import TaskUtilities


class TicktickController:
    current_date = datetime.datetime.utcnow()
    date_two_weeks_ago = (current_date - datetime.timedelta(days=14)).strftime("%Y-%m-%d")
    date_tomorrow = (current_date + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    active_tasks = {}
    notion_ids = {}
    BASE_URL = "/api/v2"
    get_state_url = BASE_URL + "/batch/check/0"
    curl_task_url = BASE_URL + "/batch/task"
    habit_checkins_url = BASE_URL + "/habitCheckins/query"
    completed_tasks_url = BASE_URL + f"/project/all/closed?from={date_two_weeks_ago}%2005:00:00&to={date_tomorrow}" \
                                     f"%2004:59:00&status=Completed&limit=500"
    abandoned_tasks_url = BASE_URL + f"/project/all/closed?from={date_two_weeks_ago}%2005:00:00&to={date_tomorrow}" \
                                     f"%2004:59:00&status=Abandoned&limit=500"
    deleted_tasks_url = BASE_URL + "/project/all/trash/pagination?start=0&limit=500"

    def __init__(self, username: str, password: str):
        self.ticktick_client = TicktickAPI(username, password)
        self.state = {}
        self.raw_tasks = []
        self.tasks = []
        self.relevant_tasks = []
        self.completed_tasks = []
        self.deleted_tasks = []
        self.abandoned_tasks = []

    def get_tasks(self):
        logging.info("Getting ticktick tasks")
        response = self.ticktick_client.get(self.get_state_url, token_required=True)
        self.completed_tasks = self.parse_ticktick_tasks(self.ticktick_client.get(self.completed_tasks_url,
                                                                                  token_required=True),
                                                         completed_tasks=True)
        self.deleted_tasks = self.parse_ticktick_tasks(self.ticktick_client.get(self.deleted_tasks_url,
                                                                                token_required=True)["tasks"])
        self.abandoned_tasks = self.parse_ticktick_tasks(self.ticktick_client.get(self.abandoned_tasks_url,
                                                                                  token_required=True))

        self.raw_tasks = response['syncTaskBean']['update']
        self.tasks = self.parse_ticktick_tasks(self.raw_tasks) + self.completed_tasks
        self.get_relevant_tasks()

    def complete_task(self, task: dict):
        logging.info(f"Completing task {task}")
        payload = TicktickPayloads.complete_task(task[ttp.ID], task[ttp.PROJECT_ID])
        self.ticktick_client.post(self.curl_task_url, payload, token_required=True)

    def get_habits(self):
        logging.info("Getting habits")

        payload = TicktickPayloads.get_habits_checkins(TicktickIds.HABIT_LIST, CHECKINS_START_DATE)
        habit_checkins_raw = self.ticktick_client.post(self.habit_checkins_url,
                                                       payload,
                                                       token_required=True)["checkins"]
        habit_checkins = {habit_id: HabitUtilities.clean_habit_checkins(checkins) for habit_id, checkins
                          in habit_checkins_raw.items()}
        return {TicktickIds.HABIT_LIST[habit_id]: checkins for habit_id, checkins in habit_checkins.items() if checkins}

    def parse_ticktick_tasks(self, raw_tasks: List[dict], completed_tasks: bool = False) -> List[dict]:
        ticktick_tasks = []
        for raw_task in raw_tasks:
            if raw_task[ttp.PROJECT_ID] not in TicktickIds.PROJECT_IDS.values():
                continue

            task = dict()
            task[TaskData.TICKTICK_ID] = raw_task[ttp.ID]
            task[TaskData.NOTION_ID] = None
            task[TaskData.TITLE] = TaskUtilities.get_task_title(raw_task)
            task[TaskData.FOCUS_TIME] = TaskUtilities.get_task_focus_time(raw_task)

            task[TaskData.RECURRENT_ID] = ""
            if ttp.REPEAT_TASK_ID in raw_task:
                task[TaskData.RECURRENT_ID] = raw_task[ttp.REPEAT_TASK_ID]

            task[TaskData.DONE] = self.was_task_completed(task)
            if completed_tasks:
                task[TaskData.DONE] = True

            task[TaskData.TAGS] = []
            task[TaskData.POINTS] = 0
            task[TaskData.ENERGY] = 0
            if ttp.TAGS in raw_task:
                task[TaskData.TAGS] = TaskUtilities.get_task_tags(raw_task)
                task[TaskData.POINTS] = TaskUtilities.get_task_estimation(raw_task, TaskData.POINTS)
                task[TaskData.ENERGY] = TaskUtilities.get_task_estimation(raw_task, TaskData.ENERGY)

            task[TaskData.DUE_DATE] = ""
            if ttp.DUE_DATE in raw_task:
                task[TaskData.DUE_DATE] = TaskUtilities.get_task_date(raw_task)

            try:
                task[TaskData.STATUS] = TicktickIds.COLUMN_TAGS[raw_task[ttp.COLUMN_ID]]
            except KeyError:
                task[TaskData.STATUS] = ""

            ticktick_tasks.append(task)

        return ticktick_tasks

    def get_relevant_tasks(self) -> List[dict]:
        """Return relevant tasks from ticktick as a dictionary

        Returns:
            relevant tasks (dict[str, dict]): The keys of the dictionary are the task ids (str)
            and the values are the task data (TaskData)
        """
        logging.info("Getting ticktick relevant tasks")

        relevant_tasks = self.tasks
        relevant_tasks = list(filter(TaskUtilities.is_task_valid, relevant_tasks))
        relevant_tasks.sort(key=lambda task: task[td.TITLE])

        self.relevant_tasks = relevant_tasks
        return relevant_tasks

    def was_task_completed(self, task: dict) -> bool:
        def condition(completed_task):
            try:
                return task[td.TICKTICK_ID] == completed_task[td.TICKTICK_ID] and\
                       task[td.DUE_DATE] == completed_task[td.DUE_DATE]
            except KeyError:
                return False

        return any(map(condition, self.completed_tasks))
