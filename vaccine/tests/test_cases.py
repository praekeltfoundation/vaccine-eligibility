import pytest

from vaccine import cases
from vaccine.models import Message
from vaccine.testing import AppTester
from sanic import Sanic, response


@pytest.fixture
def tester():
    return AppTester(cases.Application)


@pytest.fixture
async def nicd_gis_mock(sanic_client):
    Sanic.test_mode = True
    app = Sanic("nicd_gis_mock")
    app.ctx.requests = []

    @app.route("/", methods=["GET"])
    def check(request):
        app.ctx.requests.append(request)
        return response.file_stream(
            "vaccine/tests/nicd_gis_wards.json", mime_type="application/json"
        )

    client = await sanic_client(app)
    url = cases.NICD_GIS_WARD_URL
    cases.NICD_GIS_WARD_URL = f"http://{client.host}:{client.port}/"
    yield client
    cases.NICD_GIS_WARD_URL = url


@pytest.fixture
async def sacoronavirus_powerbi_mock(sanic_client):
    Sanic.test_mode = True
    app = Sanic("sacoronavirus_powerbi_mock")
    app.ctx.requests = []

    @app.route("/", methods=["POST"])
    def check(request):
        app.ctx.requests.append(request)
        return response.file_stream(
            "vaccine/tests/sacoronavirus_powerbi_vaccinations.json",
        )

    client = await sanic_client(app)
    url = cases.SACORONAVIRUS_POWERBI_URL
    cases.SACORONAVIRUS_POWERBI_URL = f"http://{client.host}:{client.port}/"
    yield client
    cases.SACORONAVIRUS_POWERBI_URL = url


@pytest.mark.asyncio
async def test_cases(tester: AppTester, nicd_gis_mock, sacoronavirus_powerbi_mock):
    await tester.user_input("cases", session=Message.SESSION_EVENT.NEW)
    tester.assert_message(
        "\n".join(
            [
                "*Current Status of Cases of COVID-19 in South Africa*",
                "",
                "*Vaccinations:* 25 619 891",
                "",
                "*Total cases:* 2 963 663",
                "2 273 New cases",
                "",
                "*The breakdown per province of total infections is as follows:*",
                "Eastern Cape - 294 283",
                "Free State - 170 227",
                "Gauteng - 943 079",
                "Kwazulu-Natal - 542 083",
                "Limpopo - 120 685",
                "Mpumalanga - 124 710",
                "North West - 156 366",
                "Northern Cape - 94 111",
                "Western Cape - 517 992",
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
