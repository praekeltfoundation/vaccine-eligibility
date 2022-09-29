import json

import pytest
from sanic import Sanic, response

from mqr import config
from mqr.midline_ussd import Application
from vaccine.models import Message
from vaccine.testing import AppTester, TState, run_sanic


@pytest.fixture
def tester():
    return AppTester(Application)


@pytest.fixture
async def rapidpro_mock():
    Sanic.test_mode = True
    app = Sanic("mock_rapidpro")
    tstate = TState()

    @app.route("/api/v2/flow_starts.json", methods=["POST"])
    def start_flow(request):
        tstate.requests.append(request)
        return response.json({}, status=200)

    async with run_sanic(app) as server:
        url = config.RAPIDPRO_URL
        config.RAPIDPRO_URL = f"http://{server.host}:{server.port}"
        config.RAPIDPRO_TOKEN = "testtoken"
        server.tstate = tstate
        yield server
        config.RAPIDPRO_URL = url


@pytest.mark.asyncio
async def test_state_eat_fruits(tester: AppTester):
    tester.setup_state("state_eat_fruits")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_state("state_eat_fruits")
    tester.assert_message(
        "\n".join(
            [
                "1/16",
                "",
                "Do you eat fruits at least once a day?",
                "1. Yes",
                "2. No",
                "3. Skip",
            ]
        ),
        max_length=160,
    )


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

    tester.assert_message(
        "\n".join(
            [
                "Please use numbers from list.",
                "",
                "1. Yes",
                "2. No",
                "3. Skip",
            ]
        ),
        max_length=160,
    )


@pytest.mark.asyncio
async def test_state_eat_vegetables(tester: AppTester):
    tester.setup_state("state_eat_vegetables")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_state("state_eat_vegetables")

    tester.assert_message(
        "\n".join(
            [
                "2/16",
                "",
                "Do you eat vegetables at least once a day?",
                "1. Yes",
                "2. No",
                "3. Skip",
            ]
        ),
        max_length=160,
    )


@pytest.mark.asyncio
async def test_state_eat_vegetables_valid(tester: AppTester):
    tester.setup_state("state_eat_vegetables")
    await tester.user_input("1")
    tester.assert_state("state_eat_liver")

    tester.assert_answer("state_eat_vegetables", "yes")


@pytest.mark.asyncio
async def test_state_eat_vegetables_invalid(tester: AppTester):
    tester.setup_state("state_eat_vegetables")
    await tester.user_input("invalid")
    tester.assert_state("state_eat_vegetables")

    tester.assert_message(
        "\n".join(
            [
                "Please use numbers from list.",
                "",
                "1. Yes",
                "2. No",
                "3. Skip",
            ]
        ),
        max_length=160,
    )


@pytest.mark.asyncio
async def test_state_eat_liver(tester: AppTester):
    tester.setup_state("state_eat_liver")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_state("state_eat_liver")

    tester.assert_message(
        "\n".join(
            [
                "3/16",
                "",
                "How often do you eat liver?",
                "1. Once a week",
                "2. Once every 2 weeks",
                "3. Once a month",
                "4. Less frequently than once a month",
                "5. Not at all",
                "6. Skip",
            ]
        ),
        max_length=160,
    )


@pytest.mark.asyncio
async def test_state_eat_liver_valid(tester: AppTester):
    tester.setup_state("state_eat_liver")
    await tester.user_input("1")
    tester.assert_state("state_foods_contain")

    tester.assert_answer("state_eat_liver", "once_week")


@pytest.mark.asyncio
async def test_state_eat_liver_invalid(tester: AppTester):
    tester.setup_state("state_eat_liver")
    await tester.user_input("invalid")
    tester.assert_state("state_eat_liver")

    tester.assert_message(
        "\n".join(
            [
                "Please use numbers from list.",
                "",
                "1. Once a week",
                "2. Once every 2 weeks",
                "3. Once a month",
                "4. Less frequently than once a month",
                "5. Not at all",
                "6. Skip",
            ]
        ),
        max_length=160,
    )


@pytest.mark.asyncio
async def test_state_foods_contain(tester: AppTester):
    tester.setup_state("state_foods_contain")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_state("state_foods_contain")

    tester.assert_message(
        "\n".join(
            [
                "4/16",
                "",
                "Nuts, eggs, meat, fish, and green vegetables have a lot of what in "
                "them?",
                "1. Calcium",
                "2. Vitamin C",
                "3. Iron",
                "4. Fibre",
                "5. Skip",
            ]
        ),
        max_length=160,
    )


