import os
from constants.task_data import TaskData
from constants.task_status import TaskStatus
from controllers.notion_controller import NotionController
from controllers.ticktick_controller import TicktickController
from task_utilities import TaskUtilities  # OAuth2 Manager



ticktick = TicktickController(os.getenv('TT_client_id'), 
                              os.getenv('TT_client_secret'),
                              os.getenv('TT_uri'),
                              os.getenv('TT_user'),
                              os.getenv('TT_pass'))

notion = NotionController(os.getenv('NT_auth'), notion_version='2021-05-13', object_id="811f2937421e488793c3441b8ca65509")

tasks_to_upload = {}
sniffed_tasks = ticktick.sniff_tasks()

if sniffed_tasks != ticktick.active_tasks:

    list_tasks_status = []
    list_tasks_status += list(map(ticktick.get_existing_task_status, ticktick.active_tasks.items()))
    list_tasks_status += list(map(ticktick.get_new_task_status, sniffed_tasks.items()))
    list_tasks_status = filter(lambda task: task[1] != TaskStatus.NO_CHANGE, list_tasks_status)

    for task, task_status in list_tasks_status:
        if task_status == TaskStatus.NEW:
            page_id = notion.create_task(task)
            ticktick.active_tasks[task[0]] = task[1]
            ticktick.notion_ids[task[0]] = page_id

        elif task_status == TaskStatus.UPDATED:
            notion.update_task(ticktick.notion_ids[task[0]], task)
            ticktick.active_tasks[task[0]] = task[1]

        elif task_status == TaskStatus.COMPLETED:
            task[1][TaskData.DONE.value] = True
            notion.update_task(ticktick.notion_ids[task[0]], task)
            del ticktick.active_tasks[task[0]]
            del ticktick.notion_ids[task[0]]

        elif task_status == TaskStatus.DELETED:
            notion.delete_task(ticktick.notion_ids[task[0]], task)
            del ticktick.notion_ids[task[0]]
            del ticktick.active_tasks[task[0]]

    TaskUtilities.save_active_tasks(ticktick.active_tasks)
    TaskUtilities.save_notion_ids(ticktick.notion_ids)
