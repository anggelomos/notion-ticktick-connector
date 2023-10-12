import os

import pytest
from nothion import NotionClient
from tickthon import TicktickClient


@pytest.fixture(scope="module")
def notion_client():
    return NotionClient(os.getenv("NT_auth"))


@pytest.fixture(scope="module")
def ticktick_client():
    return TicktickClient(os.getenv("TT_user"), os.getenv("TT_pass"))
