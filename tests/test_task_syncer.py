# TODO: Update the tests.
from datetime import datetime
from random import random

import pytest
from dateutil.tz import tz
from nothion._notion_payloads import NotionPayloads
from tickthon import Task, ExpenseLog

from task_syncer import TaskSyncer

timezone = "America/Bogota"
STATIC_NON_SYNCED_TASK = Task(title="Test task", due_date="2099-09-09", ticktick_id="test-id",
                              ticktick_etag="test-etag", created_date="2099-09-09", focus_time=9.99,
                              tags=("test", "integration", "notion", "notes"), project_id="inbox114478622",
                              timezone=timezone)
TEST_TICKTICK_TASKS = [STATIC_NON_SYNCED_TASK,
                       # Task to update
                       Task(title="Test Existing Task", due_date="9999-09-09", ticktick_id="a7f9b3d2c8e60f1472065ac4",
                            ticktick_etag="muu17zqq", created_date="9999-09-09", focus_time=random(),
                            tags=("test", "existing", "notes"), project_id="4a72b6d8e9f2103c5d6e7f8a9b0c",
                            timezone=timezone, status=2),
                       # Test task to create
                       Task(title="Test Create Task", due_date="2099-09-09", ticktick_id="kj39rudnsakl49fht83ksio5",
                            ticktick_etag="w8dhr428", created_date="2099-09-09", focus_time=9.99,
                            tags=("test", "created", "notion", "notes"), project_id="jr83utdnsakl49fh8h28dfht",
                            timezone=timezone)
                       ]
TEST_NOTION_TASKS = [STATIC_NON_SYNCED_TASK,
                     # Task to update
                     Task(title="Test Existing Task", due_date="9999-09-09", ticktick_id="a7f9b3d2c8e60f1472065ac4",
                          ticktick_etag="muu17zqq", created_date="9999-09-09", focus_time=9.99,
                          tags=("test", "existing", "notes"), project_id="4a72b6d8e9f2103c5d6e7f8a9b0c",
                          timezone=timezone),
                     # Task to complete
                     Task(title="Test Complete Task", due_date="9999-09-09", ticktick_id="b2c3d4e5f6a7b8c9d0e1f2a3",
                          ticktick_etag="5hu47d83", created_date="9999-09-09", focus_time=0,
                          tags=("test", "complete", "notes"), project_id="c3d4e5f6a7b8c9d0e1f2a3b4", timezone=timezone),
                     # Task to delete
                     Task(title="Test Delete Task", due_date="9999-09-09", ticktick_id="d4e5f6a7b8c9d0e1f2a3b4c5",
                          ticktick_etag="8ru3n28d", created_date="9999-09-09", focus_time=0,
                          tags=("test", "delete", "notes"), project_id="e5f6a7b8c9d0e1f2a3b4c5d6",
                          timezone=timezone, deleted=1)
                     ]


@pytest.fixture()
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

    created_task_search = Task(ticktick_etag="w8dhr428", created_date="", title="", ticktick_id="", tags=tuple("notes"))
    updated_task_search = Task(ticktick_etag="muu17zqq", created_date="", title="", ticktick_id="", tags=tuple("notes"))

    created_task = task_syncer._notion.get_notion_task(created_task_search)
    updated_task = task_syncer._notion.get_notion_task(updated_task_search)

    assert created_task == TEST_TICKTICK_TASKS[2]
    assert updated_task == TEST_TICKTICK_TASKS[1]

    task_syncer._notion.delete_task(created_task)
    task_syncer._notion.delete_task_note(created_task)


def test_sync_notion_tasks(task_syncer):
    task_syncer.deleted_ticktick_tasks.append(TEST_NOTION_TASKS[3])
    task_syncer._notion.create_task(TEST_NOTION_TASKS[3])
    task_syncer._notion.create_task(TEST_NOTION_TASKS[2])

    task_syncer.sync_notion_tasks()

    completed_task_search = Task(ticktick_etag="5hu47d83", created_date="", title="", ticktick_id="")
    completed_task = task_syncer._notion.get_notion_task(completed_task_search)
    assert completed_task.status == 2
    assert task_syncer._notion.is_task_already_created(TEST_NOTION_TASKS[3]) is False

    task_syncer._notion.delete_task(completed_task)


def test_sync_expenses(task_syncer):
    task_syncer._ticktick.expense_logs.append((Task(title="$9.9 Test product", due_date="9999-09-09",
                                                    ticktick_id="a7b8c9d0e1f2a3b4c5d6e7f8", created_date="9999-09-09",
                                                    ticktick_etag="a9b0c1d2"),
                                               ExpenseLog(date="9999-09-09", expense=9.9,
                                                          product="Test product integration tests notion-ticktick")))

    expenses_synced = task_syncer.sync_expenses()

    test_expense = next((expense for expense in expenses_synced if
                         expense['properties']['product']['title'][0]['plain_text'] ==
                         "Test product integration tests notion-ticktick"), None)

    task_syncer._notion.notion_api.get_table_entry(test_expense["id"])
    task_syncer._notion.notion_api.update_table_entry(test_expense["id"], NotionPayloads.delete_table_entry())


def test_sync_highlights(task_syncer):
    task_syncer._ticktick.all_day_logs.append((Task(title="Tested highlight syncer", due_date="9999-09-09",
                                                    ticktick_id="726db85349f01aec349fdb83",
                                                    created_date=datetime.now(tz.gettz("America/New_York")).isoformat(),
                                                    ticktick_etag="3c02ab1d", tags=("highlight",),
                                                    timezone="America/New_York")))

    highlights_synced = task_syncer.sync_highlights()

    test_expense = [highlight for highlight in highlights_synced if
                    highlight['properties']['Note']['title'][0]['plain_text'] == "Tested highlight syncer"]

    assert len(test_expense) == 1
    task_syncer._notion.notion_api.get_table_entry(test_expense[0]["id"])
    task_syncer._notion.notion_api.update_table_entry(test_expense[0]["id"], NotionPayloads.delete_table_entry())