@pytest.mark.asyncio
async def test_state_foods_contain_valid(tester: AppTester):
    tester.setup_state("state_foods_contain")
    await tester.user_input("1")
    tester.assert_state("state_amount_alcohol_since_pregnant")

    tester.assert_answer("state_foods_contain", "calcium")


@pytest.mark.asyncio
async def test_state_foods_contain_invalid(tester: AppTester):
    tester.setup_state("state_foods_contain")
    await tester.user_input("invalid")
    tester.assert_state("state_foods_contain")

    tester.assert_message(
        "\n".join(
            [
                "Please use numbers from list.",
                "",
                "1. Calcium",
                "2. Vitamin C",
                "3. Iron",
                "4. Fibre",
                "5. Skip",
            ]
        ),
        max_length=160,
    )


@pytest.mark.asyncio
async def test_amount_alcohol_since_pregnant(tester: AppTester):
    tester.setup_state("state_amount_alcohol_since_pregnant")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_state("state_amount_alcohol_since_pregnant")

    tester.assert_message(
        "\n".join(
            [
                "Since becoming pregnant, has the number of alcoholic drinks you have "
                "per week:",
                "1. Stayed the same",
                "2. Reduced",
                "3. Increased",
                "4. Stopped",
                "5. I never drink",
                "6. Skip",
            ]
        ),
        max_length=160,
    )


@pytest.mark.asyncio
async def test_amount_alcohol_since_pregnant_valid(tester: AppTester):
    tester.setup_state("state_amount_alcohol_since_pregnant")
    await tester.user_input("1")
    tester.assert_state("state_swollen_feet_symptom_of")

    tester.assert_answer("state_amount_alcohol_since_pregnant", "no_change")


@pytest.mark.asyncio
async def test_state_amount_alcohol_since_pregnant_invalid(tester: AppTester):
    tester.setup_state("state_amount_alcohol_since_pregnant")
    await tester.user_input("invalid")
    tester.assert_state("state_amount_alcohol_since_pregnant")

    tester.assert_message(
        "\n".join(
            [
                "Please use numbers from list.",
                "",
                "1. Stayed the same",
                "2. Reduced",
                "3. Increased",
                "4. Stopped",
                "5. I never drink",
                "6. Skip",
            ]
        ),
        max_length=160,
    )


@pytest.mark.asyncio
async def test_state_swollen_feet_symptom_of(tester: AppTester):
    tester.setup_state("state_swollen_feet_symptom_of")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_state("state_swollen_feet_symptom_of")

    tester.assert_message(
        "\n".join(
            [
                "6/16",
                "",
                "What can severe swollen feet even after a night's sleep be a symptom "
                "of?",
                "1. Urinary tract infection",
                "2. Pre-eclampsia",
                "3. Anemia",
                "4. Skip",
            ]
        ),
        max_length=160,
    )


@pytest.mark.asyncio
async def test_state_swollen_feet_symptom_of_valid(tester: AppTester):
    tester.setup_state("state_swollen_feet_symptom_of")
    await tester.user_input("1")
    tester.assert_state("state_dizzy_weak_symptom_of")

    tester.assert_answer("state_swollen_feet_symptom_of", "urinary_tract_infection")


@pytest.mark.asyncio
async def test_state_swollen_feet_symptom_of_invalid(tester: AppTester):
    tester.setup_state("state_swollen_feet_symptom_of")
    await tester.user_input("invalid")
    tester.assert_state("state_swollen_feet_symptom_of")

    tester.assert_message(
        "\n".join(
            [
                "Please use numbers from list.",
                "",
                "1. Urinary tract infection",
                "2. Pre-eclampsia",
                "3. Anemia",
                "4. Skip",
            ]
        ),
        max_length=160,
    )


@pytest.mark.asyncio
async def test_state_dizzy_weak_symptom_of(tester: AppTester):
    tester.setup_state("state_dizzy_weak_symptom_of")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_state("state_dizzy_weak_symptom_of")

    tester.assert_message(
        "\n".join(
            [
                "7/16",
                "",
                "What could a mix of feeling dizzy and weak/tired be a symptom of?",
                "1. Urinary tract infection",
                "2. Pre-eclampsia",
                "3. Anemia",
                "4. Skip",
            ]
        ),
        max_length=160,
    )


