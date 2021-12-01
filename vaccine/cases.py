from vaccine.base_application import BaseApplication
from vaccine.states import EndState


def format_int(n: int) -> str:
    """
    Formats an integer with a space thousands separator
    """
    return f"{n:,d}".replace(",", " ")


class Application(BaseApplication):
    STATE_START = "start_start"

    async def state_start(self):
        vaccinations = format_int(25_619_891)
        total_cases = format_int(2_968_052)
        new_cases = format_int(4_373)
        province_cases = (
            ("Eastern Cape", format_int(293_239)),
            ("Free State", format_int(165_597)),
            ("Gauteng", format_int(946_863)),
            ("KwaZulu-Natal", format_int(518_591)),
            ("Limpopo", format_int(123_710)),
            ("Mpumalanga", format_int(153_975)),
            ("North West", format_int(154_290)),
            ("Northern Cape", format_int(93_343)),
            ("Western Cape", format_int(518_444)),
        )
        province_text = "\n".join(
            [f"{name} - {count}" for name, count in province_cases]
        )
        text = (
            "*Current Status of Cases of COVID-19 in South Africa*\n"
            "\n"
            f"*Vaccinations:* {vaccinations}\n"
            "\n"
            f"*Total cases:* {total_cases}\n"
            f"{new_cases} New cases\n"
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
