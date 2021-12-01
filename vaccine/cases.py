from collections import defaultdict
from vaccine.base_application import BaseApplication
from vaccine.states import EndState
import aiohttp

NICD_GIS_WARD_URL = (
    "https://gis.nicd.ac.za/hosting/rest/services/WARDS_MN/MapServer/0/query"
)


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
                province_cases[ward["Province"].title()] += ward["Tot_No_of_Cases"]

        province_cases.pop("Pending")
        vaccinations = format_int(25_619_891)
        province_text = "\n".join(
            [
                f"{name} - {format_int(count)}"
                for name, count in sorted(province_cases.items())
            ]
        )
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