@pytest.mark.asyncio
async def test_state_dizzy_weak_symptom_of_valid(tester: AppTester):
    tester.setup_state("state_dizzy_weak_symptom_of")
    await tester.user_input("1")
    tester.assert_state("state_baby_kicks_felt")

    tester.assert_answer("state_dizzy_weak_symptom_of", "urinary_tract_infection")


@pytest.mark.asyncio
async def test_state_dizzy_weak_symptom_of_invalid(tester: AppTester):
    tester.setup_state("state_dizzy_weak_symptom_of")
    await tester.user_input("invalid")
    tester.assert_state("state_dizzy_weak_symptom_of")

    tester.assert_message(
        "\n".join(
            [
                "Please use numbers from list.",
                "",
                "1. Urinary tract infection",
                "2. Pre-eclampsia",
                "3. Anemia",
                "4. Skip",
            ]
        ),
        max_length=160,
    )


@pytest.mark.asyncio
async def test_baby_kicks_felt(tester: AppTester):
    tester.setup_state("state_baby_kicks_felt")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_state("state_baby_kicks_felt")

    tester.assert_message(
        "\n".join(
            [
                "8/16",
                "",
                "Do you think baby kicks should be felt every day in the third "
                "trimester"
                " of pregnancy?",
                "1. Yes",
                "2. Maybe",
                "3. No",
                "4. Don't know",
                "5. Skip",
            ]
        ),
        max_length=160,
    )


@pytest.mark.asyncio
async def test_baby_kicks_felt_valid(tester: AppTester):
    tester.setup_state("state_baby_kicks_felt")
    await tester.user_input("1")
    tester.assert_state("state_biggest_danger_sign_pregnancy")

    tester.assert_answer("state_baby_kicks_felt", "yes")


@pytest.mark.asyncio
async def test_baby_kicks_felt_invalid(tester: AppTester):
    tester.setup_state("state_baby_kicks_felt")
    await tester.user_input("invalid")
    tester.assert_state("state_baby_kicks_felt")

    tester.assert_message(
        "\n".join(
            [
                "Please use numbers from list.",
                "",
                "1. Yes",
                "2. Maybe",
                "3. No",
                "4. Don't know",
                "5. Skip",
            ]
        ),
        max_length=160,
    )


@pytest.mark.asyncio
async def test_state_biggest_danger_sign_pregnancy(tester: AppTester):
    tester.setup_state("state_biggest_danger_sign_pregnancy")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_state("state_biggest_danger_sign_pregnancy")

    tester.assert_message(
        "\n".join(
            [
                "9/16",
                "",
                "In your view, what is the biggest pregnancy danger sign on this list?",
                "1. Weight gain of 4-5 kilograms",
                "2. Vaginal bleeding",
                "3. Nose bleeds",
                "4. Skip",
            ]
        ),
        max_length=160,
    )


@pytest.mark.asyncio
async def test_state_biggest_danger_sign_pregnancy_valid(tester: AppTester):
    tester.setup_state("state_biggest_danger_sign_pregnancy")
    await tester.user_input("1")
    tester.assert_state("state_planning_on_breastfeeding")

    tester.assert_answer("state_biggest_danger_sign_pregnancy", "4_5kg_weight_gain")


@pytest.mark.asyncio
async def test_state_biggest_danger_sign_pregnancy_invalid(tester: AppTester):
    tester.setup_state("state_biggest_danger_sign_pregnancy")
    await tester.user_input("invalid")
    tester.assert_state("state_biggest_danger_sign_pregnancy")

    tester.assert_message(
        "\n".join(
            [
                "Please use numbers from list.",
                "",
                "1. Weight gain of 4-5 kilograms",
                "2. Vaginal bleeding",
                "3. Nose bleeds",
                "4. Skip",
            ]
        ),
        max_length=160,
    )


@pytest.mark.asyncio
async def test_state_planning_on_breastfeeding(tester: AppTester):
    tester.setup_state("state_planning_on_breastfeeding")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_state("state_planning_on_breastfeeding")

    tester.assert_message(
        "\n".join(
            [
                "10/16",
                "",
                "Are you planning on breastfeeding your baby after he/she is born?",
                "1. Yes",
                "2. No",
                "3. Skip",
            ]
        ),
        max_length=160,
    )


