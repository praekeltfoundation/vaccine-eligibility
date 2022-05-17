from vaccine.states import EndState
from yal.yal_base_application import BaseApplication


class Application(BaseApplication):
    START_STATE = "state_age_month"

    async def state_age_month(self):
        return EndState(
            self,
            self._("TODO: Onboarding"),
            next=self.START_STATE,
        )
