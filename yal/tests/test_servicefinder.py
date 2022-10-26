import json
from collections import defaultdict
from datetime import datetime
from typing import Dict, List
from unittest import mock

import pytest
from sanic import Sanic, response

from vaccine.testing import AppTester, TState, run_sanic
from yal import config
from yal.main import Application
from yal.utils import BACK_TO_MAIN, GET_HELP


@pytest.fixture
def tester():
    return AppTester(Application)


with open("yal/tests/servicefinder_categories.json") as f:
    CATEGORIES: List[Dict] = json.loads(f.read())


def get_processed_categories():
    categories: Dict[str, Dict] = defaultdict(dict)
    for c in CATEGORIES:
        parent = c["parent"] or "root"
        categories[parent][c["_id"]] = c["name"]
    return dict(categories)


FACILITIES: List[Dict] = [
    {
        "location": {"type": "Point", "coordinates": [28.0151783, -26.1031026]},
        "_id": "62ddcc71981c9d7ba465e67e",
        "name": "South West Gauteng TVET College - Technisa Campus",
        "description": "Technical and vocational education and training",
        "category": "62dd91904d7d919468144edf",
        "serviceType": "Education",
        "telephoneNumber": "825 797 593",
        "emailAddress": "tech@swgc.co.za",
        "fullAddress": "Huguenot Avenue & Main Street",
        "createdBy": "5eb125d604a3eb3b4859a022",
        "createdAt": 1658702961660,
        "updatedAt": 1658702961660,
        "__v": 0,
    },
    {
        "location": {"type": "Point", "coordinates": [27.8677946, -26.1404831]},
        "_id": "62ddcc6f981c9d7ba465e661",
        "name": "South West Gauteng TVET College - Roodepoort West Campus",
        "description": "Technical and vocational education and training",
        "category": "62dd91904d7d919468144edf",
        "serviceType": "Education",
        "telephoneNumber": "",
        "emailAddress": "",
        "fullAddress": "Pheasant St Roodepoort 1724",
        "createdBy": "5eb125d604a3eb3b4859a022",
        "createdAt": 1658702959684,
        "updatedAt": 1658702959684,
        "__v": 0,
    },
]


@pytest.fixture
async def servicefinder_mock():
    Sanic.test_mode = True
    app = Sanic("mock_servicefinder")
    tstate = TState()

    @app.route("/api/categories", methods=["GET"])
    def callback_get(request):
        tstate.requests.append(request)
        return response.json(CATEGORIES)

    @app.route("/api/locations", methods=["GET"])
    def callback_post(request):
        tstate.requests.append(request)
        if request.args.get("category") == "62dd86d24d7d919468144ed5":
            return response.json([])
        return response.json(FACILITIES)

    async with run_sanic(app) as server:
        url = config.SERVICEFINDER_URL
        config.SERVICEFINDER_URL = f"http://{server.host}:{server.port}"
        server.tstate = tstate
        yield server
        config.SERVICEFINDER_URL = url


@pytest.fixture
async def google_api_mock():
    Sanic.test_mode = True
    app = Sanic("mock_google_api")
    tstate = TState()
    tstate.status = "OK"

    @app.route("/maps/api/place/autocomplete/json", methods=["GET"])
    def valid_city(request):
        tstate.requests.append(request)
        if tstate.errormax:
            if tstate.errors < tstate.errormax:
                tstate.errors += 1
                return response.json({}, status=500)
        if tstate.status == "OK":
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
            data = {"status": tstate.status}
        return response.json(data, status=200)

    @app.route("/maps/api/geocode/json", methods=["GET"])
    def desc_from_pin(request):
        tstate.requests.append(request)
        if tstate.errormax:
            if tstate.errors < tstate.errormax:
                tstate.errors += 1
                return response.json({}, status=500)
        if tstate.status == "OK":
            data = {
                "status": "OK",
                "results": [
                    {
                        "formatted_address": "277 Bedford Avenue, Brooklyn, NY 11211, "
                        "USA",
                        "place_id": "ChIJd8BlQ2BZwokRAFUEcm_qrcA",
                    }
                ],
            }
        else:
            data = {"status": tstate.status}
        return response.json(data, status=200)

    @app.route("/maps/api/place/details/json", methods=["GET"])
    def details_lookup(request):
        tstate.requests.append(request)
        if tstate.errormax:
            if tstate.errors < tstate.errormax:
                tstate.errors += 1
                return response.json({}, status=500)
        if tstate.status == "OK":
            data = {
                "status": "OK",
                "result": {
                    "geometry": {"location": {"lat": -3.866_651, "lng": 51.195_827}}
                },
            }
        else:
            data = {"status": tstate.status}
        return response.json(data, status=200)

    async with run_sanic(app) as server:
        config.GOOGLE_PLACES_KEY = "TEST-KEY"
        url = config.GOOGLE_PLACES_URL
        config.GOOGLE_PLACES_URL = f"http://{server.host}:{server.port}"
        server.tstate = tstate
        yield server
        config.GOOGLE_PLACES_URL = url