@pytest.mark.asyncio
async def test_state_planning_on_breastfeeding_valid(tester: AppTester):
    tester.setup_state("state_planning_on_breastfeeding")
    await tester.user_input("1")
    tester.assert_state("state_biggest_reason_to_breastfeed_question")

    tester.assert_answer("state_planning_on_breastfeeding", "yes")


@pytest.mark.asyncio
async def test_state_planning_on_breastfeeding_valid_2(tester: AppTester):
    tester.setup_state("state_planning_on_breastfeeding")
    await tester.user_input("2")
    tester.assert_state("state_why_not_intend_breastfeeding_question")

    tester.assert_answer("state_planning_on_breastfeeding", "no")


@pytest.mark.asyncio
async def test_state_planning_on_breastfeeding_invalid(tester: AppTester):
    tester.setup_state("state_planning_on_breastfeeding")
    await tester.user_input("invalid")
    tester.assert_state("state_planning_on_breastfeeding")

    tester.assert_message(
        "\n".join(
            [
                "Please use numbers from list.",
                "",
                "1. Yes",
                "2. No",
                "3. Skip",
            ]
        ),
        max_length=160,
    )


@pytest.mark.asyncio
async def test_state_why_not_intend_breastfeeding(tester: AppTester):
    tester.setup_state("state_why_not_intend_breastfeeding")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_state("state_why_not_intend_breastfeeding")

    tester.assert_message(
        "\n".join(
            [
                "",
                "1. Breastmilk is not nutritious",
                "2. Low milk supply",
                "3. Sore nipples",
                "4. Takes too long",
                "5. Lack of information",
                "6. Lack of support",
                "7. Other",
                "8. Skip",
            ]
        ),
        max_length=160,
    )


@pytest.mark.asyncio
async def test_state_why_not_intend_breastfeeding_valid(tester: AppTester):
    tester.setup_state("state_why_not_intend_breastfeeding")
    await tester.user_input("1")
    tester.assert_state("state_important_to_vaccinate_question")

    tester.assert_answer("state_why_not_intend_breastfeeding", "not_nutritious")


@pytest.mark.asyncio
async def test_state_why_not_intend_breastfeeding_invalid(tester: AppTester):
    tester.setup_state("state_why_not_intend_breastfeeding")
    await tester.user_input("invalid")
    tester.assert_state("state_why_not_intend_breastfeeding")

    # TODO this is non standard, removed "Please use numbers from list.\n" due
    # to char count
    tester.assert_message(
        "\n".join(
            [
                "",
                "1. Breastmilk is not nutritious",
                "2. Low milk supply",
                "3. Sore nipples",
                "4. Takes too long",
                "5. Lack of information",
                "6. Lack of support",
                "7. Other",
                "8. Skip",
            ]
        ),
        max_length=160,
    )


@pytest.mark.asyncio
async def test_state_biggest_reason_to_breastfeed(tester: AppTester):
    tester.setup_state("state_biggest_reason_to_breastfeed")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_state("state_biggest_reason_to_breastfeed")

    tester.assert_message(
        "\n".join(
            [
                "",
                "1. Breastmilk boosts my baby's immunity",
                "2. Breastmilk is tastier than formula",
                "3. Breastfeeding improves my health",
                "4. I was told to breastfeed",
                "5. Other",
                "6. Skip",
            ]
        ),
        max_length=160,
    )


@pytest.mark.asyncio
async def test_state_biggest_reason_to_breastfeed_valid(tester: AppTester):
    tester.setup_state("state_biggest_reason_to_breastfeed")
    await tester.user_input("1")
    tester.assert_state("state_when_start_breastfeed")

    tester.assert_answer("state_biggest_reason_to_breastfeed", "boosts_baby_immunity")


@pytest.mark.asyncio
async def test_state_biggest_reason_to_breastfeed_invalid(tester: AppTester):
    tester.setup_state("state_biggest_reason_to_breastfeed")
    await tester.user_input("invalid")
    tester.assert_state("state_biggest_reason_to_breastfeed")

    # TODO this is non standard, removed "Please use numbers from list.\n"
    # due to char count
    tester.assert_message(
        "\n".join(
            [
                "",
                "1. Breastmilk boosts my baby's immunity",
                "2. Breastmilk is tastier than formula",
                "3. Breastfeeding improves my health",
                "4. I was told to breastfeed",
                "5. Other",
                "6. Skip",
            ]
        ),
        max_length=160,
    )


