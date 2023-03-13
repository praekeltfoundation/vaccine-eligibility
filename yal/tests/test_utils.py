from datetime import datetime
from unittest import TestCase

from yal import config, utils


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


def test_replace_persona_fields():
    """
    It should replace placeholders with the value in the given dict
    """
    meta_dict = {
        "question": "this is the question to show other things don't get replaced",
        "persona_emoji": "🦸",
        "persona_name": "caped crusader",
    }
    content = (
        "Hi 👋, You chose to call me [persona_name] and I look like [persona_emoji]"
        "Note that question doesn't get replaced. Neither does [question]"
    )

    replaced_content = utils.replace_persona_fields(content, meta_dict)
    assert replaced_content == (
        "Hi 👋, You chose to call me caped crusader and I look like 🦸"
        "Note that question doesn't get replaced. Neither does [question]"
    )


def test_replace_persona_fields_uses_placeholders():
    """
    It should replace placeholders with the value in the given dict
    """
    meta_dict = {}
    content = (
        "Hi 👋, You chose to call me [persona_name] and I look like [persona_emoji]"
        "Note that question doesn't get replaced. Neither does [question]"
    )

    replaced_content = utils.replace_persona_fields(content, meta_dict)
    assert replaced_content == (
        "Hi 👋, You chose to call me B-wise and I look like 🤖"
        "Note that question doesn't get replaced. Neither does [question]"
    )


def test_replace_persona_fields_uses_placeholders_if_skip():
    """
    It should use the placeholders if the user's value is "skip"
    """
    meta_dict = {
        "persona_emoji": "Skip",
        "persona_name": "skip",
    }
    content = (
        "Hi 👋, You chose to call me [persona_name] and I look like [persona_emoji]"
        "Note that question doesn't get replaced. Neither does [question]"
    )

    replaced_content = utils.replace_persona_fields(content, meta_dict)
    assert replaced_content == (
        "Hi 👋, You chose to call me B-wise and I look like 🤖"
        "Note that question doesn't get replaced. Neither does [question]"
    )


def test_clean_inbound():
    """
    Should remove all non-word or `#` characters, and excess whitespace
    """
    assert utils.clean_inbound("#") == "#"
    assert utils.clean_inbound("  test    whitespace ") == "test whitespace"
    assert utils.clean_inbound("test%&^*special)(*chars") == "test special chars"


def test_get_by_path():
    """
    Should return the value stored at the path
    """
    obj = {"foo": {"bar": {"baz": "hello world"}}}
    assert utils.get_by_path(obj, "foo", "bar", "baz") == "hello world"
    assert utils.get_by_path(obj, "invalid", "path") is None
    assert utils.get_by_path({}, "invalid", "path") is None
    assert utils.get_by_path(obj, "invalid", default_value="default") == "default"
    assert utils.get_by_path(obj) == obj
    assert utils.get_by_path(None, "foo", "bar", "baz") is None


def test_get_current_datetime_qa_override():
    """
    QA_OVERRIDE_CURRENT_TIMESTAMP should change the output of get_current_datetime
    """
    assert utils.get_current_datetime() != datetime(2022, 3, 4, 5, 6, 7)
    config.QA_OVERRIDE_CURRENT_TIMESTAMP = "2022-03-04T05:06:07"
    assert utils.get_current_datetime() == datetime(2022, 3, 4, 5, 6, 7)


def test_is_integer():
    obj = "1234"
    assert utils.is_integer(obj)

    obj = "string"
    assert not utils.is_integer(obj)

    obj = 1234
    assert utils.is_integer(obj)
