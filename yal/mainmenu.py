from vaccine.base_application import BaseApplication
from vaccine.states import EndState


class Application(BaseApplication):
    START_STATE = "state_mainmenu"

    async def state_mainmenu(self):
        return EndState(
            self,
            self._("TODO: Main Menu"),
            next=self.START_STATE,
        )
