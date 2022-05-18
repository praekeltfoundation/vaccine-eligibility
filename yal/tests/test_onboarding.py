import pytest

from vaccine.testing import AppTester
from yal.main import Application


@pytest.fixture
def tester():
    return AppTester(Application)


@pytest.mark.asyncio
async def test_state_dob_month_valid(tester: AppTester):
    tester.setup_state("state_dob_month")
    await tester.user_input("2")

    tester.assert_state("state_dob_day")
    tester.assert_num_messages(1)

    tester.assert_answer("state_dob_month", "2")


@pytest.mark.asyncio
async def test_state_dob_month_invalid(tester: AppTester):
    tester.setup_state("state_dob_month")
    await tester.user_input("22")

    tester.assert_state("state_dob_month")
    tester.assert_num_messages(1)

    tester.assert_no_answer("state_dob_month")


@pytest.mark.asyncio
async def test_state_dob_month_skip(tester: AppTester):
    tester.setup_state("state_dob_month")
    await tester.user_input("skip")

    tester.assert_state("state_dob_day")
    tester.assert_num_messages(1)

    tester.assert_answer("state_dob_month", "skip")


@pytest.mark.asyncio
async def test_state_dob_day_valid(tester: AppTester):
    tester.setup_state("state_dob_day")
    await tester.user_input("2")

    tester.assert_state("state_dob_year")
    tester.assert_num_messages(1)

    tester.assert_answer("state_dob_day", "2")


@pytest.mark.asyncio
async def test_state_dob_day_invalid(tester: AppTester):
    tester.setup_state("state_dob_day")
    await tester.user_input("200")

    tester.assert_state("state_dob_day")
    tester.assert_num_messages(1)

    tester.assert_no_answer("state_dob_day")


@pytest.mark.asyncio
async def test_state_dob_day_skip(tester: AppTester):
    tester.setup_state("state_dob_day")
    await tester.user_input("skip")

    tester.assert_state("state_dob_year")
    tester.assert_num_messages(1)

    tester.assert_answer("state_dob_day", "skip")
