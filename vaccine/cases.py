import json
from collections import defaultdict
from operator import itemgetter
from typing import Tuple

import aiohttp
from bs4 import BeautifulSoup

from vaccine.base_application import BaseApplication
from vaccine.states import EndState

NICD_GIS_WARD_URL = (
    "https://gis.nicd.ac.za/hosting/rest/services/WARDS_MN/MapServer/0/query"
)
SACORONAVIRUS_POWERBI_URL = "https://wabi-west-europe-api.analysis.windows.net/public/reports/querydata?synchronous=true"  # noqa: E501
CASES_IMAGE_URL = "https://sacoronavirus.co.za/category/daily-cases/"
SACORONAVIRUS_URL = "https://sacoronavirus.co.za/"


def format_int(n: int) -> str:
    """
    Formats an integer with a space thousands separator
    """
    return f"{n:,d}".replace(",", " ")


async def get_nicd_gis_ward_data() -> dict:
    async with aiohttp.ClientSession(
        headers={"User-Agent": "contactndoh-cases"}
    ) as session:
        response = await session.get(
            NICD_GIS_WARD_URL,
            params={
                "where": "1=1",
                "outFields": "Province,Latest,Tot_No_of_Cases",
                "returnGeometry": "false",
                "f": "json",
            },
            raise_for_status=True,
        )
        return await response.json()


async def get_sacoronavirus_powerbi_vaccination_data() -> int:
    # This is an undocumented API, and will return a 401 if changed slightly
    async with aiohttp.ClientSession() as session:
        with open("vaccine/sacoronavirus_powerbi_request_body", "rb") as f:
            body = f.read()
        response = await session.post(
            SACORONAVIRUS_POWERBI_URL,
            data=body,
            raise_for_status=True,
            headers={"User-Agent": "contactndoh-cases"},
            expect100=True,
        )
        response_data = json.loads(await response.read())
        return response_data["results"][0]["result"]["data"]["dsr"]["DS"][0]["PH"][0][
            "DM0"
        ][0]["M0"]


async def get_daily_cases_image_url() -> str:
    async with aiohttp.ClientSession(
        headers={"User-Agent": "contactndoh-cases"}
    ) as session:
        response = await session.get(CASES_IMAGE_URL, raise_for_status=True)
        soup = BeautifulSoup(await response.text(), "html.parser")
        return soup.main.img["src"]


async def get_deaths_recoveries() -> Tuple[int, int]:
    async with aiohttp.ClientSession(
        headers={"User-Agent": "contactndoh-cases"}
    ) as session:
        response = await session.get(SACORONAVIRUS_URL, raise_for_status=True)
        soup = BeautifulSoup(await response.text(), "html.parser")
        counters = soup.find("div", class_="counters-box")
        deaths, recoveries = 0, 0
        for counter in counters.find_all("div", "counter-box-container"):
            name = counter.find("div", "counter-box-content").string
            if "death" in name.lower():
                deaths = int(counter.span["data-value"])
            elif "recover" in name.lower():
                recoveries = int(counter.span["data-value"])
        return deaths, recoveries


class Application(BaseApplication):
    STATE_START = "start_start"

    async def state_start(self):
        case_data = await get_nicd_gis_ward_data()
        total_cases = 0
        new_cases = 0
        province_cases = defaultdict(int)
        for ward in case_data["features"]:
            ward = ward["attributes"]
            total_cases += ward["Tot_No_of_Cases"]
            new_cases += ward["Latest"]
            if ward["Province"]:
                province_cases[ward["Province"].title()] += ward["Latest"]

        province_cases.pop("Pending")
        province_text = "\n".join(
            [
                f"{name}: {format_int(count)}"
                for name, count in sorted(
                    province_cases.items(), key=itemgetter(1), reverse=True
                )
            ]
        )

        vaccinations = await get_sacoronavirus_powerbi_vaccination_data()

        image_url = await get_daily_cases_image_url()

        deaths, recoveries = await get_deaths_recoveries()

        text = (
            "*Current Status of Cases of COVID-19 in South Africa*\n"
            "\n"
            "💉 *Vaccinations administered*\n"
            f"{format_int(vaccinations)}\n"
            "\n"
            "🦠 *Cases*\n"
            f"Total: {format_int(total_cases)}\n"
            f"New cases: {format_int(new_cases)}\n"
            f"{format_int(recoveries)} Full recoveries (Confirmed Negative)\n"
            "\n"
            "💔 *Deaths*\n"
            f"{format_int(deaths)}\n"
            "\n"
            "📊 *New cases by province*\n"
            f"{province_text}\n"
            "\n"
            "For the latest news go to twitter.com/HealthZA or "
            "sacoronavirus.co.za/category/press-releases-and-notices/\n"
            "\n"
            "------\n"
            "🆕 Reply *NEWS* for the latest news\n"
            "📌 Reply *0* for the main *MENU*"
        )
        return EndState(self, text, helper_metadata={"image": image_url})
