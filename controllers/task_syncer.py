import logging
from typing import List, Tuple

from controllers.notion_controller import NotionController
from controllers.ticktick_controller import TicktickController
from data.task_data import TaskData as td, TaskData
from data.task_ticktick_parameters import TaskTicktickParameters as ttp
from data.ticktick_ids import TicktickIds as ttids
from utilities.task_utilities import TaskUtilities


class TaskSyncer:

    def __init__(self, notion: NotionController = None, ticktick: TicktickController = None):
        self.notion = notion
        self.ticktick = ticktick

        self.notion_unsynced_tasks = []
        self.ticktick_unsynced_tasks = []

    def get_unsynced_tasks(self, notion_tasks: List[dict], ticktick_tasks: List[dict]) -> Tuple[List[dict], List[dict]]:
        notion_tasks_ids = set([(task[TaskData.TICKTICK_ID], task[TaskData.DUE_DATE]) for task in notion_tasks])
        ticktick_tasks_ids = set([(task[TaskData.TICKTICK_ID], task[TaskData.DUE_DATE]) for task in ticktick_tasks])

        unsynced_tasks_ids = notion_tasks_ids.symmetric_difference(ticktick_tasks_ids)

        def is_task_unsynced(task) -> bool:
            for unsynced_tasks_id in unsynced_tasks_ids:
                if task[TaskData.TICKTICK_ID] == unsynced_tasks_id[0] and \
                        task[TaskData.DUE_DATE] == unsynced_tasks_id[1]:
                    return True
            return False

        self.notion_unsynced_tasks = list(filter(is_task_unsynced, notion_tasks))
        self.ticktick_unsynced_tasks = list(filter(is_task_unsynced, ticktick_tasks))
        return self.notion_unsynced_tasks, self.ticktick_unsynced_tasks

    def sync_ticktick_tasks(self):
        logging.info("Syncing ticktick tasks")
        for task in self.ticktick_unsynced_tasks:
            if self.was_task_updated(task):
                self.update_task(task)
            elif self.was_task_added(task):
                self.add_task(task)
            else:
                logging.warning(f"TICKTICK TASK {task[TaskData.TICKTICK_ID]} WITH DUE DATE {task[TaskData.DUE_DATE]} "
                                f"WAS NOT SYNCED")

    def sync_notion_tasks(self):
        logging.info("Syncing notion tasks")
        for task in self.notion_unsynced_tasks:
            if self.is_task_recurrent(task):
                task = self.update_recurrent_task(task)

            if task is None:
                continue

            task_updated = self.was_notion_task_updated(task)
            if task_updated:
                continue

            if self.was_task_abandoned(task):
                self.abandon_task(task)
            elif self.was_task_deleted(task):
                self.delete_task(task)
            else:
                logging.warning(f"NOTION TASK {task[TaskData.TICKTICK_ID]} WITH DUE DATE {task[TaskData.DUE_DATE]} "
                                f"WAS NOT SYNCED")
                self.notion.change_task_state(task[TaskData.NOTION_ID], active=False)

    @staticmethod
    def is_task_recurrent(task: dict) -> bool:
        return task[td.TICKTICK_ID] == task[td.RECURRENT_ID]

    def was_notion_task_updated(self, task: dict) -> bool:
        def search_updated_task(ticktick_tasks):
            date_comparison = True
            if task[td.RECURRENT_ID]:
                date_comparison = task[td.DUE_DATE] == ticktick_tasks[td.DUE_DATE]

            return task[td.TICKTICK_ID] == ticktick_tasks[td.TICKTICK_ID] and date_comparison

        updated_task = next(filter(search_updated_task, self.ticktick.relevant_tasks), None)

        if updated_task:
            updated_task[td.NOTION_ID] = task[td.NOTION_ID]
            self.notion.update_task(task[td.NOTION_ID], updated_task)
            return True
        return False

    def was_task_deleted(self, task: dict) -> bool:
        logging.info(f"Checking if task was deleted {task}")

        def condition_deleted(deleted_task):
            return task[TaskData.TICKTICK_ID] == deleted_task[TaskData.TICKTICK_ID] and \
                   task[TaskData.DUE_DATE] == deleted_task[TaskData.DUE_DATE]

        was_task_deleted = any(map(condition_deleted, self.ticktick.deleted_tasks))
        return was_task_deleted

    def was_task_abandoned(self, task) -> bool:
        logging.info(f"Checking if task was abandoned {task}")

        def condition_abandoned(abandoned_task):
            return task[TaskData.TICKTICK_ID] == abandoned_task[TaskData.TICKTICK_ID] and \
                   task[TaskData.DUE_DATE] == abandoned_task[TaskData.DUE_DATE]

        was_task_abandoned = any(map(condition_abandoned, self.ticktick.abandoned_tasks))
        return was_task_abandoned

    def was_task_updated(self, task: dict):
        logging.info(f"Checking if task was updated {task}")

        def condition(notion_task):
            if task[TaskData.TICKTICK_ID] == notion_task[TaskData.TICKTICK_ID]:
                tasks_equal = True
                for task_parameter in [parameter for parameter in TaskData if parameter not in [TaskData.NOTION_ID]]:
                    parameters_comparison = notion_task[task_parameter] == task[task_parameter]
                    tasks_equal &= parameters_comparison
                return not tasks_equal
            return False

        return any(map(condition, self.notion.active_tasks))

    def was_task_added(self, task: dict) -> bool:
        logging.info(f"Checking if task was new {task}")

        def condition(notion_task):
            return task[TaskData.TICKTICK_ID] == notion_task[TaskData.TICKTICK_ID] and \
                   task[TaskData.DUE_DATE] == notion_task[TaskData.DUE_DATE]

        return not any(map(condition, self.notion.active_tasks))

    def update_recurrent_task(self, task):

        def search_task_id_with_date(ticktick_tasks):
            return task[td.RECURRENT_ID] == ticktick_tasks[td.RECURRENT_ID] and \
                   task[td.DUE_DATE] == ticktick_tasks[td.DUE_DATE]

        def search_task_id(ticktick_tasks):
            return task[td.RECURRENT_ID] == ticktick_tasks[td.RECURRENT_ID] and \
                   ticktick_tasks[td.TICKTICK_ID] != ticktick_tasks[td.RECURRENT_ID]

        found_task = next(filter(search_task_id_with_date, self.ticktick.relevant_tasks), None)
        if not found_task:
            found_task = next(filter(search_task_id_with_date, self.ticktick.abandoned_tasks), None)
        if not found_task:
            found_task = next(filter(search_task_id_with_date, self.ticktick.deleted_tasks), None)

        if not found_task:
            found_task = next(filter(search_task_id, self.ticktick.relevant_tasks), None)
        if not found_task:
            found_task = next(filter(search_task_id, self.ticktick.abandoned_tasks), None)
        if not found_task:
            found_task = next(filter(search_task_id, self.ticktick.deleted_tasks), None)

        if found_task and self.notion.is_task_already_created(found_task[td.TICKTICK_ID], found_task[td.DUE_DATE]):
            if task[td.DUE_DATE] == found_task[td.DUE_DATE]:
                self.notion.delete_task(task[td.NOTION_ID])
            else:
                self.notion.change_task_state(task[td.NOTION_ID], active=False)
            return None

        if found_task and found_task[td.TICKTICK_ID] != task[td.TICKTICK_ID]:
            task[td.TICKTICK_ID] = found_task[td.TICKTICK_ID]
            task[td.DUE_DATE] = found_task[td.DUE_DATE]
            self.notion.update_task(task[td.NOTION_ID], task)
        return task

    def delete_task(self, task: dict):
        notion_id = self.notion.get_notion_id(task[td.TICKTICK_ID])
        self.notion.delete_task(notion_id)

    def abandon_task(self, task: dict):
        notion_id = self.notion.get_notion_id(task[td.TICKTICK_ID])
        self.notion.change_task_state(notion_id, active=False)

    def update_task(self, task: dict):
        notion_id = self.notion.get_notion_id(task[td.TICKTICK_ID])
        self.notion.update_task(notion_id, task)

    def add_task(self, task: dict):
        self.notion.create_task(task)

    def sync_expenses(self):
        expenses = [task for task in self.ticktick.raw_tasks
                    if task[ttp.TITLE].startswith("$") and task[ttp.PROJECT_ID] == ttids.PROJECT_IDS["inbox_tasks"]]

        def parse_expense_title(raw_title: str) -> Tuple[float, str]:
            expense_amount = float(raw_title.split(" ")[0].replace("$", ""))
            expense_title = " ".join(raw_title.split(" ")[1:])
            return expense_amount, expense_title.capitalize()

        for expense in expenses:
            amount, title = parse_expense_title(expense[ttp.TITLE])
            date = TaskUtilities.get_task_date(expense, use_created_time=True)

            self.notion.add_expense(title, amount, date)
            self.ticktick.complete_task(expense)