@pytest.fixture
async def rapidpro_mock():
    Sanic.test_mode = True
    app = Sanic("mock_rapidpro")
    tstate = TState()

    @app.route("/api/v2/contacts.json", methods=["POST"])
    def update_contact(request):
        tstate.requests.append(request)
        return response.json({}, status=200)

    @app.route("/api/v2/contacts.json", methods=["GET"])
    def get_contact(request):
        return response.json({"results": []})

    async with run_sanic(app) as server:
        config.RAPIDPRO_URL = f"http://{server.host}:{server.port}"
        config.RAPIDPRO_TOKEN = "testtoken"
        server.tstate = tstate
        yield server


@pytest.mark.asyncio
async def test_state_servicefinder_start_no_address(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_servicefinder_start")
    await tester.user_input("1")
    tester.assert_state("state_location")

    tester.assert_message(
        "\n".join(
            [
                "NEED HELP / Find clinics and services /📍*Location*",
                "-----",
                "",
                "To be able to suggest youth-friendly clinics and FREE services "
                "near you, I need to know where you live.",
                "",
                "🤖*(You can share your location by sending me a pin (📍). To do this:*",
                "",
                "1️⃣*Tap the + _(plus)_* button or the 📎*_(paperclip)_* button "
                "below.",
                "",
                "2️⃣Next, tap *Location* then select *Send Your Current Location.*",
                "",
                "_You can also use the *search 🔎 at the top of the screen, to type "
                "in the address or area* you want to share._",
                "",
                "-----",
                "*Or reply:*",
                BACK_TO_MAIN,
                GET_HELP,
            ]
        )
    )


@pytest.mark.asyncio
async def test_state_servicefinder_start_existing_address(
    tester: AppTester, google_api_mock, rapidpro_mock
):
    tester.setup_state("state_servicefinder_start")

    tester.user.metadata["location_description"] = "99 high level, cape town, FS"
    tester.user.metadata["longitude"] = -73.9612889
    tester.user.metadata["latitude"] = 40.714232

    await tester.user_input("1")
    tester.assert_state("state_confirm_existing_address")

    [msg1, msg2] = tester.fake_worker.outbound_messages
    assert msg1.content == "🤖 *Okay, I just need to confirm some details...*"
    assert msg2.content == "\n".join(
        [
            "🏥 Find Clinics and Services",
            "*Get help near you*",
            "-----",
            "🤖 *The address I have for you right now is:*",
            "",
            "99 high level, cape town, FS",
            "-----",
            "*Or reply:*",
            BACK_TO_MAIN,
            GET_HELP,
        ]
    )

    tester.assert_message(
        "\n".join(
            [
                "🏥 Find Clinics and Services",
                "*Get help near you*",
                "-----",
                "",
                "🤖 *Would you like me to recommend helpful services close to "
                "this address?*",
                "",
                "*1* - Yes please",
                "*2* - Use a different location",
                "",
                "-----",
                "*Or reply:*",
                BACK_TO_MAIN,
                GET_HELP,
            ]
        )
    )

    assert [r.path for r in google_api_mock.tstate.requests] == []


@pytest.mark.asyncio
async def test_state_confirm_existing_address_yes(
    tester: AppTester, servicefinder_mock, google_api_mock, rapidpro_mock
):
    tester.setup_state("state_confirm_existing_address")
    tester.user.metadata["servicefinder_breadcrumb"] = "*Get help near you*"

    await tester.user_input("1")

    tester.assert_state("state_category")

    question = "\n".join(
        [
            "🏥 Find Clinics and Services",
            "*Get help near you*",
            "-----",
            "",
            "🤖 *Choose an option from the list:*",
            "",
            "*1* - Clinics & Hospitals",
            "*2* - HIV Prevention",
            "*3* - Family Planning",
            "*4* - Sexual Violence Support",
            "*5* - Educational Opportunities",
            "*6* - Talk to Somebody",
            "*7* - Get Support",
            "",
            "*OR*",
            "",
            "*8* - Talk to somebody",
            "",
            "-----",
            "*Or reply:*",
            BACK_TO_MAIN,
            GET_HELP,
        ]
    )

    tester.assert_message(question)

    assert [r.path for r in servicefinder_mock.tstate.requests] == ["/api/categories"]
    assert [r.path for r in google_api_mock.tstate.requests] == []


@pytest.mark.asyncio
async def test_state_confirm_existing_address_no(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_confirm_existing_address")
    tester.user.metadata["servicefinder_breadcrumb"] = "*Get help near you*"

    await tester.user_input("2")

    tester.assert_state("state_location")

    [msg1] = tester.fake_worker.outbound_messages
    assert msg1.content == "🤖 *Sure. Where would you like me to look?*"

    tester.assert_message(
        "\n".join(
            [
                "🏥 Find Clinics and Services",
                "*Get help near you*",
                "-----",
                "",
                "🤖*You can change your location by sending me a pin (📍)."
                " To do this:*",
                "",
                "1️⃣Tap the *+ _(plus)_* button or the 📎*_(paperclip)_* button "
                "below.",
                "",
                "2️⃣Next, tap *Location* then select *Send Your Current Location.*",
                "",
                "_You can also use the *search 🔎 at the top of the screen, to type "
                "in the address or area* you want to share._",
                "",
                "-----",
                "*Or reply:*",
                BACK_TO_MAIN,
                GET_HELP,
            ]
        )
    )


@pytest.mark.asyncio
async def test_state_category_sub(tester: AppTester, servicefinder_mock, rapidpro_mock):
    tester.setup_state("state_category")

    tester.user.metadata["categories"] = get_processed_categories()
    tester.user.metadata["parent_category"] = "root"
    tester.user.metadata["servicefinder_breadcrumb"] = "*Get help near you*"

    await tester.user_input("2")

    tester.assert_state("state_category")
    question = "\n".join(
        [
            "🏥 Find Clinics and Services",
            "Get help near you / *HIV Prevention*",
            "-----",
            "",
            "🤖 *Choose an option from the list:*",
            "",
            "*1* - Where to get PrEP",
            "*2* - Where to get PEP",
            "",
            "*OR*",
            "",
            "*3* - Talk to somebody",
            "",
            "-----",
            "*Or reply:*",
            BACK_TO_MAIN,
            GET_HELP,
        ]
    )

    tester.assert_message(question)


@pytest.mark.asyncio
@mock.patch("yal.servicefinder.utils.get_current_datetime")
async def test_state_category(
    get_current_datetime, tester: AppTester, servicefinder_mock, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 3, 4, 5, 6, 7)
    tester.setup_state("state_category")

    tester.user.metadata["categories"] = get_processed_categories()
    tester.user.metadata["servicefinder_breadcrumb"] = "*Get help near you*"
    tester.user.metadata["parent_category"] = "62dd86c14d7d919468144ed4"
    tester.user.metadata["latitude"] = -26.2031026
    tester.user.metadata["longitude"] = 28.0251783

    await tester.user_input("2")

    tester.assert_state("state_start")

    question = "\n".join(
        [
            "🏥 *Find Clinics and Services*",
            "Where to get PEP near you",
            "-----",
            "",
            "1️⃣ *South West Gauteng TVET College - Technisa Campus*",
            "📍 Huguenot Avenue & Main Street",
            "📞 825 797 593",
            "🦶 11 km",
            "https://www.google.com/maps/place/-26.1031026,28.0151783",
            "----",
            "",
            "2️⃣ *South West Gauteng TVET College - Roodepoort West Campus*",
            "📍 Pheasant St Roodepoort 1724",
            "🦶 17 km",
            "https://www.google.com/maps/place/-26.1404831,27.8677946",
            "-----",
            "Once you've chosen a facility, *tap on the link* to see the quickest "
            "route from where you are to the facility from your maps or to send them "
            "an email.",
            "",
            "-----",
            "*Or reply:*",
            BACK_TO_MAIN,
            GET_HELP,
        ]
    )

    tester.assert_message(question)

    assert [r.path for r in servicefinder_mock.tstate.requests] == ["/api/locations"]

    [request] = rapidpro_mock.tstate.requests
    assert request.json["fields"] == {
        "feedback_timestamp": "2022-03-04T05:16:07",
        "feedback_type": "servicefinder",
    }


@pytest.mark.asyncio
async def test_state_category_no_facilities(
    tester: AppTester, servicefinder_mock, rapidpro_mock
):
    tester.setup_state("state_category")

    tester.user.metadata["categories"] = get_processed_categories()
    tester.user.metadata["servicefinder_breadcrumb"] = "*Get help near you*"
    tester.user.metadata["parent_category"] = "62dd86c14d7d919468144ed4"
    tester.user.metadata["latitude"] = -26.2031026
    tester.user.metadata["longitude"] = 28.0251783

    await tester.user_input("1")

    tester.assert_state("state_no_facilities_found")

    question = "\n".join(
        [
            "🤖 *Sorry, we can't find any services near you.*",
            "",
            "But don't worry, here are some other options you can try:",
            "",
            "1. Try another location",
            "2. Try another service",
        ]
    )

    tester.assert_message(question)

    assert [r.path for r in servicefinder_mock.tstate.requests] == ["/api/locations"]

    tester.assert_metadata("parent_category", "root")
    tester.assert_metadata("servicefinder_breadcrumb", "*Get help near you*")


@pytest.mark.asyncio
@mock.patch("yal.pleasecallme.get_current_datetime")
async def test_state_category_talk(get_current_datetime, tester: AppTester):
    get_current_datetime.return_value = datetime(2022, 6, 20, 17, 30)
    tester.setup_state("state_category")

    tester.user.metadata["categories"] = get_processed_categories()
    tester.user.metadata["servicefinder_breadcrumb"] = "*Get help near you*"
    await tester.user_input("8")

    tester.assert_state("state_in_hours")
    tester.assert_metadata("parent_category", "root")
    tester.assert_metadata("servicefinder_breadcrumb", "*Get help near you*")


@pytest.mark.asyncio
async def test_state_location(
    tester: AppTester, servicefinder_mock, google_api_mock, rapidpro_mock
):
    tester.setup_state("state_location")
    tester.user.metadata["servicefinder_breadcrumb"] = "*Get help near you*"
    tester.user.metadata["google_session_token"] = "123"

    await tester.user_input(
        "test location",
        transport_metadata={
            "message": {"location": {"longitude": 12.34, "latitude": 56.78}}
        },
    )
    tester.assert_state("state_category")

    tester.assert_metadata("latitude", 56.78)
    tester.assert_metadata("longitude", 12.34)
    tester.assert_metadata("place_id", "ChIJd8BlQ2BZwokRAFUEcm_qrcA")
    tester.assert_metadata(
        "location_description", "277 Bedford Avenue, Brooklyn, NY 11211, USA"
    )

    assert [r.path for r in google_api_mock.tstate.requests] == [
        "/maps/api/geocode/json"
    ]

    assert len(rapidpro_mock.tstate.requests) == 1
    request = rapidpro_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "latitude": 56.78,
            "longitude": 12.34,
            "location_description": "277 Bedford Avenue, Brooklyn, NY 11211, USA",
        },
    }


