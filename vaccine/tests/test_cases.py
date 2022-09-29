import pytest
from sanic import Sanic, response

from vaccine import cases
from vaccine.models import Message
from vaccine.testing import AppTester, run_sanic


@pytest.fixture
def tester():
    return AppTester(cases.Application)


@pytest.fixture
async def healthcheck_mock():
    Sanic.test_mode = True
    app = Sanic("healthcheck_mock")

    @app.route("/v2/covidcases/contactndoh", methods=["GET"])
    def contactndoh(request):
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
                "daily": {
                    "tests": 50377,
                    "positive": 15465,
                    "recoveries": 18224,
                    "deaths": 3,
                    "vaccines": 6296,
                },
            }
        )

    async with run_sanic(app) as server:
        url = cases.HEALTHCHECK_API_URL
        cases.HEALTHCHECK_API_URL = f"http://{server.host}:{server.port}/"
        yield server
        cases.HEALTHCHECK_API_URL = url


@pytest.mark.asyncio
async def test_cases(tester: AppTester, healthcheck_mock):
    await tester.user_input("cases", session=Message.SESSION_EVENT.NEW)
    tester.assert_message(
        "\n".join(
            [
                "*Current Status of Cases of COVID-19 in South Africa*",
                "_Reported at 14/12/2021_",
                "",
                "🦠 *Cases*",
                "Total: 3 180 785",
                "New cases: 15 465",
                "Active cases: 177 340",
                "2 913 297 Full recoveries (Confirmed Negative)",
                "",
                "💉 *Vaccinations administered*",
                "27 188 606",
                "",
                "🔬 *Tests conducted*",
                "Total: 20 283 906",
                "Daily: 50 377",
                "",
                "💔 *Deaths*",
                "Total: 90 148",
                "Daily: 3",
                "",
                "------",
                "🆕 Reply *NEWS* for the latest news",
                "📌 Reply *0* for the main *MENU*",
                "_Source: https://sacoronavirus.co.za_",
            ]
        )
    )
    assert (
        tester.application.messages[0].helper_metadata["image"]
        == "https://s3.af-south-1.amazonaws.com/evds-healthcheck-qa-django/13-dec-map.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAUPEZAKIUSYC4ZVEQ%2F20211214%2Faf-south-1%2Fs3%2Faws4_request&X-Amz-Date=20211214T135744Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=a7a7687c3cfb59501502c185be38a14f10c1435772e1ddf83267f09639baefdb"  # noqa: E501
    )
