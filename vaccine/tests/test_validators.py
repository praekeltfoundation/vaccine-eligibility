import pytest

from vaccine.states import ErrorMessage
from vaccine.validators import name_validator, nonempty_validator


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


@pytest.mark.asyncio
async def test_name_validator():
    validator = name_validator("Error message")
    await validator(" test\t")

    err = None
    try:
        await validator(" a ")
    except ErrorMessage as e:
        err = e
    assert err is not None
    assert err.message == "Error message"

    err = None
    try:
        await validator(" 123456789 ")
    except ErrorMessage as e:
        err = e
    assert err is not None
    assert err.message == "Error message"
