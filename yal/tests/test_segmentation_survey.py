import pytest

from vaccine.models import Message
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
                "1/3",
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
                "7. R6 401 - R12 800",
                "8. R12 801 - R25 600",
                "9. R25 601 - R51 200",
                "10. R51 201 - R102 400",
                "11. R102 401 - R204 800",
                "12. R204 801 or more",
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
                "2/3",
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
async def test_survey_freetext_question(tester: AppTester):
    tester.user.metadata["segment_section"] = 1
    tester.user.metadata["segment_question"] = "state_s1_6_detail_monthly_sex_partners"

    tester.setup_state("state_survey_question")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_message(
        "\n".join(
            [
                "*BWise / Survey*",
                "-----",
                "Section 1",
                "1/3",
                "",
                "**Ok. You can tell me how many sexual partners you had here.*",
                "",
                "_Just type and send_*",
                "",
                "-----",
                "*Or reply:*",
                "0. 🏠 Back to Main *MENU*",
                "#. 🆘Get *HELP*",
            ]
        )
    )

    await tester.user_input("11")

    tester.assert_state("state_survey_question")

    tester.assert_answer("state_s1_6_detail_monthly_sex_partners", "11")


@pytest.mark.asyncio
async def test_survey_next_section(tester: AppTester):
    tester.user.metadata["segment_section"] = 2
    tester.user.metadata["segment_question"] = "state_s2_2_knowledge_2"

    tester.setup_state("state_survey_question")
    await tester.user_input("1")
    tester.assert_state("state_survey_question")

    tester.assert_message(
        "\n".join(
            [
                "*BWise / Survey*",
                "-----",
                "Section 3",
                "1/2",
                "",
                "*_The following statements may apply more or less to you. To what "
                "extent do you think each statement applies to you personally?_ ",
                "",
                "*I’m my own boss.**",
                "",
                "1. Does not apply at all",
                "2. Applies somewhat",
                "3. Applies",
                "4. Applies a lot",
                "5. Applies completely",
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