@pytest.mark.asyncio
async def test_state_when_start_breastfeed(tester: AppTester):
    tester.setup_state("state_when_start_breastfeed")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_state("state_when_start_breastfeed")

    tester.assert_message(
        "\n".join(
            [
                "12/16",
                "",
                "When do you plan to start breastfeeding your baby?",
                "1. Within 1 hour of birth",
                "2. After 1 hour post-delivery",
                "3. Day 2 & above",
                "4. Undecided",
                "5. Skip",
            ]
        ),
        max_length=160,
    )


@pytest.mark.asyncio
async def test_state_when_start_breastfeed_valid(tester: AppTester):
    tester.setup_state("state_when_start_breastfeed")
    await tester.user_input("1")
    tester.assert_state("state_how_long_only_breastmilk_question")

    tester.assert_answer("state_when_start_breastfeed", "within_1_hour")


@pytest.mark.asyncio
async def test_state_when_start_breastfeed_invalid(tester: AppTester):
    tester.setup_state("state_when_start_breastfeed")
    await tester.user_input("invalid")
    tester.assert_state("state_when_start_breastfeed")

    tester.assert_message(
        "\n".join(
            [
                "Please use numbers from list.",
                "",
                "1. Within 1 hour of birth",
                "2. After 1 hour post-delivery",
                "3. Day 2 & above",
                "4. Undecided",
                "5. Skip",
            ]
        ),
        max_length=160,
    )


@pytest.mark.asyncio
async def test_state_how_long_only_breastmilk(tester: AppTester):
    tester.setup_state("state_how_long_only_breastmilk")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_state("state_how_long_only_breastmilk")

    tester.assert_message(
        "\n".join(
            [
                "",
                "1. 0-3 months",
                "2. 4-5 months",
                "3. For 6 months",
                "4. Longer than 6 months",
                "5. I don't want to only breastfeed",
                "6. I don't know",
                "7. Skip",
            ]
        ),
        max_length=160,
    )


@pytest.mark.asyncio
async def test_state_how_long_only_breastmilk_valid(tester: AppTester):
    tester.setup_state("state_how_long_only_breastmilk")
    await tester.user_input("1")
    tester.assert_state("state_important_to_vaccinate_question")

    tester.assert_answer("state_how_long_only_breastmilk", "0_to_3_months")


@pytest.mark.asyncio
async def test_state_how_long_only_breastmilk_invalid(tester: AppTester):
    tester.setup_state("state_how_long_only_breastmilk")
    await tester.user_input("invalid")
    tester.assert_state("state_how_long_only_breastmilk")

    tester.assert_message(
        "\n".join(
            [
                "Please use numbers from list.",
                "",
                "1. 0-3 months",
                "2. 4-5 months",
                "3. For 6 months",
                "4. Longer than 6 months",
                "5. I don't want to only breastfeed",
                "6. I don't know",
                "7. Skip",
            ]
        ),
        max_length=160,
    )


@pytest.mark.asyncio
async def test_state_important_to_vaccinate_question(tester: AppTester):
    tester.setup_state("state_important_to_vaccinate_question")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_state("state_important_to_vaccinate_question")

    tester.assert_message(
        "\n".join(
            [
                "14/16",
                "",
                "What do you think about this statement?",
                "",
                "I think it is important to vaccinate my baby against severe"
                " diseases like measles, polio, and tetanus",
                "1. Next",
            ]
        ),
        max_length=160,
    )


@pytest.mark.asyncio
async def test_state_important_to_vaccinate_question_valid(tester: AppTester):
    tester.setup_state("state_important_to_vaccinate_question")
    await tester.user_input("1")
    tester.assert_state("state_important_to_vaccinate")

    tester.assert_answer("state_important_to_vaccinate_question", "1")


@pytest.mark.asyncio
async def test_state_important_to_vaccinate(tester: AppTester):
    tester.setup_state("state_important_to_vaccinate")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_state("state_important_to_vaccinate")

    tester.assert_message(
        "\n".join(
            [
                "",
                "1. I strongly agree",
                "2. I agree",
                "3. I don't agree or disagree",
                "4. I disagree",
                "5. I strongly disagree",
                "6. Skip",
            ]
        ),
        max_length=160,
    )


