import logging
import os
from controllers.notion_controller import NotionController
from controllers.ticktick_controller import TicktickController
from utilities.task_utilities import TaskUtilities  # OAuth2 Manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)8s] %(message)s (%(filename)s:%(lineno)s)")
notion = NotionController(os.getenv('NT_auth'), notion_version='2021-08-16', object_id="811f2937421e488793c3441b8ca65509")
ticktick = TicktickController(os.getenv('TT_client_id'),
                              os.getenv('TT_client_secret'),
                              os.getenv('TT_uri'),
                              os.getenv('TT_user'),
                              os.getenv('TT_pass'))

if not TaskUtilities.are_tasks_synced(notion.active_tasks, ticktick.relevant_tasks):
    ticktick.complete_tasks(notion)
    ticktick.delete_tasks(notion)
    ticktick.update_tasks(notion)
    ticktick.add_new_tasks(notion)
