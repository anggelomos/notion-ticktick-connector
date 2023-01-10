import logging
import os
from controllers.notion_controller import NotionController
from controllers.ticktick_controller import TicktickController
from utilities.task_utilities import TaskUtilities  # OAuth2 Manager


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)8s] %(message)s (%(filename)s:%(lineno)s)")
    notion = NotionController(os.getenv('NT_auth'), notion_version='2021-08-16')
    ticktick = TicktickController(os.getenv('TT_user'), os.getenv('TT_pass'))

    notion.get_active_tasks()
    ticktick.sync_tasks()

    habits = ticktick.get_habits()
    notion.check_habits(habits)
    if not TaskUtilities().are_tasks_synced(notion.active_tasks, ticktick.relevant_tasks):
        ticktick.complete_tasks(notion)
        ticktick.delete_tasks(notion)
        ticktick.update_tasks(notion)
        ticktick.add_new_tasks(notion)


if __name__ == "__main__":
    main()
