import logging
import os
from src.task_syncer import TaskSyncer

from tickthon import TicktickClient
from nothion import NotionClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)8s] %(message)s (%(filename)s:%(lineno)s)")


def main():
    ticktick = TicktickClient(os.getenv("TT_user"), os.getenv("TT_pass"))
    notion = NotionClient(os.getenv("NT_auth"))

    task_syncer = TaskSyncer(ticktick, notion)
    task_syncer.sync_expenses()
    task_syncer.sync_highlights()
    task_syncer.sync_tasks()
    task_syncer.add_work_task_tag()


if __name__ == "__main__":
    main()
