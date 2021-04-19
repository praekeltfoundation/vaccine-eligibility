from vaccine.healthcheck_ussd import Application as HealthCheckApp
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
