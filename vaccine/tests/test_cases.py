import pytest
from sanic import Sanic, response

from vaccine import cases
from vaccine.models import Message
from vaccine.testing import AppTester


@pytest.fixture
def tester():
    return AppTester(cases.Application)


@pytest.fixture
async def healthcheck_mock(sanic_client):
    Sanic.test_mode = True
    app = Sanic("healthcheck_mock")
    app.ctx.requests = []

    @app.route("/v2/covidcases/contactndoh", methods=["GET"])
    def contactndoh(request):
        app.ctx.requests.append(request)
        return response.json(
            {
                "image": {
                    "id": 1,
                    "url": "https://sacoronavirus.b-cdn.net/wp-content/uploads/2021/12/13-dec-map.jpg",  # noqa: E501
                    "image": "https://s3.af-south-1.amazonaws.com/evds-healthcheck-qa-django/13-dec-map.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAUPEZAKIUSYC4ZVEQ%2F20211214%2Faf-south-1%2Fs3%2Faws4_request&X-Amz-Date=20211214T135744Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=a7a7687c3cfb59501502c185be38a14f10c1435772e1ddf83267f09639baefdb",  # noqa: E501
                    "image_size": 107854,
                    "image_width": 960,
                    "image_height": 720,
                    "date": "2021-12-13",
                    "created_at": "2021-12-14T15:24:52.909491+02:00",
                    "updated_at": "2021-12-14T15:24:52.909539+02:00",
                },
                "counter": {
                    "id": 1,
                    "tests": 20283906,
                    "positive": 3180785,
                    "recoveries": 2913297,
                    "deaths": 90148,
                    "vaccines": 27188606,
                    "date": "2021-12-14",
                    "created_at": "2021-12-14T15:00:48.861565+02:00",
                    "updated_at": "2021-12-14T15:00:48.861582+02:00",
                },
                "timestamp": "2021-12-14T13:00:48.565583Z",
                "latest": 0,
                "latest_provinces": {
                    "Western Cape": 0,
                    "Eastern Cape": 0,
                    "Northern Cape": 0,
                    "Free State": 0,
                    "Kwazulu-Natal": 0,
                    "North West": 0,
                    "Gauteng": 0,
                    "Mpumalanga": 0,
                    "Limpopo": 0,
                },
            }
        )

    client = await sanic_client(app)
    url = cases.HEALTHCHECK_API_URL
    cases.HEALTHCHECK_API_URL = f"http://{client.host}:{client.port}/"
    yield client
    cases.HEALTHCHECK_API_URL = url


@pytest.mark.asyncio
async def test_cases(tester: AppTester, healthcheck_mock):
    await tester.user_input("cases", session=Message.SESSION_EVENT.NEW)
    tester.assert_message(
        "\n".join(
            [
                "*Current Status of Cases of COVID-19 in South Africa*",
                "",
                "💉 *Vaccinations administered*",
                "27 188 606",
                "",
                "🦠 *Cases*",
                "Total: 3 180 785",
                "New cases: 0",
                "2 913 297 Full recoveries (Confirmed Negative)",
                "",
                "💔 *Deaths*",
                "90 148",
                "",
                "📊 *New cases by province*",
                "Western Cape: 0",
                "Eastern Cape: 0",
                "Northern Cape: 0",
                "Free State: 0",
                "Kwazulu-Natal: 0",
                "North West: 0",
                "Gauteng: 0",
                "Mpumalanga: 0",
                "Limpopo: 0",
                "",
                "For the latest news go to twitter.com/HealthZA or "
                "sacoronavirus.co.za/category/press-releases-and-notices/",
                "",
                "------",
                "🆕 Reply *NEWS* for the latest news",
                "📌 Reply *0* for the main *MENU*",
                "_Source: https://sacoronavirus.co.za Updated: 14/12/2021 15h00 "
                "(Errors and omissions excepted)_",
            ]
        )
    )
    assert (
        tester.application.messages[0].helper_metadata["image"]
        == "https://s3.af-south-1.amazonaws.com/evds-healthcheck-qa-django/13-dec-map.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAUPEZAKIUSYC4ZVEQ%2F20211214%2Faf-south-1%2Fs3%2Faws4_request&X-Amz-Date=20211214T135744Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=a7a7687c3cfb59501502c185be38a14f10c1435772e1ddf83267f09639baefdb"  # noqa: E501
    )
