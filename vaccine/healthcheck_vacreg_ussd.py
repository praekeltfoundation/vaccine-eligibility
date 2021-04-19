from typing import List

from vaccine.healthcheck_ussd import Application as HealthCheckApp
from vaccine.models import Message
from vaccine.states import Choice, MenuState
from vaccine.vaccine_reg_ussd import Application as VacRegApp


class Application(VacRegApp, HealthCheckApp):
    START_STATE = "state_menu"

    async def state_menu(self):
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
                Choice(self.START_STATE, "Start over"),
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
                Choice(self.START_STATE, "Start over"),
            ],
        )
