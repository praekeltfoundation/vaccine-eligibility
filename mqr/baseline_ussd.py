import logging

import aiohttp

import vaccine.healthcheck_config as config
from mqr.utils import rapidpro
from vaccine.base_application import BaseApplication
from vaccine.states import Choice, ChoiceState, EndState
from vaccine.utils import HTTP_EXCEPTIONS, normalise_phonenumber

logger = logging.getLogger(__name__)


class Application(BaseApplication):
    START_SURVEY = "survey_start"

    async def survey_start(self):
        if config.RAPIDPRO_URL and config.RAPIDPRO_TOKEN:
            msisdn = normalise_phonenumber(self.inbound.from_addr)
            urn = f"whatsapp:{msisdn.lstrip(' + ')}"

            if rapidpro:
                for i in range(3):
                    try:
                        contact = rapidpro.get_contacts(urn=urn).first(
                            retry_on_rate_exceed=True
                        )

                        if not contact:
                            return await self.go_to_state("state_error")

                        data = await contact
                        if not data.mqr_consent and data.mqr_arm:
                            return await self.go_to_state("state_error")
                        break
                    except HTTP_EXCEPTIONS as e:
                        if i == 2:
                            logger.exception(e)
                            return await self.go_to_state("state_error")
                        else:
                            continue

                self.save_answer("state_age", data.age)
                return await self.go_to_state("breast_feeding")
            return await self.go_to_state("state_error")

    async def breast_feeding(self):
        question = self._(
            "1/13 \n" "\n" "Do you plan to breastfeed your baby after birth?"
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
            next="breast_feeding_term",
        )

    async def breast_feeding_term(self):
        question = self._(
            "2/13 \n"
            "\n"
            "*How long do you plan to give your baby only breastmilk "
            "before giving other foods and water?*"
        )
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "*How long do you plan to give your baby only"
            " breastmilk before giving other foods and water?*"
        )
        choices = [Choice("1", "Next")]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="breast_feeding_term_answers",
        )

    async def breast_feeding_term_answers(self):
        question = self._("Breast feeding period")
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "*How long do you plan to give your baby only"
            " breastmilk before giving other foods and water?*"
        )
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
            next="vaccination_diseases_statement",
        )

    async def vaccination_diseases_statement(self):
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
            next="vaccination_severe_diseases_statement_answers",
        )

    async def vaccination_diseases_statement_answers(self):
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
            next="vaccination_risks_statement",
        )

    async def vaccination_risks_statement(self):
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
            next="vaccination_risks_statement_answers",
        )

    async def vaccination_risks_statement_answers(self):
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
            next="pregnancy_checkup",
        )

    async def pregnancy_checkup(self):
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
            next="pregnancy_checkup_answers",
        )

    async def pregnancy_checkup_answers(self):
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
            next="eating_vegetables",
        )

    async def eating_vegetables(self):
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
            next="eating_fruits",
        )

    async def eating_fruits(self):
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
            next="eating_dairy_products",
        )

    async def eating_dairy_products(self):
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
            next="eating_liver_frequency",
        )

    async def eating_liver_frequency(self):
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
            next="pregnancy_danger_signs",
        )

    async def pregnancy_danger_signs(self):
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
            Choice("weight_gain", "Yes"),
            Choice("vaginal_bleeding", "Weight gain of 4-5 kilograms"),
            Choice("nose_bleeds", "Nose bleeds"),
            Choice("skip", "Skip"),
        ]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="second_pregnancy_danger_signs",
        )

    async def second_pregnancy_danger_signs(self):
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
            next="marital_status",
        )

    async def marital_status(self):
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
            next="education_highest_level",
        )

    async def education_highest_level(self):
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
            next="vaccinate_baby_statement_answers",
        )

    async def education_highest_level_answers(self):
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
            next="state_end",
        )

    async def state_end(self):
        text = self._(
            "Thank you for answering. You'll get your R5 airtime in the next 24 hours "
            "& your first message will be sent soon   Dial *134*550*7# (free) "
            "to update your details"
        )
        return EndState(self, text=text, next=self.START_STATE)

    async def survey_error(self):
        return EndState(
            self,
            self._(
                "Sorry, something went wrong. We have been notified. Please try again "
                "later"
            ),
            next=self.START_SURVEY,
        )