@pytest.mark.asyncio
async def test_state_location_invalid(tester: AppTester):
    tester.setup_state("state_location")

    await tester.user_input("invalid location")
    tester.assert_state("state_location")


@pytest.mark.asyncio
async def test_servicefinder_start_to_end(
    tester: AppTester, google_api_mock, servicefinder_mock, rapidpro_mock
):
    tester.setup_state("state_servicefinder_start")

    tester.user.metadata["location_description"] = "99 high level, cape town, FS"
    tester.user.metadata["longitude"] = 12.34
    tester.user.metadata["latitude"] = 56.78

    await tester.user_input("1")
    tester.assert_state("state_confirm_existing_address")

    await tester.user_input("1")
    tester.assert_state("state_category")

    await tester.user_input("2")
    tester.assert_state("state_category")

    await tester.user_input("2")
    tester.assert_state("state_start")


@pytest.mark.asyncio
async def test_state_location_type_address(tester: AppTester):
    tester.setup_state("state_location")
    await tester.user_input("Type address")
    tester.assert_state("state_province")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_state_province(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_province")
    await tester.user_input("2")
    tester.assert_answer("state_province", "FS")
    tester.assert_state("state_full_address")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_state_province_skip(
    tester: AppTester, rapidpro_mock, servicefinder_mock, google_api_mock
):
    tester.user.metadata["servicefinder_breadcrumb"] = "*Get help near you*"
    tester.user.metadata["google_session_token"] = "123"

    tester.setup_answer("state_province", "skip")
    tester.setup_state("state_full_address")
    await tester.user_input("test suburb \n test street")
    tester.assert_answer("state_province", "")


@pytest.mark.asyncio
async def test_state_full_address_invalid(tester: AppTester):
    tester.setup_state("state_full_address")
    await tester.user_input("2 test street test suburb")
    tester.assert_state("state_validate_full_address_error")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_state_validate_full_address_error_retry(
    tester: AppTester, rapidpro_mock
):
    tester.setup_state("state_validate_full_address_error")
    await tester.user_input("2")
    tester.assert_state("state_full_address")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_state_validate_full_address_error_long(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_validate_full_address_error")
    await tester.user_input("1")
    tester.assert_state("state_suburb")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_state_suburb(tester: AppTester):
    tester.setup_state("state_suburb")
    await tester.user_input("test suburb")
    tester.assert_state("state_street_name")
    tester.assert_answer("state_suburb", "test suburb")


@pytest.mark.asyncio
async def test_state_street_name(
    tester: AppTester, servicefinder_mock, google_api_mock, rapidpro_mock
):
    tester.user.metadata["servicefinder_breadcrumb"] = "*Get help near you*"
    tester.user.metadata["google_session_token"] = "123"

    tester.setup_answer("state_province", "FS")
    tester.setup_answer("state_suburb", "test suburb")
    tester.setup_state("state_street_name")
    await tester.user_input("test street")
    tester.assert_state("state_category")

    assert [r.path for r in google_api_mock.tstate.requests] == [
        "/maps/api/place/autocomplete/json",
        "/maps/api/place/details/json",
    ]

    assert len(rapidpro_mock.tstate.requests) == 1
    request = rapidpro_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "latitude": -3.866_651,
            "longitude": 51.195_827,
            "location_description": "test street test suburb, FS",
        },
    }


