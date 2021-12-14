from datetime import datetime
from operator import itemgetter
from os import environ
from urllib.parse import urljoin

import aiohttp

from vaccine.base_application import BaseApplication
from vaccine.states import EndState
from vaccine.utils import TZ_SAST

HEALTHCHECK_API_URL = environ.get(
    "HEALTHCHECK_API_URL",
    "https://evds-healthcheck-django-qa.covid19-k8s.prd-p6t.org/",
)


def format_int(n: int) -> str:
    """
    Formats an integer with a space thousands separator
    """
    return f"{n:,d}".replace(",", " ")


async def get_cases_api_data() -> dict:
    async with aiohttp.ClientSession(
        headers={"User-Agent": "contactndoh-cases"}
    ) as session:
        response = await session.get(
            urljoin(HEALTHCHECK_API_URL, "/v2/covidcases/contactndoh/"),
            raise_for_status=True,
        )
        return await response.json()


class Application(BaseApplication):
    STATE_START = "start_start"

    async def state_start(self):
        data = await get_cases_api_data()
        province_text = "\n".join(
            [
                f"{name}: {format_int(count)}"
                for name, count in sorted(
                    data["latest_provinces"].items(), key=itemgetter(1), reverse=True
                )
            ]
        )

        timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        timestamp = timestamp.astimezone(TZ_SAST)

        text = (
            "*Current Status of Cases of COVID-19 in South Africa*\n"
            "\n"
            "💉 *Vaccinations administered*\n"
            f"{format_int(data['counter']['vaccines'])}\n"
            "\n"
            "🦠 *Cases*\n"
            f"Total: {format_int(data['counter']['positive'])}\n"
            f"New cases: {format_int(data['latest'])}\n"
            f"{format_int(data['counter']['recoveries'])} "
            "Full recoveries (Confirmed Negative)\n"
            "\n"
            "💔 *Deaths*\n"
            f"{format_int(data['counter']['deaths'])}\n"
            "\n"
            "📊 *New cases by province*\n"
            f"{province_text}\n"
            "\n"
            "For the latest news go to twitter.com/HealthZA or "
            "sacoronavirus.co.za/category/press-releases-and-notices/\n"
            "\n"
            "------\n"
            "🆕 Reply *NEWS* for the latest news\n"
            "📌 Reply *0* for the main *MENU*\n"
            "_Source: https://sacoronavirus.co.za "
            f"Updated: {timestamp.strftime('%d/%m/%Y %Hh%M')} "
            "(Errors and omissions excepted)_"
        )
        return EndState(self, text, helper_metadata={"image": data["image"]["image"]})