@pytest.mark.asyncio
async def test_state_important_to_vaccinate_valid(tester: AppTester):
    tester.setup_state("state_important_to_vaccinate")
    await tester.user_input("1")
    tester.assert_state("state_vaccine_benefits_outweighs_risk_question")

    tester.assert_answer("state_important_to_vaccinate", "strongly_agree")


@pytest.mark.asyncio
async def test_state_important_to_vaccinate_invalid(tester: AppTester):
    tester.setup_state("state_important_to_vaccinate")
    await tester.user_input("invalid")
    tester.assert_state("state_important_to_vaccinate")

    tester.assert_message(
        "\n".join(
            [
                "Please use numbers from list.",
                "",
                "1. I strongly agree",
                "2. I agree",
                "3. I don't agree or disagree",
                "4. I disagree",
                "5. I strongly disagree",
                "6. Skip",
            ]
        ),
        max_length=160,
    )


@pytest.mark.asyncio
async def test_state_vaccine_benefits_outweighs_risk(tester: AppTester):
    tester.setup_state("state_vaccine_benefits_outweighs_risk")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_state("state_vaccine_benefits_outweighs_risk")

    tester.assert_message(
        "\n".join(
            [
                "",
                "1. I strongly agree",
                "2. I agree",
                "3. I don't agree or disagree",
                "4. I disagree",
                "5. I strongly disagree",
                "6. Skip",
            ]
        ),
        max_length=160,
    )


@pytest.mark.asyncio
async def test_state_vaccine_benefits_outweighs_risk_valid(tester: AppTester):
    tester.setup_state("state_vaccine_benefits_outweighs_risk")
    await tester.user_input("1")
    tester.assert_state("state_likelihood_of_following_schedule")

    tester.assert_answer("state_vaccine_benefits_outweighs_risk", "strongly_agree")


@pytest.mark.asyncio
async def test_state_vaccine_benefits_outweighs_risk_invalid(tester: AppTester):
    tester.setup_state("state_vaccine_benefits_outweighs_risk")
    await tester.user_input("invalid")
    tester.assert_state("state_vaccine_benefits_outweighs_risk")

    tester.assert_message(
        "\n".join(
            [
                "Please use numbers from list.",
                "",
                "1. I strongly agree",
                "2. I agree",
                "3. I don't agree or disagree",
                "4. I disagree",
                "5. I strongly disagree",
                "6. Skip",
            ]
        ),
        max_length=160,
    )


@pytest.mark.asyncio
async def test_state_likelihood_of_following_schedule(tester: AppTester):
    tester.setup_state("state_likelihood_of_following_schedule")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_state("state_likelihood_of_following_schedule")

    tester.assert_message(
        "\n".join(
            [
                "16/16",
                "",
                "How likely are you to follow the recommended shot schedule for your "
                "child?",
                "1. Very unlikely",
                "2. Unlikely",
                "3. Not sure",
                "4. Likely",
                "5. Very likely",
                "6. Skip",
            ]
        ),
        max_length=160,
    )


@pytest.mark.asyncio
async def test_state_likelihood_of_following_schedule_valid(
    tester: AppTester, rapidpro_mock
):
    tester.setup_state("state_likelihood_of_following_schedule")
    await tester.user_input("1")
    tester.assert_state("state_eat_fruits")

    assert [r.path for r in rapidpro_mock.tstate.requests] == [
        "/api/v2/flow_starts.json"
    ]
    request = rapidpro_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "flow": config.RAPIDPRO_MIDLINE_SURVEY_COMPLETE_FLOW,
        "urns": ["whatsapp:27820001001"],
    }


@pytest.mark.asyncio
async def test_state_likelihood_of_following_schedule_invalid(tester: AppTester):
    tester.setup_state("state_likelihood_of_following_schedule")
    await tester.user_input("invalid")
    tester.assert_state("state_likelihood_of_following_schedule")

    tester.assert_message(
        "\n".join(
            [
                "Please use numbers from list.",
                "",
                "1. Very unlikely",
                "2. Unlikely",
                "3. Not sure",
                "4. Likely",
                "5. Very likely",
                "6. Skip",
            ]
        ),
        max_length=160,
    )
