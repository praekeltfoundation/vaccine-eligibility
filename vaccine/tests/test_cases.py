import pytest

from vaccine.cases import Application
from vaccine.models import Message
from vaccine.testing import AppTester


@pytest.fixture
def tester():
    return AppTester(Application)


@pytest.mark.asyncio
async def test_cases(tester: AppTester):
    await tester.user_input("cases", session=Message.SESSION_EVENT.NEW)
    tester.assert_message(
        "\n".join(
            [
                "*Current Status of Cases of COVID-19 in South Africa*",
                "",
                "*Vaccinations:* 25 619 891",
                "",
                "*Total cases:* 2 968 052",
                "4 373 New cases",
                "",
                "*The breakdown per province of total infections is as follows:*",
                "Eastern Cape - 293 239",
                "Free State - 165 597",
                "Gauteng - 946 863",
                "KwaZulu-Natal - 518 591",
                "Limpopo - 123 710",
                "Mpumalanga - 153 975",
                "North West - 154 290",
                "Northern Cape - 93 343",
                "Western Cape - 518 444",
                "",
                "For the latest news go to twitter.com/HealthZA or "
                "sacoronavirus.co.za/category/press-releases-and-notices/",
                "",
                "------",
                "🆕 Reply *NEWS* for the latest news",
                "📌 Reply *0* for the main *MENU*",
            ]
        )
    )
