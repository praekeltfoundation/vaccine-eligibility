from datetime import datetime, timezone
from json import JSONDecodeError
from uuid import uuid4

DECODE_MESSAGE_EXCEPTIONS = (
    UnicodeDecodeError,
    JSONDecodeError,
    TypeError,
    KeyError,
    ValueError,
)


def random_id():
    return uuid4().hex


def current_timestamp():
    return datetime.now(timezone.utc)
