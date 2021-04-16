from datetime import date
from unittest import TestCase, mock

from vaccine.utils import SAIDNumber


class SAIDNumberTests(TestCase):
    def test_invalid_type(self):
        with self.assertRaises(ValueError):
            SAIDNumber(9001010001088)
        with self.assertRaises(ValueError):
            SAIDNumber(None)

    def test_not_number(self):
        with self.assertRaises(ValueError):
            SAIDNumber("A123456789012")

    def test_invalid_length(self):
        with self.assertRaises(ValueError):
            SAIDNumber("900101000108")

    def test_invalid_checksum(self):
        with self.assertRaises(ValueError):
            SAIDNumber("9001010001087")

    def test_invalid_dob(self):
        with self.assertRaises(ValueError):
            SAIDNumber("9002310001083")

    @mock.patch("vaccine.utils.get_today")
    def test_dob(self, get_today):
        """
        Should always be 0-100 years old
        """
        get_today.return_value = date(2020, 1, 1)
        assert SAIDNumber("9001010001088").date_of_birth == date(1990, 1, 1)
        assert SAIDNumber("1912310001081").date_of_birth == date(2019, 12, 31)
        assert SAIDNumber("2001010001085").date_of_birth == date(1920, 1, 1)
        assert SAIDNumber("1912310001081").age == 0
        assert SAIDNumber("2001010001085").age == 99
