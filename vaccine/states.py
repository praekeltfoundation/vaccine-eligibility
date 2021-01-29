from typing import List

from vaccine.models import Message


class EndState:
    def __init__(self, app, text: str, next: str):
        self.app = app
        self.text = text
        self.next = next

    async def process_message(self, message: Message) -> List[Message]:
        self.app.user.in_session = False
        self.app.user.state.name = self.next
        return await self.display(message)

    async def display(self, message: Message) -> List[Message]:
        # TODO: send message
        return [message.reply(self.text, continue_session=False)]
