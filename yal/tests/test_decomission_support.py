import pytest

from vaccine.models import Message
from vaccine.testing import AppTester
from yal.decomission_support import Application


@pytest.fixture
def tester():
    return AppTester(Application)


@pytest.mark.asyncio
async def test_state_support_start_display(tester: AppTester):
    """Test that the support start menu displays correctly"""
    tester.setup_state("state_support_start")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_state("state_support_start")
    tester.assert_message(
        "\n".join(
            [
                "What kind of support are you looking for right now?",
                "",
                "*Choose what fits you best* 👇",
                "1. 🤰 Pregnancy care",
                "2. 🛡️ HIV prevention",
                "3. 🗣️ Health updates",
                "4. 💖 Sex health info",
            ]
        )
    )


@pytest.mark.asyncio
async def test_state_support_start_to_pregnancy_care_number(tester: AppTester):
    """Test navigation to pregnancy care using number choice"""
    tester.setup_state("state_support_start")
    await tester.user_input("1")

    # EndState sets state to None
    tester.assert_state(None)
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_state_support_start_to_hiv_prevention_number(tester: AppTester):
    """Test navigation to HIV prevention using number choice"""
    tester.setup_state("state_support_start")
    await tester.user_input("2")

    # EndState sets state to None
    tester.assert_state(None)
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_state_support_start_to_health_updates_number(tester: AppTester):
    """Test navigation to health updates using number choice"""
    tester.setup_state("state_support_start")
    await tester.user_input("3")

    # EndState sets state to None
    tester.assert_state(None)
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_state_support_start_to_sex_health_info_number(tester: AppTester):
    """Test navigation to sex health info using number choice"""
    tester.setup_state("state_support_start")
    await tester.user_input("4")

    # EndState sets state to None
    tester.assert_state(None)
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_state_support_start_invalid_choice(tester: AppTester):
    """Test error handling for invalid choice"""
    tester.setup_state("state_support_start")
    await tester.user_input("invalid")

    tester.assert_state("state_support_start")
    tester.assert_message(
        "⚠️ This service works best when you use the numbered options available"
    )


@pytest.mark.asyncio
async def test_state_support_start_invalid_number(tester: AppTester):
    """Test error handling for invalid number choice"""
    tester.setup_state("state_support_start")
    await tester.user_input("99")

    tester.assert_state("state_support_start")
    tester.assert_message(
        "⚠️ This service works best when you use the numbered options available"
    )


@pytest.mark.asyncio
async def test_state_pregnancy_care_content(tester: AppTester):
    """Test pregnancy care end state content"""
    tester.setup_state("state_support_start")
    await tester.user_input("1")

    # EndState sets state to None
    tester.assert_state(None)
    tester.assert_num_messages(1)
    # Verify message contains key content
    message = tester.application.messages[0]
    assert "got this" in message.content
    assert "MomConnect" in message.content
    assert "wa.me/2796312456" in message.content


@pytest.mark.asyncio
async def test_state_hiv_prevention_content(tester: AppTester):
    """Test HIV prevention end state content"""
    tester.setup_state("state_support_start")
    await tester.user_input("2")

    # EndState sets state to None
    tester.assert_state(None)
    tester.assert_num_messages(1)
    # Verify message contains key content
    message = tester.application.messages[0]
    assert "Staying safe" in message.content
    assert "myPrep" in message.content
    assert "www.myprep.co.za" in message.content


@pytest.mark.asyncio
async def test_state_health_updates_content(tester: AppTester):
    """Test health updates end state content"""
    tester.setup_state("state_support_start")
    await tester.user_input("3")

    # EndState sets state to None
    tester.assert_state(None)
    tester.assert_num_messages(1)
    # Verify message contains key content
    message = tester.application.messages[0]
    assert "Stay informed" in message.content
    assert "ContactNDOH" in message.content
    assert "wa.me/27600123456" in message.content


@pytest.mark.asyncio
async def test_state_sex_health_info_content(tester: AppTester):
    """Test sex health info end state content"""
    tester.setup_state("state_support_start")
    await tester.user_input("4")

    # EndState sets state to None
    tester.assert_state(None)
    tester.assert_num_messages(1)
    # Verify message contains key content
    message = tester.application.messages[0]
    assert "Curious is normal" in message.content
    assert "SelfCav" in message.content
    assert "wa.me/27873731548" in message.content


@pytest.mark.asyncio
async def test_direct_state_access_pregnancy_care(tester: AppTester):
    """Test accessing pregnancy care state directly"""
    tester.setup_state("state_pregnancy_care")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    # EndState sets state to None
    tester.assert_state(None)
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_direct_state_access_hiv_prevention(tester: AppTester):
    """Test accessing HIV prevention state directly"""
    tester.setup_state("state_hiv_prevention")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    # EndState sets state to None
    tester.assert_state(None)
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_direct_state_access_health_updates(tester: AppTester):
    """Test accessing health updates state directly"""
    tester.setup_state("state_health_updates")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    # EndState sets state to None
    tester.assert_state(None)
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_direct_state_access_sex_health_info(tester: AppTester):
    """Test accessing sex health info state directly"""
    tester.setup_state("state_sex_health_info")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    # EndState sets state to None
    tester.assert_state(None)
    tester.assert_num_messages(1)