@pytest.mark.asyncio
async def test_state_full_address_skip(tester: AppTester):
    tester.setup_state("state_full_address")
    await tester.user_input("skip")
    tester.assert_state("state_cannot_skip")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_state_suburb_skip(tester: AppTester):
    tester.setup_state("state_suburb")
    await tester.user_input("skip")
    tester.assert_state("state_cannot_skip")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_state_cannot_skip(tester: AppTester, rapidpro_mock):
    tester.setup_state("state_cannot_skip")
    await tester.user_input("1")
    tester.assert_state("state_full_address")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_state_validate_full_address_success(
    tester: AppTester, servicefinder_mock, google_api_mock, rapidpro_mock
):
    tester.user.metadata["servicefinder_breadcrumb"] = "*Get help near you*"
    tester.user.metadata["google_session_token"] = "123"

    tester.setup_answer("state_province", "FS")
    tester.setup_state("state_full_address")
    await tester.user_input("test suburb \n test street")
    tester.assert_state("state_category")

    assert [r.path for r in google_api_mock.tstate.requests] == [
        "/maps/api/place/autocomplete/json",
        "/maps/api/place/details/json",
    ]

    assert len(rapidpro_mock.tstate.requests) == 1
    request = rapidpro_mock.tstate.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "latitude": -3.866_651,
            "longitude": 51.195_827,
            "location_description": "test street test suburb, FS",
        },
    }
