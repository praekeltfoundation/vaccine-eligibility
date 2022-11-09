import pytest

from vaccine.testing import AppTester
from yal.main import Application


@pytest.fixture
def tester():
    return AppTester(Application)


@pytest.mark.asyncio
async def test_survey_start(tester: AppTester):
    tester.setup_state("state_start_survey")
    await tester.user_input("1")
    tester.assert_state("state_survey_question")

    tester.assert_message(
        "\n".join(
            [
                "*BWise / Survey*",
                "-----",
                "Section 1",
                "1/2",
                "",
                "*How much does everyone in your house make altogether, before paying "
                "for regular monthly items?*",
                "",
                "1. No income",
                "2. R1 - R400",
                "3. R401 - R800",
                "4. R801 - R1 600",
                "5. R1 601 - R3 200",
                "6. R3 201 - R6 400",
                "",
                "-----",
                "*Or reply:*",
                "0. 🏠 Back to Main *MENU*",
                "#. 🆘Get *HELP*",
            ]
        )
    )


@pytest.mark.asyncio
async def test_survey_next_question(tester: AppTester):
    tester.setup_state("state_survey_question")
    await tester.user_input("1")
    tester.assert_state("state_survey_question")
    tester.assert_message(
        "\n".join(
            [
                "*BWise / Survey*",
                "-----",
                "Section 1",
                "2/2",
                "",
                "*What is your present relationship status?*",
                "",
                "1. Not currently dating",
                "2. In a serious relationship",
                "3. In a relationship, but not a serious one",
                "",
                "-----",
                "*Or reply:*",
                "0. 🏠 Back to Main *MENU*",
                "#. 🆘Get *HELP*",
            ]
        )
    )


@pytest.mark.asyncio
async def test_survey_next_section(tester: AppTester):
    tester.user.metadata["segment_section"] = 1
    tester.user.metadata["segment_question"] = "state_relationship_status"

    tester.setup_state("state_survey_question")
    await tester.user_input("1")
    tester.assert_state("state_survey_question")

    tester.assert_message(
        "\n".join(
            [
                "*BWise / Survey*",
                "-----",
                "Section 2",
                "1/2",
                "",
                "*_Do you think this is True or False?_ ",
                "",
                "*People can reduce the risk of getting STIs by using condoms every "
                "time they have sexual intercourse.**",
                "",
                "1. True",
                "2. False",
                "",
                "-----",
                "*Or reply:*",
                "0. 🏠 Back to Main *MENU*",
                "#. 🆘Get *HELP*",
            ]
        )
    )


@pytest.mark.asyncio
async def test_survey_end(tester: AppTester):
    tester.user.metadata["segment_section"] = 3
    tester.user.metadata["segment_question"] = "state_s3_2_loc_2_work"

    tester.setup_state("state_survey_question")
    await tester.user_input("1")
    tester.assert_state("state_survey_done")
