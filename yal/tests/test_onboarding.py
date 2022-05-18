import pytest

from vaccine.testing import AppTester
from yal.main import Application


@pytest.fixture
def tester():
    return AppTester(Application)


@pytest.mark.asyncio
async def test_dob_month_valid(tester: AppTester):
    tester.setup_state("state_dob_month")
    await tester.user_input("2")

    tester.assert_state("state_dob_day")
    tester.assert_num_messages(1)

    tester.assert_answer("state_dob_month", "2")


@pytest.mark.asyncio
async def test_dob_month_skip(tester: AppTester):
    tester.setup_state("state_dob_month")
    await tester.user_input("skip")

    tester.assert_state("state_dob_day")
    tester.assert_num_messages(1)

    tester.assert_answer("state_dob_month", "skip")
