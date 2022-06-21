import logging

from vaccine.base_application import BaseApplication
from vaccine.states import EndState

logger = logging.getLogger(__name__)


class Application(BaseApplication):
    START_STATE = "state_please_call_start"

    async def state_please_call_start(self):
        return EndState(
            self,
            self._("TODO: Please Call Me"),
            next=self.START_STATE,
        )
