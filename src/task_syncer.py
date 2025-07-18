import logging
from typing import Optional, Iterable

from nothion import NotionClient
from tickthon import Task, TaskType, TicktickClient


class TaskSyncer:

    def __init__(self, ticktick: TicktickClient, notion: NotionClient):
        self._ticktick = ticktick
        self._notion = notion
        self._ticktick_tasks: list[Task] = self._ticktick.get_active_tasks()
        self._notion_tasks: list[Task] = self._notion.tasks.get_active_tasks()
        self._completed_ticktick_tasks = self._ticktick.get_completed_tasks()

    def sync_tasks(self):
        ticktick_tasks = self._get_ticktick_tasks()
        self._sync_ticktick_tasks(ticktick_tasks)

    def _get_ticktick_tasks(self) -> list[Task]:
        """Get all tasks from ticktick in the active lists"""
        ticktick_lists = self._ticktick.ticktick_list_ids
        active_lists = [ticktick_lists.TODAY_BACKLOG, ticktick_lists.WEEK_BACKLOG, ticktick_lists.MONTH_BACKLOG]
        active_tasks = self._ticktick.get_tasks_by_list(active_lists, TaskType.ALL)

        return active_tasks

    def _sync_ticktick_tasks(self, ticktick_tasks: list[Task]):
        """Sync ticktick tasks to notion.

        Args:
            ticktick_tasks: list[Task] - List of ticktick tasks to sync to notion.
        """
        logging.info(f"Syncing ticktick tasks: {ticktick_tasks}")
        for task in ticktick_tasks:
            notion_task = self._search_for_task(task, self._notion_tasks)
            if notion_task and not self._is_task_synced(task, notion_task):
                self._notion.tasks.update_task(task)
            else:
                logging.warning(f"TICKTICK TASK {task.title} WAS NOT SYNCED")

    def _is_task_synced(self, ticktick_task: Task, notion_task: Task) -> bool:
        """Check if a task is synced.

        Args:
            ticktick_task: Task - Ticktick task to check.
            notion_task: Task - Notion task to check.

        Returns:
            bool: True if all sync fields match between tasks, False otherwise.
        """
        return (ticktick_task.project_id == notion_task.project_id and
                ticktick_task.column_id == notion_task.column_id and
                ticktick_task.focus_time == notion_task.focus_time)

    def sync_notion_tasks(self):
        logging.info("Syncing notion tasks")
        for task in self._notion_unsync_tasks:
            was_task_deleted = self._search_for_task(task, self.deleted_ticktick_tasks)
            was_task_updated = self._search_for_task(task, self._ticktick_unsync_tasks)

            if was_task_deleted:
                self.delete_notion_tasks(task)
            elif was_task_updated:
                continue
            else:
                self.complete_notion_tasks(task)

    @staticmethod
    def _search_for_task(search_task: Task, tasks: Iterable[Task]) -> Optional[Task]:
        logging.info(f"Searching task: {search_task.title}")
        for task in tasks:
            if task.title == search_task.title:
                return task
        return None
