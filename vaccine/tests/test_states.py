from ..base_application import BaseApplication
from ..models import User
from ..states import BaseWhatsAppChoiceState, Choice


def test_base_whatsapp_choice_state():
    """
    Because list and buttons on whatsapp get truncated to 20 characters, we might get
    back text that has been trucated, so we need to deal with that and select the
    correct choice.
    """
    user = User("+27820001001")
    app = BaseApplication(user)
    choice = Choice("long", "Choice that is longer than 20 characters")
    state = BaseWhatsAppChoiceState(
        app, "test question", [choice], "test error", "test next"
    )
    assert state._get_choice("Choice that is longer than 20 characters") == choice
    assert state._get_choice("Choice that is longe") == choice
