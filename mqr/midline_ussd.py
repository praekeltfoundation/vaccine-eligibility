import logging
from urllib.parse import urljoin

import aiohttp

from mqr import config
from vaccine.base_application import BaseApplication
from vaccine.states import Choice, ChoiceState, EndState
from vaccine.utils import HTTP_EXCEPTIONS, normalise_phonenumber

logger = logging.getLogger(__name__)
# TODO: FWB

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
            "User-Agent": "mqr-midline-study-ussd",
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
                            f"/api/v1/mqrmidlinesurvey/{msisdn}/",
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
        return await self.go_to_state("state_eat_fruits")

    async def state_eat_fruits(self):
        question = self._(
            "1/16\n" "\n" "Do you eat fruits at least once a day?"
        )
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "Do you eat fruits at least once a day?"
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
            next="state_eat_vegetables",
        )

    async def state_eat_vegetables(self):
        question = self._(
            "2/16\n" "\n" "Do you eat vegetables at least once a day?"
        )
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "Do you eat vegetables at least once a day?"
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
            next="state_eat_liver",
        )

    async def state_eat_liver(self):
        question = self._(
            "3/16\n" "\n" "How often do you eat liver?"
        )
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "How often do you eat liver?"
        )
        choices = [
            Choice("once_week", "Once a week"),
            Choice("once_2_weeks", "Once every 2 weeks"),
            Choice("once_month", "Once a month"),
            Choice("less_freq_once_month", "Less frequently than once a month"),
            Choice("not_at_all", "Not at all"),
            Choice("skip", "Skip"),
        ]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_foods_contain",
        )

    async def state_foods_contain(self):
        question = self._(
            "4/16\n" "\n" "Nuts, eggs, meat, fish, and green vegetables have a lot of what in them?"
        )
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "Nuts, eggs, meat, fish, and green vegetables have a lot of what in them?"
        )
        choices = [
            Choice("calcium", "Calcium"),
            Choice("vitamin_c", "Vitamin C"),
            Choice("iron", "Iron"),
            Choice("fibre", "Fibre"),
            Choice("skip", "Skip"),
        ]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_amount_alcohol_since_pregnant",
        )

    async def state_amount_alcohol_since_pregnant(self):
        question = self._(
            "Since becoming pregnant, has the number of alcoholic drinks you have per week:"
        )
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "Since becoming pregnant, has the number of alcoholic drinks you have per week:"
        )
        choices = [
            Choice("no_change", "Stayed the same"),
            Choice("reduced", "Reduced"),
            Choice("increased", "Increased"),
            Choice("stopped", "Stopped"),
            Choice("i_never_drink", "I never drink"),
            Choice("skip", "Skip"),
        ]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_swollen_feet_symptom_of",
        )

    async def state_swollen_feet_symptom_of(self):
        question = self._(
            "6/16\n" "\n" "What can severe swollen feet even after a night's sleep be a symptom of?"
        )
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "What can severe swollen feet even after a night's sleep be a symptom of?"
        )
        choices = [
            Choice("urinary_tract_infection", "Urinary tract infection"),
            Choice("pre_eclampsia", "Pre-eclampsia"),
            Choice("anemia", "Anemia"),
            Choice("skip", "Skip"),
        ]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_dizzy_weak_symptom_of",
        )

    async def state_dizzy_weak_symptom_of(self):
        question = self._(
            "7/16\n" "\n" "What could a mix of feeling dizzy and weak/tired be a symptom of?"
        )
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "What could a mix of feeling dizzy and weak/tired be a symptom of?"
        )
        choices = [
            Choice("urinary_tract_infection", "Urinary tract infection"),
            Choice("pre_eclampsia", "Pre-eclampsia"),
            Choice("anemia", "Anemia"),
            Choice("skip", "Skip"),
        ]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_baby_kicks_felt",
        )        

    async def state_baby_kicks_felt(self):
        question = self._(
            "8/16\n" "\n" "Do you think baby kicks should be felt every day in the third trimester of pregnancy?"
        )
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "Do you think baby kicks should be felt every day in the third trimester of pregnancy?"
        )
        choices = [
            Choice("yes", "Yes"),
            Choice("maybe", "Maybe"),
            Choice("no", "No"),
            Choice("dont_know", "Don't know"),
            Choice("skip", "Skip"),
        ]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_biggest_danger_sign_pregnancy",
        )

    async def state_biggest_danger_sign_pregnancy(self):
        question = self._(
            "9/16\n" "\n" "In your view, what is the biggest pregnancy danger sign on this list?"
        )
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "In your view, what is the biggest pregnancy danger sign on this list?"
        )
        choices = [
            Choice("4_5kg_weight_gain", "Weight gain of 4-5 kilograms"),
            Choice("vaginal_bleeding", "Vaginal bleeding"),
            Choice("nose_bleeds", "Nose bleeds"),
            Choice("skip", "Skip"),
        ]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_planning_on_breastfeeding",
        )

    async def state_planning_on_breastfeeding(self):
        async def next_state(choice: Choice):
            if choice.value == "yes":
                return "state_biggest_reason_to_breastfeed_question"
            if choice.value == "no":
                return "state_why_not_intend_breastfeeding_question"
            if choice.value == "skip":        
                return "state_important_to_vaccinate"
            return "state_important_to_vaccinate"

        question = self._(
            "10/16\n" "\n" "Are you planning on breastfeeding your baby after he/she is born?"
        )
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "Are you planning on breastfeeding your baby after he/she is born?"
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
            next=next_state,
        )
    #split
    
    async def state_why_not_intend_breastfeeding_question(self):
        question = self._(
            "11/16\n" "\n" "What is the biggest reason why you don't intend on breastfeeding your baby after he/she is born?"
        )
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "What is the biggest reason why you don't intend on breastfeeding your baby after he/she is born?"
        )
        choices = [Choice("1", "Next")]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_why_not_intend_breastfeeding",
        )

    async def state_why_not_intend_breastfeeding(self):
        question = self._(
            ""
        )
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "What is the biggest reason why you don't intend on breastfeeding your baby after he/she is born?"
        )
        choices = [
            Choice("not_nutritious", "Breastmilk is not nutritious"),
            Choice("low_milk_supply", "Low milk supply"),
            Choice("sore_nipples", "Sore nipples"),
            Choice("takes_too_long", "Takes too long"),
            Choice("lacks_info", "Lack of information"),
            Choice("lacks_support", "Lack of support"),
            Choice("other_reason", "Other"),
            Choice("skip", "Skip"),
        ]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_important_to_vaccinate_question",
        )
    #split
    async def state_biggest_reason_to_breastfeed_question(self):
        question = self._(
            "11/16\n" "\n" "What is the biggest reason why you want to breastfeed your baby?"
        )
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "What is the biggest reason why you want to breastfeed your baby?"
        )
        choices = [Choice("1", "Next")]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_biggest_reason_to_breastfeed",
        )

    async def state_biggest_reason_to_breastfeed(self):
        question = self._(
            ""
        )
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "What is the biggest reason why you want to breastfeed your baby?"
        )
        choices = [
            Choice("boosts_baby_immunity", "Breastmilk boosts my baby's immunity"),
            Choice("tastier_than_formula", "Breastmilk is tastier than formula"),
            Choice("improves_my_health", "Breastfeeding improves my health"),
            Choice("was_told_to", "I was told to breastfeed"),
            Choice("other_reason", "Other"),
            Choice("skip", "Skip"),            
        ]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_when_start_breastfeed",
        )

    async def state_when_start_breastfeed(self):
        question = self._(
            "12/16\n" "\n" "When do you plan to start breastfeeding your baby?"
        )
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "When do you plan to start breastfeeding your baby?"
        )
        choices = [
            Choice("within_1_hour", "Within 1 hour of birth"),
            Choice("after_1_hour", "After 1 hour post-delivery"),
            Choice("day_two_and_above", "Day 2 & above"),
            Choice("undecided", "Undecided"),
            Choice("skip", "Skip"),
        ]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_how_long_only_breastmilk_question",
        )    

    #split
    async def state_how_long_only_breastmilk_question(self):
        question = self._(
            "13/16\n" "\n" "How long do you plan to give your baby only breastmilk before giving other foods and water?"
        )
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "How long do you plan to give your baby only breastmilk before giving other foods and water?"
        )
        choices = [Choice("1", "Next")]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_how_long_only_breastmilk",
        )
    async def state_how_long_only_breastmilk(self):
        question = self._(
            ""
        )
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "How long do you plan to give your baby only breastmilk before giving other foods and water?"
        )
        choices = [
            Choice("0_to_3_months", "0-3 months"),
            Choice("4_to_5_months", "4-5 months"),
            Choice("6_months", "For 6 months"),
            Choice("longer_than_6_months", "Longer than 6 months"),
            Choice("dont_want_only_breastfeed", "I don't want to only breastfeed"),
            Choice("dont_know", "I don't know"),
            Choice("skip", "Skip"),
        ]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_important_to_vaccinate_question",
        )    
    async def state_important_to_vaccinate_question(self):
        question = self._(
            "14/16\n" "\n" "What do you think about this statement?\n"
            "\n"
            "I think it is important to vaccinate my baby against severe diseases like measles, polio, and tetanus"
        )
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "What do you think about this statement?\n"
            "\n"
            "I think it is important to vaccinate my baby against severe diseases like measles, polio, and tetanus"
        )
        choices = [Choice("1", "Next")]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_breastfeed_period_question",
        )

    async def state_important_to_vaccinate(self):
        question = self._(
            ""
        )
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "What do you think about this statement?\n"
            "\n"
            "I think it is important to vaccinate my baby against severe diseases like measles, polio, and tetanus"
        )
        choices = [
            Choice("strongly_agree", "I strongly agree"),
            Choice("agree", "I agree"),
            Choice("undecided", "I don't agree or disagree"),
            Choice("disagree", "I disagree"),
            Choice("strongly_disagree", "I strongly disagree"),
            Choice("skip", "Skip"),
        ]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_vaccine_benefits_outweighs_risk_question",
        )            

    #split
    async def state_vaccine_benefits_outweighs_risk_question(self):
        question = self._(
            "15/16\n" "\n" "What do you think about this statement?\n"
             "\n"
             "The benefits of vaccinating my child outweighs the risks my child will develop side effects from them"
        )
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "What do you think about this statement?\n"
             "\n"
             "The benefits of vaccinating my child outweighs the risks my child will develop side effects from them"
        )
        choices = [Choice("1", "Next")]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_vaccine_benefits_outweighs_risk",
        ) 

    async def state_vaccine_benefits_outweighs_risk(self):
        question = self._(
            "15/16\n" "\n" "What do you think about this statement?\n"
             "\n"
             "The benefits of vaccinating my child outweighs the risks my child will develop side effects from them"
        )
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "What do you think about this statement?\n"
             "\n"
             "The benefits of vaccinating my child outweighs the risks my child will develop side effects from them"
        )
        choices = [
            Choice("strongly_agree", "I strongly agree"),
            Choice("agree", "I agree"),
            Choice("undecided", "I don't agree or disagree"),
            Choice("disagree", "I disagree"),
            Choice("strongly_disagree", "I strongly disagree"),
            Choice("skip", "Skip"),
        ]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_likelihood_of_following_schedule",
        )    

    async def state_likelihood_of_following_schedule(self):
        question = self._(
            "16/16\n" "\n" "How likely are you to follow the recommended shot schedule for your child?"
        )
        error = self._(
            "Please use numbers from list.\n"
            "\n"
            "How likely are you to follow the recommended shot schedule for your child?"
        )
        choices = [
            Choice("very_unlikely", "Very unlikely"),
            Choice("unlikely", "Unlikely"),
            Choice("not_sure", "Not sure"),
            Choice("likely", "Likely"),
            Choice("very_likely", "Very likely"),
            Choice("skip", "Skip"),
        ]

        return ChoiceState(
            self,
            question=question,
            error=error,
            choices=choices,
            next="state_end",
        )    
    # TODO FWB - Update all functions below this line (copied from baseline) 
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
        return await self.go_to_state("state_update_rapidpro_contact")

    async def state_update_rapidpro_contact(self):
        msisdn = normalise_phonenumber(self.inbound.from_addr)
        urn = f"whatsapp:{msisdn.lstrip(' + ')}"

        async with get_rapidpro() as session:
            for i in range(3):
                try:
                    data = {
                        "flow": config.RAPIDPRO_BASELINE_SURVEY_COMPLETE_FLOW,
                        "urns": [urn],
                    }
                    response = await session.post(
                        urljoin(config.RAPIDPRO_URL, "/api/v2/flow_starts.json"),
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
            "\n".join(
                [
                    "Thank you for answering these questions. Your R5 airtime will be sent within 24 hours."
                    "You will get your next MomConnect message soon.",
                    "Have a lovely day!",
                ]
            )
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

