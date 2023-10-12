from random import random

import pytest
from nothion._notion_payloads import NotionPayloads
from tickthon import Task, ExpenseLog

from task_syncer import TaskSyncer

timezone = "America/Bogota"
STATIC_NON_SYNCED_TASK = Task(title="Test task", due_date="2099-09-09", ticktick_id="test-id",
                              ticktick_etag="test-etag", focus_time=9.99, tags=("test", "integration", "notion"),
                              project_id="inbox114478622", timezone=timezone)
TEST_TICKTICK_TASKS = [STATIC_NON_SYNCED_TASK,
                       # Task to update
                       Task(title="Test Existing Task", due_date="9999-09-09", ticktick_id="a7f9b3d2c8e60f1472065ac4",
                            ticktick_etag="muu17zqq", focus_time=random(), tags=("test", "existing"),
                            project_id="4a72b6d8e9f2103c5d6e7f8a9b0c", timezone=timezone, status=2),
                       # Test task to create
                       Task(title="Test Create Task", due_date="2099-09-09", ticktick_id="kj39rudnsakl49fht83ksio5",
                            ticktick_etag="w8dhr428", focus_time=9.99, tags=("test", "created", "notion"),
                            project_id="jr83utdnsakl49fh8h28dfht", timezone=timezone)
                       ]
TEST_NOTION_TASKS = [STATIC_NON_SYNCED_TASK,
                     # Task to update
                     Task(title="Test Existing Task", due_date="9999-09-09", ticktick_id="a7f9b3d2c8e60f1472065ac4",
                          ticktick_etag="muu17zqq", focus_time=9.99, tags=("test", "existing"),
                          project_id="4a72b6d8e9f2103c5d6e7f8a9b0c", timezone=timezone),
                     # Task to complete
                     Task(title="Test Complete Task", due_date="9999-09-09", ticktick_id="b2c3d4e5f6a7b8c9d0e1f2a3",
                          ticktick_etag="5hu47d83", focus_time=0, tags=("test", "complete"),
                          project_id="c3d4e5f6a7b8c9d0e1f2a3b4", timezone=timezone),
                     # Task to delete
                     Task(title="Test Delete Task", due_date="9999-09-09", ticktick_id="d4e5f6a7b8c9d0e1f2a3b4c5",
                          ticktick_etag="8ru3n28d", focus_time=0, tags=("test", "delete"),
                          project_id="e5f6a7b8c9d0e1f2a3b4c5d6", timezone=timezone, deleted=1)
                     ]


@pytest.fixture(scope="module")
def task_syncer(ticktick_client, notion_client):
    task_syncer = TaskSyncer(ticktick_client, notion_client)
    task_syncer._ticktick_tasks = set(TEST_TICKTICK_TASKS)
    task_syncer._notion_tasks = set(TEST_NOTION_TASKS)
    task_syncer._get_unsync_tasks()
    return task_syncer


def test_get_unsync_tasks(task_syncer):
    expected_ticktick_unsync_tasks = set(TEST_TICKTICK_TASKS[1:])
    expected_notion_unsync_tasks = set(TEST_NOTION_TASKS[2:])

    assert task_syncer._ticktick_unsync_tasks == expected_ticktick_unsync_tasks
    assert task_syncer._notion_unsync_tasks == expected_notion_unsync_tasks


def test_sync_ticktick_tasks(task_syncer):
    task_syncer.sync_ticktick_tasks()

    created_task = task_syncer._notion.get_task_by_etag("w8dhr428")
    updated_task = task_syncer._notion.get_task_by_etag("muu17zqq")

    assert created_task == TEST_TICKTICK_TASKS[2]
    assert updated_task == TEST_TICKTICK_TASKS[1]

    task_syncer._notion.delete_task(created_task)


def test_sync_notion_tasks(task_syncer):
    task_syncer._ticktick.deleted_tasks.append(TEST_NOTION_TASKS[3])
    task_syncer._notion.create_task(TEST_NOTION_TASKS[3])
    task_syncer._notion.create_task(TEST_NOTION_TASKS[2])

    task_syncer.sync_notion_tasks()

    completed_task = task_syncer._notion.get_task_by_etag("5hu47d83")
    assert completed_task.status == 2
    assert task_syncer._notion.is_task_already_created(TEST_NOTION_TASKS[3]) is False

    task_syncer._notion.delete_task(completed_task)


def test_sync_expenses(task_syncer):
    task_syncer._ticktick.expense_logs.append((Task(title="$9.9 Test product", due_date="9999-09-09",
                                                    ticktick_id="a7b8c9d0e1f2a3b4c5d6e7f8", ticktick_etag="a9b0c1d2"),
                                              ExpenseLog(date="9999-09-09", expense=9.9,
                                                         product="Test product integration tests notion-ticktick")))

    expenses_synced = task_syncer.sync_expenses()

    test_expense = next((expense for expense in expenses_synced if
                         expense['properties']['product']['title'][0]['plain_text'] ==
                         "Test product integration tests notion-ticktick"), None)

    task_syncer._notion.notion_api.get_table_entry(test_expense["id"])
    task_syncer._notion.notion_api.update_table_entry(test_expense["id"], NotionPayloads.delete_table_entry())
