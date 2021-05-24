import pytest

from vaccine.states import ErrorMessage
from vaccine.validators import nonempty_validator


@pytest.mark.asyncio
async def test_nonempty_validator():
    validator = nonempty_validator("Error message")
    await validator(" test\t")

    err = None
    try:
        await validator(" \t \n ")
    except ErrorMessage as e:
        err = e
    assert err is not None
    assert err.message == "Error message"

    err = None
    try:
        await validator(None)
    except ErrorMessage as e:
        err = e
    assert err is not None
    assert err.message == "Error message"
