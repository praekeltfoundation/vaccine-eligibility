from datetime import date
from unittest import TestCase, mock

from vaccine.utils import Countries, SAIDNumber, display_phonenumber


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

    def test_sex(self):
        assert SAIDNumber("9001010001088").sex == SAIDNumber.SEX.female
        assert SAIDNumber("9001015001083").sex == SAIDNumber.SEX.male


class DisplayPhoneNumberTests(TestCase):
    def test_valid(self):
        assert display_phonenumber("27820001001") == "082 000 1001"

    def test_invalid(self):
        assert display_phonenumber("invalid") == "invalid"


class CountriesTests(TestCase):
    def test_search_united_states(self):
        assert Countries().search_for_country("united states")[0][0] == "UM"
        assert Countries().search_for_country("united states")[1][0] == "US"

    def test_search_ireland(self):
        assert Countries().search_for_country("ireland")[0][0] == "IE"
        assert Countries().search_for_country("ireland")[1][0] == "GB"

    def test_search_eswatini(self):
        assert Countries().search_for_country("eswatini")[0][0] == "SZ"

    def test_search_hong_kong(self):
        assert Countries().search_for_country("hong kong")[0][0] == "HK"

    def test_search_ivory_coast(self):
        assert Countries().search_for_country("ivory coast")[2][0] == "CI"
        assert Countries().search_for_country("cote d ivory")[0][0] == "CI"
        assert Countries().search_for_country("cote d'ivory")[0][0] == "CI"
