import pytest
from sanic import Sanic, response

from vaccine import cases
from vaccine.models import Message
from vaccine.testing import AppTester


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


@pytest.fixture
async def sacoronavirus_mock(sanic_client):
    Sanic.test_mode = True
    app = Sanic("sacoronavirus_mock")
    app.ctx.requests = []

    @app.route("/", methods=["GET"])
    def homepage(request):
        app.ctx.requests.append(request)
        return response.file_stream("vaccine/tests/sacoronavirus.html")

    @app.route("/category/daily-cases/", methods=["GET"])
    def check(request):
        app.ctx.requests.append(request)
        return response.file_stream("vaccine/tests/sacoronavirus_cases.html")

    client = await sanic_client(app)
    img_url = cases.CASES_IMAGE_URL
    homepage_url = cases.SACORONAVIRUS_URL
    cases.CASES_IMAGE_URL = f"http://{client.host}:{client.port}/category/daily-cases/"
    cases.SACORONAVIRUS_URL = f"http://{client.host}:{client.port}/"
    yield client
    cases.CASES_IMAGE_URL = img_url
    cases.SACORONAVIRUS_URL = homepage_url


@pytest.mark.asyncio
async def test_cases(
    tester: AppTester, nicd_gis_mock, sacoronavirus_powerbi_mock, sacoronavirus_mock
):
    await tester.user_input("cases", session=Message.SESSION_EVENT.NEW)
    tester.assert_message(
        "\n".join(
            [
                "*Current Status of Cases of COVID-19 in South Africa*",
                "",
                "💉 *Vaccinations administered*",
                "25 619 891",
                "",
                "🦠 *Cases*",
                "Total: 2 963 663",
                "New cases: 2 273",
                "2 850 905 Full recoveries (Confirmed Negative)",
                "",
                "💔 *Deaths*",
                "89 915",
                "",
                "📊 *New cases by province*",
                "Gauteng: 1 895",
                "Western Cape: 119",
                "Kwazulu-Natal: 74",
                "North West: 56",
                "Mpumalanga: 49",
                "Limpopo: 33",
                "Free State: 27",
                "Eastern Cape: 10",
                "Northern Cape: 10",
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
    assert (
        tester.application.messages[0].helper_metadata["image"]
        == "https://sacoronavirus.b-cdn.net/wp-content/uploads/2021/12/01-dec-map.jpg"
    )
