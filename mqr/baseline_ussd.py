import logging
from urllib.parse import urljoin

import aiohttp

import vaccine.healthcheck_config as config
from vaccine.base_application import BaseApplication
from vaccine.states import Choice, ChoiceState, EndState
from vaccine.utils import HTTP_EXCEPTIONS, normalise_phonenumber

logger = logging.getLogger(__name__)


def get_eventstore():
    # TODO: Cache the session globally. Things that don't work:
    # - Declaring the session at the top of the file
    #   You get a `Timeout context manager should be used inside a task` error
    # - Declaring it here but caching it in a global variable for reuse
    #   You get a `Event loop is closed` error
    return aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=5),
        headers={
            "Authorization": f"Token {config.EVENTSTORE_API_TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "mqr-baseline-study-ussd",
        },
    )


def get_rapidpro():
    return aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=5),
        headers={
            "Authorization": f"Token {config.RAPIDPRO_TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "mqr-baseline-study-ussd",
        },
    )


class Application(BaseApplication):
    START_SURVEY = "state_start"

    async def state_start(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        urn = f"whatsapp:{msisdn.lstrip(' + ')}"

        sms_mqr_contact = False

        async with get_rapidpro() as session:
            for i in range(3):
                try:
                    response = await session.get(
                        urljoin(config.RAPIDPRO_URL, "/api/v2/contacts.json"),
                        params={"urn": urn},
                    )
                    response.raise_for_status()
                    response_body = await response.json()

                    if len(response_body["results"]) > 0:
                        contact = response_body["results"][0]

                        if (
                            contact["fields"]["mqr_consent"] == "Accepted"
                            and contact["fields"]["mqr_arm"] == "RCM_SMS"
                        ):
                            sms_mqr_contact = True
                    break
                except HTTP_EXCEPTIONS as e:
                    if i == 2:
                        logger.exception(e)
                        return await self.go_to_state("state_error")
                    else:
                        continue
        if sms_mqr_contact:
            return await self.go_to_state("state_check_existing_result")
        return await self.go_to_state("state_contact_not_found")

    async def state_check_existing_result(self):
        msisdn = self.inbound.from_addr
        exists = False

        async with get_eventstore() as session:
            for i in range(3):
                try:
                    response = await session.get(
                        urljoin(
                            config.EVENTSTORE_API_URL,
                            f"/api/v1/mqrbaselinesurvey/{msisdn}/",
                        ),
                    )
                    if response.status == 404:
                        break
                    response.raise_for_status()
                    exists = True
                    break
                except HTTP_EXCEPTIONS as e:
                    if i == 2:
                        logger.exception(e)
                        return await self.go_to_state("state_error")
                    else:
                        continue
        if exists:
            return await self.go_to_state("state_already_completed")
        return await self.go_to_state("state_breastfeed")

    async def state_breastfeed(self):
        question = self._(
            "1/13\n" "\n" "Do you plan to breastfeed your baby after birth?"
        )
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "Do you plan to breastfeed your baby after birth?"
        )
        choices = [
            Choice("yes", "Yes"),
            Choice("no", "No"),
            Choice("skip", "Skip"),
        ]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_breastfeed_period_question",
        )

    async def state_breastfeed_period_question(self):
        question = self._(
            "2/13 \n"
            "\n"
            "How long do you plan to give your baby only breastmilk "
            "before giving other foods and water?"
        )
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "How long do you plan to give your baby only"
            " breastmilk before giving other foods and water?"
        )
        choices = [Choice("1", "Next")]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_breastfeed_period",
        )

    async def state_breastfeed_period(self):
        question = self._("Breast feeding period")
        error = self._("Please use numbers from list.")
        choices = [
            Choice("0_3_months", "0-3 months"),
            Choice("4_5_months", "4-5 months"),
            Choice("6_months", "For 6 months"),
            Choice("over_6_months", "Longer than 6 months"),
            Choice("not_only_breastfeed", "I don't want to only breastfeed"),
            Choice("dont_know", "I don't know"),
            Choice("skip", "Skip"),
        ]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_vaccine_importance_question",
        )

    async def state_vaccine_importance_question(self):
        question = self._(
            "3/13 \n"
            "\n"
            "What do you think about this statement"
            "\n"
            "I think it is important to vaccinate my baby against severe"
            " diseases like measles, polio and tetanus"
        )
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "What do you think about this statement"
            "\n"
            "I think it is important to vaccinate my baby against severe"
            " diseases like measles, polio and tetanus"
        )
        choices = [Choice("1", "Next")]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_vaccine_importance",
        )

    async def state_vaccine_importance(self):
        question = self._("")
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "What do you think about this statement"
            "\n"
            "I think it is important to vaccinate my baby against severe"
            " diseases like measles, polio and tetanus"
        )
        choices = [
            Choice("strongly_agree", "I strongly agree"),
            Choice("agree", "I agree"),
            Choice("neutral", "I don't agree or disagree"),
            Choice("disagree", "I disagree"),
            Choice("strongly_disagree", "I strongly disagree"),
            Choice("skip", "Skip"),
        ]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_vaccine_benefits_question",
        )

    async def state_vaccine_benefits_question(self):
        question = self._(
            "4/13 \n"
            "\n"
            "What do you think about this statement"
            "\n"
            "The benefits of vaccinating my child outweighs the risks my "
            "child will develop side effects from them"
        )
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "What do you think about this statement"
            "\n"
            "The benefits of vaccinating my child outweighs the risks my "
            "child will develop side effects from them"
        )
        choices = [Choice("1", "Next")]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_vaccine_benefits",
        )

    async def state_vaccine_benefits(self):
        question = self._("")
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "The benefits of vaccinating my child outweighs the risks my "
            "child will develop side effects from them"
        )
        choices = [
            Choice("strongly_agree", "I strongly agree"),
            Choice("agree", "I agree"),
            Choice("neutral", "I don't agree or disagree"),
            Choice("disagree", "I disagree"),
            Choice("strongly_disagree", "I strongly disagree"),
            Choice("skip", "Skip"),
        ]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_clinic_visit_frequency_question",
        )

    async def state_clinic_visit_frequency_question(self):
        question = self._(
            "5/13 \n"
            "\n"
            "How often do you plan to go to the clinic for a a check-up during "
            "this pregnancy?"
        )
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "How often do you plan to go to the clinic for a a check-up during "
            "this pregnancy?"
        )
        choices = [Choice("1", "Next")]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_clinic_visit_frequency",
        )

    async def state_clinic_visit_frequency(self):
        question = self._("")
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "How often do you plan to go to the clinic for a a check-up during "
            "this pregnancy?"
        )
        choices = [
            Choice("more_than_once_a_month", "More than once a month"),
            Choice("once_a_month", "Once a month"),
            Choice("once_2_3_months", "Once every  2 to 3 months"),
            Choice("once_4_5_months", "Once every  4 to 5 months"),
            Choice("once_6_9_months", "Once every 6 to 9 months"),
            Choice("never", "Never"),
            Choice("skip", "Skip"),
        ]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_vegetables",
        )

    async def state_vegetables(self):
        question = self._(
            "6/13 \n"
            "\n"
            "Since becoming pregnant, do you eat vegetables at least once a week?"
        )
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "Since becoming pregnant, do you eat vegetables at least once a week?"
        )
        choices = [
            Choice("yes", "Yes"),
            Choice("no", "No"),
            Choice("skip", "Skip"),
        ]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_fruit",
        )

    async def state_fruit(self):
        question = self._(
            "7/13 \n"
            "\n"
            "Since becoming pregnant, do you eat fruit at least once a week?"
        )
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "Since becoming pregnant, do you eat fruit at least once a week?"
        )
        choices = [
            Choice("yes", "Yes"),
            Choice("no", "No"),
            Choice("skip", "Skip"),
        ]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_dairy",
        )

    async def state_dairy(self):
        question = self._(
            "8/13 \n"
            "\n"
            "Since becoming pregnant, do you have milk, maas, hard cheese or yoghurt "
            "at least once a week?"
        )
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "Since becoming pregnant, do you have milk, maas, hard cheese or yoghurt "
            "at least once a week?"
        )
        choices = [
            Choice("yes", "Yes"),
            Choice("no", "No"),
            Choice("skip", "Skip"),
        ]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_liver_frequency",
        )

    async def state_liver_frequency(self):
        question = self._("9/13 \n" "\n" "How often do you eat liver?")
        error = self._(
            "Please use numbers from list.\n" "\n" "How often do you eat liver?"
        )
        choices = [
            Choice("2_3_times_week", "2-3 times a week"),
            Choice("once_a_week", "Once a week"),
            Choice("once_a_month", "Once a month"),
            Choice("less_once_a_month", "Less than once a month"),
            Choice("never", "Never"),
            Choice("skip", "Skip"),
        ]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_danger_sign1",
        )

    async def state_danger_sign1(self):
        question = self._(
            "10/13 \n"
            "\n"
            "In your view, what is the biggest pregnancy danger sign on this list?"
        )
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "In your view, what is the biggest pregnancy danger sign on this list?"
        )
        choices = [
            Choice("weight_gain", "Weight gain of 4-5 kilograms"),
            Choice("vaginal_bleeding", "Vaginal bleeding"),
            Choice("nose_bleeds", "Nose bleeds"),
            Choice("skip", "Skip"),
        ]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_danger_sign2",
        )

    async def state_danger_sign2(self):
        question = self._(
            "11/13 \n"
            "\n"
            "In your view, what is the biggest pregnancy danger sign on this list?"
        )
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "In your view, what is the biggest pregnancy danger sign on this list?"
        )
        choices = [
            Choice("swollen_feet_legs", "Swollen feet and legs even after sleep"),
            Choice("bloating", "Bloating"),
            Choice("gas", "Gas"),
            Choice("skip", "Skip"),
        ]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_marital_status",
        )

    async def state_marital_status(self):
        question = self._("12/13 \n" "\n" "What is your marital status?")
        error = self._(
            "Please use numbers from list.\n" "\n" "What is your marital status?"
        )
        choices = [
            Choice("never_married", "Never married"),
            Choice("married", "Married"),
            Choice("separated_or_divorced", "Separated or divorced"),
            Choice("widowed", "Widowed"),
            Choice("partner_or_boyfriend", "Have a partner or boyfriend"),
            Choice("skip", "Skip"),
        ]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_education_level_question",
        )

    async def state_education_level_question(self):
        question = self._(
            "13/13 \n"
            "\n"
            "Which answer best describes your highest level of education?"
        )
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "Which answer best describes your highest level of education?"
        )
        choices = [Choice("1", "Next")]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_education_level",
        )

    async def state_education_level(self):
        question = self._("")
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "Which answer best describes your highest level of education? "
        )
        choices = [
            Choice("less_grade_7", "Less than Grade 7"),
            Choice("between_grade_7_12", "Between Grades 7-12"),
            Choice("matric", "Matric"),
            Choice("diploma", "Diploma"),
            Choice("degree_or_higher", "University degree or higher"),
            Choice("skip", "Skip"),
        ]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_submit_data",
        )

    async def state_submit_data(self):
        async with get_eventstore() as session:
            for i in range(3):
                try:
                    answers = self.user.answers
                    data = {
                        "msisdn": self.inbound.from_addr,
                        "breastfeed": answers.get("state_breastfeed"),
                        "breastfeed_period": answers.get("state_breastfeed_period"),
                        "vaccine_importance": answers.get("state_vaccine_importance"),
                        "vaccine_benefits": answers.get("state_vaccine_benefits"),
                        "clinic_visit_frequency": answers.get(
                            "state_clinic_visit_frequency"
                        ),
                        "vegetables": answers.get("state_vegetables"),
                        "fruit": answers.get("state_fruit"),
                        "dairy": answers.get("state_dairy"),
                        "liver_frequency": answers.get("state_liver_frequency"),
                        "danger_sign1": answers.get("state_danger_sign1"),
                        "danger_sign2": answers.get("state_danger_sign2"),
                        "marital_status": answers.get("state_marital_status"),
                        "education_level": answers.get("state_education_level"),
                    }
                    logger.info(">>>> state_submit_data /api/v1/mqrbaselinesurvey/")
                    logger.info(config.EVENTSTORE_API_URL)
                    logger.info(data)
                    response = await session.post(
                        urljoin(
                            config.EVENTSTORE_API_URL, "/api/v1/mqrbaselinesurvey/"
                        ),
                        json=data,
                    )
                    response.raise_for_status()
                    break
                except HTTP_EXCEPTIONS as e:
                    if i == 2:
                        logger.exception(e)
                        return await self.go_to_state("state_error")
                    else:
                        continue
        return await self.go_to_state("state_end")

    async def state_end(self):
        text = self._(
            "Thank you for answering. You'll get your R5 airtime in the next 24 hours "
            "& your first message will be sent soon   Dial *134*550*7# (free) "
            "to update your details"
        )
        return EndState(self, text=text, next=self.START_STATE)

    async def state_error(self):
        return EndState(
            self,
            self._(
                "Sorry, something went wrong. We have been notified. Please try again "
                "later"
            ),
            next=self.START_SURVEY,
        )

    async def state_contact_not_found(self):
        return EndState(
            self,
            self._(
                "\n".join(
                    [
                        "You have dialed the wrong number.",
                        "",
                        "Dial *134*550*2# when you're at a clinic to register on "
                        "MomConnect or dial *134*550*7# to update details",
                    ]
                )
            ),
            next=self.START_SURVEY,
        )

    async def state_already_completed(self):
        return EndState(
            self,
            self._(
                "\n".join(
                    [
                        "Thanks, you have already completed this survey.",
                        "",
                        "You will get your weekly message soon.",
                    ]
                )
            ),
            next=self.START_SURVEY,
        )
