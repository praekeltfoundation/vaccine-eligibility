from datetime import datetime
from os import environ
from urllib.parse import urljoin

import aiohttp

from vaccine.base_application import BaseApplication
from vaccine.states import EndState

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

        timestamp = datetime.fromisoformat(data["counter"]["date"]).date()
        timestamp = timestamp.strftime("%d/%m/%Y")

        active = (
            data["counter"]["positive"]
            - data["counter"]["recoveries"]
            - data["counter"]["deaths"]
        )

        daily_cases = (
            f"Daily: {format_int(data['daily']['positive'])}\n"
            if "daily" in data
            else ""
        )
        daily_deaths = (
            f"Daily: {format_int(data['daily']['deaths'])}\n" if "daily" in data else ""
        )

        text = (
            "*Current Status of Cases of COVID-19 in South Africa*\n"
            f"_Reported at {timestamp}_\n"
            "\n"
            "💉 *Vaccinations administered*\n"
            f"{format_int(data['counter']['vaccines'])}\n"
            "\n"
            "🦠 *Cases*\n"
            f"Total: {format_int(data['counter']['positive'])}\n"
            f"{daily_cases}"
            f"Active cases: {format_int(active)}\n"
            f"{format_int(data['counter']['recoveries'])} "
            "Full recoveries (Confirmed Negative)\n"
            "\n"
            "💔 *Deaths*\n"
            f"Total: {format_int(data['counter']['deaths'])}\n"
            f"{daily_deaths}"
            "\n"
            "------\n"
            "🆕 Reply *NEWS* for the latest news\n"
            "📌 Reply *0* for the main *MENU*\n"
            "_Source: https://sacoronavirus.co.za_"
        )
        return EndState(self, text, helper_metadata={"image": data["image"]["image"]})
