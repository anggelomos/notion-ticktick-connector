import logging
import os
from dotenv import load_dotenv
from src.task_syncer import TaskSyncer

from tickthon import TicktickClient
from nothion import NotionClient

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)8s] %(message)s (%(filename)s:%(lineno)s)")


def main():
    ticktick = TicktickClient(os.getenv("TT_USER"), os.getenv("TT_PASS"))
    notion = NotionClient(os.getenv("NT_AUTH"), os.getenv("NT_TASKS_DB_ID"))

    task_syncer = TaskSyncer(ticktick, notion)
    task_syncer.sync_expenses()
    task_syncer.sync_highlights()
    task_syncer.sync_tasks()
    task_syncer.add_work_task_tag()


if __name__ == "__main__":
    main()
