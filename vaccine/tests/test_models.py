import json

from vaccine.models import Event, Message, StateData, User


def test_message_serialisation():
    """
    Message should be able to be serialised and deserialised with no changes
    """
    message = Message(
        to_addr="27820001001",
        from_addr="27820001002",
        transport_name="whatsapp",
        transport_type=Message.TRANSPORT_TYPE.HTTP_API,
        in_reply_to="original-message-id",
        session_event=Message.SESSION_EVENT.NEW,
        content="message content",
        to_addr_type=Message.ADDRESS_TYPE.MSISDN,
        from_addr_type=Message.ADDRESS_TYPE.MSISDN,
    )
    assert message == Message.from_json(message.to_json())


def test_event_serialization():
    """
    Event should be able to be serialised and deserialised with no changes
    """
    event = Event(
        user_message_id="message-id",
        event_type=Event.EVENT_TYPE.DELIVERY_REPORT,
        delivery_status=Event.DELIVERY_STATUS.DELIVERED,
    )
    assert event == Event.from_json(event.to_json())


def test_event_ack():
    """
    sent_message_id should be required for an ack
    """
    exception = None
    try:
        Event(user_message_id="message-id", event_type=Event.EVENT_TYPE.ACK)
    except AssertionError as e:
        exception = e
    assert exception is not None

    Event(
        user_message_id="message-id",
        event_type=Event.EVENT_TYPE.ACK,
        sent_message_id="message-id",
    )


def test_event_nack():
    """
    nack_reason should be required for a nack
    """
    exception = None
    try:
        Event(user_message_id="message-id", event_type=Event.EVENT_TYPE.NACK)
    except AssertionError as e:
        exception = e
    assert exception is not None

    Event(
        user_message_id="message-id",
        event_type=Event.EVENT_TYPE.NACK,
        nack_reason="cannot reach service",
    )


def test_event_delivery_report():
    """
    delivery_status should be required for a delivery report
    """
    exception = None
    try:
        Event(user_message_id="message-id", event_type=Event.EVENT_TYPE.DELIVERY_REPORT)
    except AssertionError as e:
        exception = e
    assert exception is not None

    Event(
        user_message_id="message-id",
        event_type=Event.EVENT_TYPE.DELIVERY_REPORT,
        delivery_status=Event.DELIVERY_STATUS.DELIVERED,
    )


def test_user_serialization():
    """
    Users should be able to be serialised and deserialised with no changes
    """
    user = User("27820001001", state=StateData("state_start"))
    assert user == User.from_json(user.to_json())


def test_user_get_or_create():
    """
    If the data is valid, then return a user with that data, otherwise return a new user
    """
    user = User.get_or_create(
        "27820001001",
        json.dumps({"addr": "27820001001", "state": {"name": "state_start"}}),
    )
    assert user == User("27820001001", state=StateData("state_start"))

    user = User.get_or_create("27820001001", "")
    assert user == User("27820001001")
