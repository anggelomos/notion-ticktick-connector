import logging
import os
from controllers.notion_controller import NotionController
from controllers.task_syncer import TaskSyncer
from controllers.ticktick_controller import TicktickController


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)8s] %(message)s (%(filename)s:%(lineno)s)")
    notion = NotionController(os.getenv('NT_auth'), notion_version='2022-06-28')
    ticktick = TicktickController(os.getenv('TT_user'), os.getenv('TT_pass'))

    notion.get_active_tasks()
    ticktick.get_tasks()

    habits = ticktick.get_habits()
    notion.check_habits(habits)

    task_syncer = TaskSyncer(notion, ticktick)
    task_syncer.sync_expenses()
    task_syncer.get_unsynced_tasks(notion.active_tasks, ticktick.relevant_tasks)
    task_syncer.sync_ticktick_tasks()
    task_syncer.sync_notion_tasks()


if __name__ == "__main__":
    main()
