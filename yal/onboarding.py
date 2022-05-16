from vaccine.base_application import BaseApplication
from vaccine.states import EndState


class Application(BaseApplication):
    START_STATE = "state_age_month"

    async def state_age_month(self):
        return EndState(
            self,
            self._("TODO: Onboarding"),
            next=self.START_STATE,
        )
