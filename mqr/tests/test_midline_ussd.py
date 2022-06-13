import json

import pytest
from sanic import Sanic, response

from mqr import config
from mqr.baseline_ussd import Application
from mqr.midline_ussd import Application
from vaccine.models import Message, StateData, User
from vaccine.testing import AppTester


@pytest.fixture
def tester():
    return AppTester(Application)


@pytest.mark.asyncio
async def test_state_eat_fruits(tester: AppTester):
    tester.setup_state("state_eat_fruits")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_state("state_eat_fruits")

    [reply] = tester.application.messages
    assert len(reply.content) < 160
    assert reply.content == "\n".join([
        "1/16",
        "",
        "Do you eat fruits at least once a day?",
        "1. Yes",
        "2. No",
        "3. Skip",
    ])

@pytest.mark.asyncio
async def test_state_eat_fruits_valid(tester: AppTester):
    tester.setup_state("state_eat_fruits")
    await tester.user_input("1")
    tester.assert_state("state_eat_vegetables")

    tester.assert_answer("state_eat_fruits", "yes")

@pytest.mark.asyncio
async def test_state_eat_fruits_invalid(tester: AppTester):
    tester.setup_state("state_eat_fruits")
    await tester.user_input("invalid")
    tester.assert_state("state_eat_fruits")

    [reply] = tester.application.messages
    assert len(reply.content) < 160
    assert reply.content == "\n".join([
        "Please use numbers from list.",
        "",
        "Do you eat fruits at least once a day?",
        "1. Yes",
        "2. No",
        "3. Skip",
    ])
