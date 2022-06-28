import pytest
from sanic import Sanic, response

from vaccine.testing import AppTester
from yal import config
from yal.main import Application


@pytest.fixture
def tester():
    return AppTester(Application)


@pytest.fixture
async def servicefinder_mock(sanic_client):
    Sanic.test_mode = True
    app = Sanic("mock_servicefinder")
    app.requests = []

    # TODO: update this when we get the details from Devlin
    @app.route("/categories", methods=["GET"])
    def callback_get(request):
        app.requests.append(request)
        return response.json(
            {
                "categories": {"1": "category 1", "2": "category 2", "3": "category 3"},
            }
        )

    # TODO: update this when we get the details from Devlin
    @app.route("/facilities", methods=["POST"])
    def callback_post(request):
        app.requests.append(request)
        return response.json(
            {
                "facilities": [
                    "facility 1",
                    "facility 2",
                    "facility 3",
                ]
            }
        )

    client = await sanic_client(app)
    url = config.SERVICEFINDER_URL
    config.SERVICEFINDER_URL = f"http://{client.host}:{client.port}"
    yield client
    config.SERVICEFINDER_URL = url


@pytest.fixture
async def google_api_mock(sanic_client):
    Sanic.test_mode = True
    app = Sanic("mock_google_api")
    app.requests = []
    app.api_errormax = 0
    app.api_errors = 0
    app.status = "OK"

    @app.route("/maps/api/place/autocomplete/json", methods=["GET"])
    def valid_city(request):
        app.requests.append(request)
        if app.api_errormax:
            if app.api_errors < app.api_errormax:
                app.api_errors += 1
                return response.json({}, status=500)
        if app.status == "OK":
            data = {
                "status": "OK",
                "predictions": [
                    {
                        "description": "Cape Town, South Africa",
                        "place_id": "ChIJD7fiBh9u5kcRYJSMaMOCCwQ",
                    }
                ],
            }
        else:
            data = {"status": app.status}
        return response.json(data, status=200)

    @app.route("/maps/api/place/details/json", methods=["GET"])
    def details_lookup(request):
        app.requests.append(request)
        if app.api_errormax:
            if app.api_errors < app.api_errormax:
                app.api_errors += 1
                return response.json({}, status=500)
        if app.status == "OK":
            data = {
                "status": "OK",
                "result": {
                    "geometry": {"location": {"lat": -3.866_651, "lng": 51.195_827}}
                },
            }
        else:
            data = {"status": app.status}
        return response.json(data, status=200)

    client = await sanic_client(app)
    config.GOOGLE_PLACES_KEY = "TEST-KEY"
    url = config.GOOGLE_PLACES_URL
    config.GOOGLE_PLACES_URL = f"http://{client.host}:{client.port}"
    yield client
    config.GOOGLE_PLACES_URL = url


@pytest.mark.asyncio
async def test_state_servicefinder_start_no_address(tester: AppTester):
    tester.setup_state("state_servicefinder_start")
    await tester.user_input("1")
    tester.assert_state("state_location")


@pytest.mark.asyncio
async def test_state_servicefinder_start_existing_address(
    tester: AppTester, google_api_mock
):
    tester.setup_state("state_servicefinder_start")

    tester.user.metadata["province"] = "FS"
    tester.user.metadata["suburb"] = "cape town"
    tester.user.metadata["street_name"] = "high level"
    tester.user.metadata["street_number"] = "99"

    await tester.user_input("1")
    tester.assert_state("state_confirm_existing_address")

    assert [r.path for r in google_api_mock.app.requests] == [
        "/maps/api/place/autocomplete/json"
    ]

    tester.assert_metadata("place_id", "ChIJD7fiBh9u5kcRYJSMaMOCCwQ")


@pytest.mark.asyncio
async def test_state_confirm_existing_address_yes(
    tester: AppTester, servicefinder_mock, google_api_mock
):
    tester.setup_state("state_confirm_existing_address")

    tester.user.metadata["place_id"] = "ChIJD7fiBh9u5kcRYJSMaMOCCwQ"
    tester.user.metadata["google_session_token"] = "123"

    await tester.user_input("1")

    tester.assert_state("state_category")

    question = "\n".join(
        [
            "🏥 Find Clinics and Services",
            "*Get help near you*",
            "-----",
            "",
            "🙍🏾‍♀️ *Choose an option from the list:*",
            "",
            "1 - category 1",
            "2 - category 2",
            "3 - category 3",
            "",
            "*OR*",
            "",
            "4 - Talk to somebody",
            "",
            "-----",
            "*Or reply:*",
            "*0* - 🏠 Back to Main *MENU*",
            "*#* - 🆘 Get *HELP*",
        ]
    )

    tester.assert_message(question)

    assert [r.path for r in servicefinder_mock.app.requests] == ["/categories"]
    assert [r.path for r in google_api_mock.app.requests] == [
        "/maps/api/place/details/json"
    ]

    tester.assert_metadata("latitude", -3.866651)
    tester.assert_metadata("longitude", 51.195827)


@pytest.mark.asyncio
async def test_state_confirm_existing_address_no(tester: AppTester):
    tester.setup_state("state_confirm_existing_address")

    await tester.user_input("2")

    tester.assert_state("state_location")


@pytest.mark.asyncio
async def test_state_category(tester: AppTester, servicefinder_mock):
    tester.setup_state("state_category")

    tester.user.metadata["categories"] = {
        "1": "category 1",
        "2": "category 2",
        "3": "category 3",
    }
    tester.user.metadata["latitude"] = 123
    tester.user.metadata["longitude"] = 123

    await tester.user_input("2")

    tester.assert_state("state_start")
    assert [r.path for r in servicefinder_mock.app.requests] == ["/facilities"]


@pytest.mark.asyncio
async def test_state_category_talk(tester: AppTester):
    tester.setup_state("state_category")

    tester.user.metadata["categories"] = {
        "1": "category 1",
        "2": "category 2",
        "3": "category 3",
    }

    await tester.user_input("4")

    tester.assert_state("state_in_hours")


@pytest.mark.asyncio
async def test_state_location(tester: AppTester, servicefinder_mock):
    tester.setup_state("state_location")

    await tester.user_input(
        "test location",
        transport_metadata={
            "msg": {"location": {"longitude": 12.34, "latitude": 56.78}}
        },
    )
    tester.assert_state("state_category")

    tester.assert_metadata("latitude", 56.78)
    tester.assert_metadata("longitude", 12.34)


@pytest.mark.asyncio
async def test_state_location_invalid(tester: AppTester):
    tester.setup_state("state_location")

    await tester.user_input("invalid location")
    tester.assert_state("state_location")
