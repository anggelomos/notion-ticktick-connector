import logging
from typing import Set, Optional, Iterable, List

from nothion import NotionClient
from tickthon import Task, TicktickClient


class TaskSyncer:

    def __init__(self, ticktick: TicktickClient, notion: NotionClient):
        self._ticktick = ticktick
        self._notion = notion
        self._ticktick_tasks: Set[Task] = set(self._ticktick.get_active_tasks())
        self._notion_tasks: Set[Task] = set(self._notion.get_active_tasks())

    def sync_tasks(self):
        self._get_unsync_tasks()
        self.sync_ticktick_tasks()
        self.sync_notion_tasks()

    def _get_unsync_tasks(self):
        logging.info("Getting unsync tasks")
        ticktick_base_unsync_tasks = self._ticktick_tasks - self._notion_tasks
        notion_base_unsync_tasks = self._notion_tasks - self._ticktick_tasks

        ticktick_etags = {t.ticktick_etag for t in ticktick_base_unsync_tasks}
        notion_etags_dict = {t.ticktick_etag: t for t in notion_base_unsync_tasks}
        notion_clean_etags = set(notion_etags_dict.keys()) - ticktick_etags

        ticktick_ids = {t.ticktick_id for t in ticktick_base_unsync_tasks}
        notion_ids_dict = {t.ticktick_id: t for t in notion_base_unsync_tasks}
        notion_clean_ids = set(notion_ids_dict.keys()) - ticktick_ids

        self._ticktick_unsync_tasks = ticktick_base_unsync_tasks
        self._notion_unsync_tasks = set([notion_etags_dict[etag] for etag in notion_clean_etags] +
                                        [notion_ids_dict[task_id] for task_id in notion_clean_ids])

    def sync_ticktick_tasks(self):
        logging.info(f"Syncing ticktick tasks: {self._ticktick_unsync_tasks}")
        for task in self._ticktick_unsync_tasks:
            notion_task = self.search_for_task(task, self._notion_tasks)
            if notion_task is None:
                self._notion.create_task(task)
            elif task != notion_task:
                self._notion.update_task(task)
            else:
                logging.warning(f"TICKTICK TASK {task.ticktick_id} WITH ETAG {task.ticktick_etag} "
                                f"WAS NOT SYNCED")

    def sync_notion_tasks(self):
        logging.info("Syncing notion tasks")
        for task in self._notion_unsync_tasks:
            was_task_deleted = self.search_for_task(task, self._ticktick.deleted_tasks)
            was_task_updated = self.search_for_task(task, self._ticktick_unsync_tasks)

            if was_task_deleted:
                self._notion.delete_task(task)
            elif was_task_updated:
                continue
            else:
                self._notion.complete_task(task)

    @staticmethod
    def search_for_task(search_task: Task, tasks: Iterable[Task]) -> Optional[Task]:
        logging.info(f"Searching task with id {search_task.ticktick_id} and etag {search_task.ticktick_etag}")
        for task in tasks:
            if task.ticktick_etag == search_task.ticktick_etag or task.ticktick_id == search_task.ticktick_id:
                return task
        return None

    def sync_expenses(self) -> List[dict]:
        expenses_synced = []
        for expense_task, expense_log in self._ticktick.get_expense_logs():
            expenses_synced.append(self._notion.add_expense_log(expense_log))
            self._ticktick.complete_task(expense_task)
        return expenses_synced
