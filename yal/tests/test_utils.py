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
