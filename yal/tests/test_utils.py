from datetime import datetime
from unittest import TestCase

from yal import utils


def override_get_today():
    return datetime.strptime("20220519", "%Y%m%d").date()


class BotAgeTests(TestCase):
    def setUp(self):
        utils.get_today = override_get_today

    def test_bot_age(self):
        assert utils.get_bot_age() == 18


def test_generic_error_message():
    """
    It should choose a random message from the generic error message list
    """
    for _ in range(10):
        assert utils.get_generic_error() in utils.GENERIC_ERRORS
