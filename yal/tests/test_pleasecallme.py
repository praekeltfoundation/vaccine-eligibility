from datetime import datetime
from unittest import mock

import pytest

from vaccine.models import Message
from vaccine.testing import AppTester
from yal.main import Application


@pytest.fixture
def tester():
    return AppTester(Application)


@pytest.mark.asyncio
@mock.patch("yal.pleasecallme.get_current_datetime")
async def test_start_out_of_hours(get_current_datetime, tester: AppTester):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_please_call_start")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_state("state_out_of_hours")


@pytest.mark.asyncio
@mock.patch("yal.pleasecallme.get_current_datetime")
async def test_start_in_hours(get_current_datetime, tester: AppTester):
    get_current_datetime.return_value = datetime(2022, 6, 20, 17, 30)
    tester.setup_state("state_please_call_start")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    [greeting_msg] = tester.fake_worker.outbound_messages
    assert greeting_msg.content == "\n".join(
        [
            "👩🏾 *Say no more—I'm on it!*",
            "☝🏾 Hold tight just a sec...",
        ]
    )

    tester.assert_state("state_in_hours")


@pytest.mark.asyncio
async def test_state_out_of_hours(tester: AppTester):
    tester.setup_state("state_out_of_hours")
    await tester.user_input("1")
    tester.assert_state("state_open_hours")


@pytest.mark.asyncio
async def test_state_in_hours(tester: AppTester):
    tester.setup_state("state_in_hours")
    await tester.user_input("1")
    tester.assert_state("state_callback_confirmation")


@pytest.mark.asyncio
async def test_state_callback_confirmation(tester: AppTester):
    tester.setup_state("state_callback_confirmation")
    tester.user.metadata["callback_wait"] = "5 - 7min"
    await tester.user_input("1")
    tester.assert_state("state_start")


@pytest.mark.asyncio
async def test_state_in_hours_specify(tester: AppTester):
    tester.setup_state("state_in_hours")
    await tester.user_input("2")
    tester.assert_state("state_specify_msisdn")


@pytest.mark.asyncio
async def test_state_specify_msisdn_invalid(tester: AppTester):
    tester.setup_state("state_specify_msisdn")
    await tester.user_input("invalid")
    tester.assert_state("state_specify_msisdn")


@pytest.mark.asyncio
async def test_state_specify_msisdn(tester: AppTester):
    tester.setup_state("state_specify_msisdn")
    await tester.user_input("0831231234")
    tester.assert_state("state_confirm_specified_msisdn")


@pytest.mark.asyncio
async def test_state_confirm_specified_msisdn_incorrect(tester: AppTester):
    tester.setup_state("state_confirm_specified_msisdn")
    tester.setup_answer("state_specify_msisdn", "0831231234")
    await tester.user_input("2")
    tester.assert_state("state_specify_msisdn")


@pytest.mark.asyncio
async def test_state_confirm_specified_msisdn(tester: AppTester):
    tester.setup_state("state_confirm_specified_msisdn")
    tester.setup_answer("state_specify_msisdn", "0831231234")
    await tester.user_input("1")
    tester.assert_state("state_ask_to_save_emergency_number")


@pytest.mark.asyncio
async def test_state_ask_to_save_emergency_number(tester: AppTester):
    tester.setup_state("state_ask_to_save_emergency_number")
    await tester.user_input("2")
    tester.assert_state("state_callback_confirmation")