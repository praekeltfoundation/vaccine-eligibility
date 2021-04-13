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


def luhn_checksum(input):
    def digits_of(n):
        return [int(d) for d in str(n)]

    digits = digits_of(input)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = 0
    checksum += sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d * 2))
    return checksum % 10
