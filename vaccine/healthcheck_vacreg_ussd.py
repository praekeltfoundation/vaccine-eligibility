from typing import List

from vaccine import vacreg_config as config
from vaccine.healthcheck_ussd import Application as HealthCheckApp
from vaccine.models import Message
from vaccine.states import Choice, MenuState
from vaccine.utils import SAIDNumber
from vaccine.vaccine_reg_ussd import Application as VacRegApp


class Application(VacRegApp, HealthCheckApp):
    START_STATE = "state_menu"

    async def state_menu(self):
        ussd_parts = self.inbound.to_addr.split("*")
        if len(ussd_parts) == 4 and len(ussd_parts[3]) == 14:
            try:
                id_number = SAIDNumber(ussd_parts[3][:13])

                self.save_answer(
                    "state_identification_type", VacRegApp.ID_TYPES.rsa_id.name
                )
                self.save_answer("state_identification_number", id_number.id_number)

                if (
                    id_number.age < config.ELIGIBILITY_AGE_GATE_MIN
                    and id_number.age > config.AMBIGUOUS_MAX_AGE - 100
                ):
                    return await self.go_to_state("state_under_age_notification")

                dob = id_number.date_of_birth
                if id_number.age > config.AMBIGUOUS_MAX_AGE - 100:
                    self.save_answer("state_dob_year", str(dob.year))
                self.save_answer("state_dob_month", str(dob.month))
                self.save_answer("state_dob_day", str(dob.day))
                self.save_answer("state_gender", id_number.sex.value)
                return await self.go_to_state("state_terms_and_conditions")
            except ValueError:
                pass

        return MenuState(
            self,
            question="Welcome to the NATIONAL DEPARTMENT OF HEALTH's COVID-19 Response "
            "service",
            error="ERROR: Please try again",
            choices=[
                Choice(VacRegApp.START_STATE, "Vaccine Registration"),
                Choice(HealthCheckApp.START_STATE, "HealthCheck Symptom checker"),
            ],
        )

    async def process_message(self, message: Message) -> List[Message]:
        if (
            message.session_event == Message.SESSION_EVENT.NEW
            and self.state_name is not None
            and self.state_name != self.START_STATE
        ):
            self.save_answer("resume_state", self.state_name)
            if hasattr(VacRegApp, self.state_name):
                self.state_name = "state_timed_out_vacreg"
            else:
                self.state_name = "state_timed_out_healthcheck"
        return await super().process_message(message)

    async def state_timed_out_vacreg(self):
        return MenuState(
            self,
            question="Welcome back to the NATIONAL DEPARTMENT OF HEALTH's COVID-19 "
            "Vaccine Registration service",
            error="Welcome back to the NATIONAL DEPARTMENT OF HEALTH's COVID-19 "
            "Vaccine Registration service",
            choices=[
                Choice(self.user.answers["resume_state"], "Continue where I left off"),
                Choice(VacRegApp.START_STATE, "Start over"),
            ],
        )

    async def state_timed_out_healthcheck(self):
        return MenuState(
            self,
            question="\n".join(
                [
                    "Welcome back to The National Department of Health's COVID-19 "
                    "Service",
                    "",
                    "Reply",
                ]
            ),
            error="\n".join(
                [
                    "Welcome back to The National Department of Health's COVID-19 "
                    "Service",
                    "",
                    "Reply",
                ]
            ),
            choices=[
                Choice(self.user.answers["resume_state"], "Continue where I left off"),
                Choice(HealthCheckApp.START_STATE, "Start over"),
            ],
        )
