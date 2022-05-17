from vaccine.states import EndState
from yal.yal_base_application import YalBaseApplication


class Application(YalBaseApplication):
    START_STATE = "state_mainmenu"

    async def state_mainmenu(self):
        return EndState(
            self,
            self._("TODO: Main Menu"),
            next=self.START_STATE,
        )
