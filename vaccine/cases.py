import json
from collections import defaultdict

import aiohttp

from vaccine.base_application import BaseApplication
from vaccine.states import EndState

NICD_GIS_WARD_URL = (
    "https://gis.nicd.ac.za/hosting/rest/services/WARDS_MN/MapServer/0/query"
)
SACORONAVIRUS_POWERBI_URL = "https://wabi-west-europe-api.analysis.windows.net/public/reports/querydata?synchronous=true"  # noqa: E501


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
            headers={
                "User-Agent": "curl/7.64.1",
                "Accept": "*/*",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            expect100=True,
        )
        response_data = json.loads(await response.read())
        return response_data["results"][0]["result"]["data"]["dsr"]["DS"][0]["PH"][0][
            "DM0"
        ][0]["M0"]


class Application(BaseApplication):
    STATE_START = "start_start"

    async def state_start(self):
        case_data = await get_nicd_gis_ward_data()
        total_cases = 0
        new_cases = 0
        province_cases = defaultdict(lambda: defaultdict(int))
        for ward in case_data["features"]:
            ward = ward["attributes"]
            total_cases += ward["Tot_No_of_Cases"]
            new_cases += ward["Latest"]
            if ward["Province"]:
                province_cases[ward["Province"].title()]["t"] += ward["Tot_No_of_Cases"]
                province_cases[ward["Province"].title()]["l"] += ward["Latest"]

        province_cases.pop("Pending")
        province_text = "\n".join(
            [
                f"{name} - {format_int(count['t'])} (+{format_int(count['l'])})"
                for name, count in sorted(province_cases.items())
            ]
        )

        vaccinations = format_int(await get_sacoronavirus_powerbi_vaccination_data())

        text = (
            "*Current Status of Cases of COVID-19 in South Africa*\n"
            "\n"
            f"*Vaccinations:* {vaccinations}\n"
            "\n"
            f"*Total cases:* {format_int(total_cases)}\n"
            f"{format_int(new_cases)} New cases\n"
            "\n"
            "*The breakdown per province of total infections is as follows:*\n"
            f"{province_text}\n"
            "\n"
            "For the latest news go to twitter.com/HealthZA or "
            "sacoronavirus.co.za/category/press-releases-and-notices/\n"
            "\n"
            "------\n"
            "🆕 Reply *NEWS* for the latest news\n"
            "📌 Reply *0* for the main *MENU*"
        )
        return EndState(self, text)
