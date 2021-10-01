import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Iterable, Optional

from email_validator import EmailNotValidError, caching_resolver, validate_email

from vaccine.states import ErrorMessage
from vaccine.utils import clean_name, normalise_phonenumber

dns_resolver = caching_resolver()
thread_pool = ThreadPoolExecutor()


def nonempty_validator(error_text):
    async def validator(value):
        if value is None or value.strip() == "":
            raise ErrorMessage(error_text)

    return validator


def name_validator(error_text):
    async def validator(value):
        value = clean_name(value)
        if len(value) < 2:
            raise ErrorMessage(error_text)
        if value.isdigit():
            raise ErrorMessage(error_text)

    return validator


def phone_number_validator(error_text):
    async def validator(value):
        try:
            normalise_phonenumber(value)
        except ValueError:
            raise ErrorMessage(error_text)

    return validator


def email_validator(error_text: str, skip_keywords: Iterable[str] = []):
    async def validator(value: Optional[str]):
        if value and value.strip().lower() in [
            k.strip().lower() for k in skip_keywords
        ]:
            return

        try:
            # The email validation library makes a sync DNS call, so we need to wrap it
            future = thread_pool.submit(
                validate_email, value, dns_resolver=dns_resolver
            )
            await asyncio.wrap_future(future)
        except EmailNotValidError as e:
            raise ErrorMessage(error_text.format(email_error=e))

    return validator
