import json
from datetime import datetime
from unittest import mock
from urllib.parse import parse_qs, urlparse

import pytest
from sanic import Sanic, response

from vaccine.models import Message
from vaccine.testing import AppTester
from yal import config
from yal.main import Application
from yal.utils import BACK_TO_MAIN, GET_HELP


@pytest.fixture
def tester():
    return AppTester(Application)


def build_message_detail(
    id,
    title,
    content,
    tags=[],
    has_children=False,
    image=None,
    total_messages=1,
    quick_replies=[],
    related_pages=[],
):
    return {
        "id": id,
        "title": title,
        "subtitle": None,
        "body": {
            "message": 1,
            "next_message": None,
            "previous_message": None,
            "total_messages": total_messages,
            "text": {
                "type": "Whatsapp_Message",
                "value": {"image": image, "message": content, "next_prompt": ""},
                "id": "111b8f05-be1b-4461-ac85-562930747336",
            },
            "revision": id,
        },
        "tags": tags,
        "has_children": has_children,
        "meta": {"parent": {"id": 123, "title": "Parent Title"}},
        "quick_replies": quick_replies,
        "related_pages": related_pages,
    }


@pytest.fixture
async def rapidpro_mock(sanic_client):
    Sanic.test_mode = True
    app = Sanic("mock_rapidpro")
    app.requests = []

    @app.route("/api/v2/contacts.json", methods=["POST"])
    def update_contact(request):
        app.requests.append(request)
        return response.json({}, status=200)

    client = await sanic_client(app)
    url = config.RAPIDPRO_URL
    config.RAPIDPRO_URL = f"http://{client.host}:{client.port}"
    config.RAPIDPRO_TOKEN = "testtoken"
    yield client
    config.RAPIDPRO_URL = url


@pytest.fixture
async def turn_mock(sanic_client):
    Sanic.test_mode = True
    app = Sanic("mock_turn")
    app.requests = []

    @app.route("/v1/messages/<message_id:string>/labels", methods=["POST"])
    def label_message(request, message_id):
        app.requests.append(request)
        return response.json({}, status=200)

    client = await sanic_client(app)
    url = config.API_HOST
    config.API_HOST = f"http://{client.host}:{client.port}"
    config.API_TOKEN = "testtoken"
    yield client
    config.API_HOST = url


@pytest.fixture
async def contentrepo_api_mock(sanic_client):
    Sanic.test_mode = True
    app = Sanic("contentrepo_api_mock")
    app.requests = []
    app.errors = 0
    app.errormax = 0

    @app.route("/api/v2/pages", methods=["GET"])
    def get_main_menu(request):
        app.requests.append(request)
        if app.errormax:
            if app.errors < app.errormax:
                app.errors += 1
                return response.json({}, status=500)

        tag = request.args.get("tag")

        pages = []
        if tag == "mainmenu":
            pages.append({"id": 111, "title": "Main Menu 1 💊"})
            pages.append({"id": 222, "title": "Main Menu 2 🤝"})

        child_of = request.args.get("child_of")
        if child_of in ["111", "222", "333", "444"]:
            pages.append({"id": 333, "title": "Sub menu 1"})
            pages.append({"id": 444, "title": "Sub menu 2"})
            pages.append({"id": 1231, "title": "Sub menu 3"})

        if child_of in ["1111"]:
            for i in range(5):
                pages.append({"id": i, "title": f"Sub menu {i+1}"})
            pages.append({"id": 123, "title": "Sub menu that is very long"})

        if child_of == "1231":
            pages.append({"id": 1232, "title": "Sub Menu with image"})

        return response.json(
            {
                "count": len(pages),
                "results": pages,
            }
        )

    @app.route("/suggestedcontent", methods=["GET"])
    def get_suggested_content(request):
        app.requests.append(request)
        pages = []
        pages.append({"id": 444, "title": "Suggested Content 1"})
        pages.append({"id": 555, "title": "Suggested Content 2"})

        return response.json(
            {
                "count": len(pages),
                "results": pages,
            }
        )

    @app.route("/api/v2/pages/111", methods=["GET"])
    def get_page_detail_111(request):
        app.requests.append(request)
        return response.json(
            build_message_detail(
                111,
                "Main Menu 1 💊",
                "Message test content 1",
            )
        )

    @app.route("/api/v2/pages/1111", methods=["GET"])
    def get_page_detail_1111(request):
        app.requests.append(request)
        return response.json(
            build_message_detail(
                111,
                "Main Menu 1 💊",
                "Message test content 1",
            )
        )

    @app.route("/api/v2/pages/1112", methods=["GET"])
    def get_page_detail_1112(request):
        app.requests.append(request)
        return response.json(
            build_message_detail(
                1112,
                "Main Menu 1 💊",
                "Message test content 1",
                quick_replies=["No, thanks"],
            )
        )

    @app.route("/api/v2/pages/222", methods=["GET"])
    def get_page_detail_222(request):
        app.requests.append(request)
        return response.json(
            build_message_detail(
                222,
                "Main Menu 2 🤝",
                "Message test content 2",
                has_children=True,
            )
        )

    @app.route("/api/v2/pages/333", methods=["GET"])
    def get_page_detail_333(request):
        app.requests.append(request)
        return response.json(
            build_message_detail(
                333,
                "Sub menu 1",
                "Sub menu test content 2",
                has_children=True,
            )
        )

    @app.route("/api/v2/pages/444", methods=["GET"])
    def get_page_detail_444(request):
        app.requests.append(request)
        return response.json(
            build_message_detail(
                444,
                "Sub menu 2",
                "Sub menu test content 2",
            )
        )

    @app.route("/api/v2/pages/1231", methods=["GET"])
    def get_page_detail_1231(request):
        app.requests.append(request)
        return response.json(
            build_message_detail(
                444,
                "Sub menu 2",
                "Sub menu test content with image",
                ["test"],
                True,
                "1",
            )
        )

    @app.route("/api/v2/pages/1232", methods=["GET"])
    def get_page_detail_1232(request):
        app.requests.append(request)
        return response.json(
            build_message_detail(
                444,
                "Sub menu 2",
                "Detail test content with image",
                image="2",
                total_messages=2,
            )
        )

    @app.route("/api/v2/pages/1234", methods=["GET"])
    def get_page_detail_1234(request):
        app.requests.append(request)
        return response.json(
            build_message_detail(
                1234,
                "Main Menu 1 💊",
                "Message test content 1",
                ["aaq"],
            )
        )

    @app.route("/api/v2/pages/1235", methods=["GET"])
    def get_page_detail_1235(request):
        app.requests.append(request)
        return response.json(
            build_message_detail(
                1235,
                "Main Menu 1 💊",
                "Message test content 1",
                ["servicefinder"],
            )
        )

    @app.route("/api/v2/pages/1236", methods=["GET"])
    def get_page_detail_1236(request):
        app.requests.append(request)
        return response.json(
            build_message_detail(
                1236,
                "Main Menu 1 💊",
                "Message test content 1",
                ["pleasecallme"],
            )
        )

    @app.route("/api/v2/images/<image_id:int>", methods=["GET"])
    def get_image(request, image_id):
        app.requests.append(request)
        return response.json(
            {"meta": {"download_url": f"http://aws.test/test{image_id}.jpg"}}
        )

    @app.route("/api/v2/custom/ratings/", methods=["POST"])
    def add_page_rating(request):
        app.requests.append(request)
        return response.json({}, status=201)

    client = await sanic_client(app)
    url = config.CONTENTREPO_API_URL
    config.CONTENTREPO_API_URL = f"http://{client.host}:{client.port}"
    config.CONTENTREPO_API_TOKEN = "testtoken"
    yield client
    config.CONTENTREPO_API_URL = url


@pytest.mark.asyncio
@mock.patch("yal.mainmenu.get_current_datetime")
async def test_state_mainmenu_start(
    get_current_datetime, tester: AppTester, contentrepo_api_mock, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_pre_mainmenu")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)
    tester.assert_num_messages(1)
    tester.assert_message(
        "\n".join(
            [
                "🏡 *MAIN MENU*",
                "How can I help you today?",
                "-----",
                "Send me the number of the topic you're interested in.",
                "",
                "*🏥 NEED HELP?*",
                "1. Please call me!",
                "2. Find clinics and services",
                "-----",
                "*Main Menu 1 💊*",
                "3. Sub menu 1",
                "4. Sub menu 2",
                "5. Sub menu 3",
                "-----",
                "*Main Menu 2 🤝*",
                "6. Sub menu 1",
                "7. Sub menu 2",
                "8. Sub menu 3",
                "-----",
                "🙋🏿‍♂️ *QUESTIONS?*",
                "9. Ask a Question",
                "-----",
                "*⚙️ CHAT SETTINGS*",
                "10. Change Profile",
                "-----",
                "💡 TIP: Jump back to this menu at any time by replying 0 or MENU.",
            ]
        )
    )

    assert [r.path for r in contentrepo_api_mock.app.requests] == [
        "/api/v2/pages",
        "/api/v2/pages",
        "/api/v2/pages",
        "/suggestedcontent/",
    ]

    assert len(rapidpro_mock.app.requests) == 1
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_mainmenu_time": "2022-06-19T17:30:00",
            "suggested_text": "*11* - Suggested Content 1\n*12* - Suggested Content 2",
        },
    }


@pytest.mark.asyncio
@mock.patch("yal.mainmenu.get_current_datetime")
async def test_state_mainmenu_start_suggested_populated(
    get_current_datetime, tester: AppTester, contentrepo_api_mock, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_mainmenu")
    tester.user.metadata["suggested_content"] = {
        "444": "Suggested Content 1",
        "555": "Suggested Content 2",
    }
    await tester.user_input(session=Message.SESSION_EVENT.NEW)
    tester.assert_num_messages(1)
    tester.assert_message(
        "\n".join(
            [
                "🏡 *MAIN MENU*",
                "How can I help you today?",
                "-----",
                "Send me the number of the topic you're interested in.",
                "",
                "*🏥 NEED HELP?*",
                "1. Please call me!",
                "2. Find clinics and services",
                "-----",
                "*Main Menu 1 💊*",
                "3. Sub menu 1",
                "4. Sub menu 2",
                "5. Sub menu 3",
                "-----",
                "*Main Menu 2 🤝*",
                "6. Sub menu 1",
                "7. Sub menu 2",
                "8. Sub menu 3",
                "-----",
                "🙋🏿‍♂️ *QUESTIONS?*",
                "9. Ask a Question",
                "-----",
                "*⚙️ CHAT SETTINGS*",
                "10. Change Profile",
                "-----",
                "💡 TIP: Jump back to this menu at any time by replying 0 or MENU.",
            ]
        )
    )

    assert [r.path for r in contentrepo_api_mock.app.requests] == [
        "/api/v2/pages",
        "/api/v2/pages",
        "/api/v2/pages",
    ]

    assert len(rapidpro_mock.app.requests) == 1
    request = rapidpro_mock.app.requests[0]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_mainmenu_time": "2022-06-19T17:30:00",
            "suggested_text": "*11* - Suggested Content 1\n*12* - Suggested Content 2",
        },
    }


@pytest.mark.asyncio
async def test_state_mainmenu_static(
    tester: AppTester, contentrepo_api_mock, rapidpro_mock
):
    tester.setup_state("state_pre_mainmenu")
    await tester.user_input("2")

    tester.assert_num_messages(1)
    tester.assert_state("state_servicefinder_start")

    assert [r.path for r in contentrepo_api_mock.app.requests] == [
        "/api/v2/pages",
        "/api/v2/pages",
        "/api/v2/pages",
        "/suggestedcontent/",
    ]

    assert len(rapidpro_mock.app.requests) == 2


@pytest.mark.asyncio
async def test_state_mainmenu_aaq(
    tester: AppTester, contentrepo_api_mock, rapidpro_mock
):
    tester.setup_state("state_pre_mainmenu")
    await tester.user_input("9")

    tester.assert_num_messages(1)
    tester.assert_state("state_start")
    tester.assert_message("Coming soon...")

    assert [r.path for r in contentrepo_api_mock.app.requests] == [
        "/api/v2/pages",
        "/api/v2/pages",
        "/api/v2/pages",
        "/suggestedcontent/",
    ]

    assert len(rapidpro_mock.app.requests) == 2


@pytest.mark.asyncio
async def test_state_mainmenu_contentrepo(
    tester: AppTester, contentrepo_api_mock, rapidpro_mock
):
    tester.setup_state("state_pre_mainmenu")
    await tester.user_input("4")

    question = "\n".join(
        [
            "Sub menu 2",
            "-----",
            "",
            "Sub menu test content 2",
            "",
            "1. Pls give us feedback",
            "",
            "-----",
            "*Or reply:*",
            BACK_TO_MAIN,
            GET_HELP,
        ]
    )

    tester.assert_num_messages(1)
    tester.assert_message(question)

    assert [r.path for r in contentrepo_api_mock.app.requests] == [
        "/api/v2/pages",
        "/api/v2/pages",
        "/api/v2/pages",
        "/suggestedcontent/",
        "/api/v2/pages/444",
    ]

    tester.assert_metadata("topics_viewed", ["222"])

    assert len(rapidpro_mock.app.requests) == 3
    request = rapidpro_mock.app.requests[1]
    assert json.loads(request.body.decode("utf-8")) == {
        "fields": {
            "last_mainmenu_time": "",
            "suggested_text": "",
        },
    }


@pytest.mark.asyncio
@mock.patch("yal.mainmenu.get_current_datetime")
async def test_state_mainmenu_contentrepo_children(
    get_current_datetime, tester: AppTester, contentrepo_api_mock, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_pre_mainmenu")
    await tester.user_input("3")

    question = "\n".join(
        [
            "Sub menu 1",
            "-----",
            "",
            "Sub menu test content 2",
            "",
            "1. Sub menu 1",
            "2. Sub menu 2",
            "3. Sub menu 3",
            "",
            "-----",
            "*Or reply:*",
            BACK_TO_MAIN,
            GET_HELP,
        ]
    )

    tester.assert_num_messages(1)
    tester.assert_message(question)

    await tester.user_input("2")

    question = "\n".join(
        [
            "Sub menu 2",
            "-----",
            "",
            "Sub menu test content 2",
            "",
            "1. Pls give us feedback",
            "",
            "-----",
            "*Or reply:*",
            "2. ⬅️ Parent Title",
            BACK_TO_MAIN,
            GET_HELP,
        ]
    )

    tester.assert_num_messages(1)
    tester.assert_message(question)

    assert [r.path for r in contentrepo_api_mock.app.requests] == [
        "/api/v2/pages",
        "/api/v2/pages",
        "/api/v2/pages",
        "/suggestedcontent/",
        "/api/v2/pages/333",
        "/api/v2/pages",
        "/api/v2/pages",
        "/api/v2/pages/444",
    ]

    detail_request = contentrepo_api_mock.app.requests[-1]
    parsed_url = urlparse(detail_request.url)
    params = parse_qs(parsed_url.query)

    assert params["whatsapp"][0] == "true"
    assert params["data__session_id"][0] == "1"
    assert params["data__user_addr"][0] == "27820001001"

    assert len(rapidpro_mock.app.requests) == 5

    update_request = rapidpro_mock.app.requests[-1]
    assert update_request.json["fields"] == {
        "last_main_time": "2022-06-19T17:30:00",
        "suggested_text": "*3* - Suggested Content 1\n*4* - Suggested Content 2",
    }


@pytest.mark.asyncio
async def test_state_submenu_image(
    tester: AppTester, contentrepo_api_mock, rapidpro_mock
):
    tester.setup_state("state_pre_mainmenu")
    await tester.user_input("5")

    question = "\n".join(
        [
            "Sub menu 2",
            "-----",
            "",
            "Sub menu test content with image",
            "",
            "1. Sub Menu with image",
            "",
            "-----",
            "*Or reply:*",
            BACK_TO_MAIN,
            GET_HELP,
        ]
    )

    [msg] = tester.application.messages
    assert msg.helper_metadata["image"] == "http://aws.test/test1.jpg"
    tester.assert_message(question)


@pytest.mark.asyncio
async def test_state_detail_image(
    tester: AppTester, contentrepo_api_mock, rapidpro_mock
):
    tester.setup_state("state_pre_mainmenu")
    await tester.user_input("5")
    await tester.user_input("1")

    question = "\n".join(
        [
            "Sub menu 2",
            "-----",
            "",
            "Detail test content with image",
            "",
            "1. Next",
            "",
            "-----",
            "*Or reply:*",
            "2. ⬅️ Parent Title",
            BACK_TO_MAIN,
            GET_HELP,
        ]
    )

    [msg] = tester.application.messages
    assert msg.helper_metadata["image"] == "http://aws.test/test2.jpg"
    tester.assert_message(question)


@pytest.mark.asyncio
async def test_state_display_page_submenu_back(
    tester: AppTester, contentrepo_api_mock, rapidpro_mock
):
    tester.setup_state("state_display_page")
    tester.user.metadata["page_type"] = "submenu"
    tester.user.metadata["selected_page_id"] = "111"
    tester.user.metadata["title"] = "title"
    tester.user.metadata["body"] = "body"
    tester.user.metadata["current_menu_level"] = 3
    tester.user.metadata["current_message_id"] = 1
    tester.user.metadata["related_pages"] = None
    tester.user.metadata["suggested_content"] = {}

    tester.user.metadata["parent_title"] = "Previous thing"

    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_message(
        "\n".join(
            [
                "title",
                "-----",
                "",
                "body",
                "",
                "1. Sub menu 1",
                "2. Sub menu 2",
                "3. Sub menu 3",
                "",
                "-----",
                "*Or reply:*",
                "4. ⬅️ Previous thing",
                BACK_TO_MAIN,
                GET_HELP,
            ]
        ),
        buttons=["Sub menu 1", "Sub menu 2", "Sub menu 3"],
    )


@pytest.mark.asyncio
async def test_state_display_page_list(
    tester: AppTester, contentrepo_api_mock, rapidpro_mock
):
    tester.setup_state("state_display_page")
    tester.user.metadata["page_type"] = "submenu"
    tester.user.metadata["selected_page_id"] = "1111"
    tester.user.metadata["title"] = "title"
    tester.user.metadata["body"] = "body"
    tester.user.metadata["current_menu_level"] = 3
    tester.user.metadata["current_message_id"] = 1
    tester.user.metadata["related_pages"] = None
    tester.user.metadata["suggested_content"] = {}

    tester.user.metadata["parent_title"] = "Previous thing"

    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_message(
        "\n".join(
            [
                "title",
                "-----",
                "",
                "body",
                "",
                "1. Sub menu 1",
                "2. Sub menu 2",
                "3. Sub menu 3",
                "4. Sub menu 4",
                "5. Sub menu 5",
                "6. Sub menu that is very long",
                "",
                "-----",
                "*Or reply:*",
                "7. ⬅️ Previous thing",
                BACK_TO_MAIN,
                GET_HELP,
            ]
        ),
        button="See my options",
        list_items=[
            "Sub menu 1",
            "Sub menu 2",
            "Sub menu 3",
            "Sub menu 4",
            "Sub menu 5",
            "Sub menu that is ver",
        ],
    )


@pytest.mark.asyncio
async def test_state_display_page_detail(
    tester: AppTester, contentrepo_api_mock, rapidpro_mock
):
    tester.setup_state("state_display_page")
    tester.user.metadata["page_type"] = "detail"
    tester.user.metadata["selected_page_id"] = "111"
    tester.user.metadata["title"] = "title"
    tester.user.metadata["body"] = "body"
    tester.user.metadata["current_menu_level"] = 1
    tester.user.metadata["current_message_id"] = 1
    tester.user.metadata["related_pages"] = None
    tester.user.metadata["suggested_content"] = {}

    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_message(
        "\n".join(
            [
                "title",
                "-----",
                "",
                "body",
                "",
                "1. Pls give us feedback",
                "",
                "-----",
                "*Or reply:*",
                BACK_TO_MAIN,
                GET_HELP,
            ]
        )
    )


@pytest.mark.asyncio
async def test_state_display_page_detail_quick_replies(
    tester: AppTester, contentrepo_api_mock, rapidpro_mock
):
    tester.setup_state("state_contentrepo_page")
    tester.user.metadata["selected_page_id"] = "1112"
    tester.user.metadata["current_message_id"] = 1
    tester.user.metadata["current_menu_level"] = 3
    tester.user.metadata["last_topic_viewed"] = "1"
    tester.user.metadata["parent_title"] = "Test Back"
    tester.user.metadata["suggested_content"] = {}

    tester.user.session_id = 123
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_message(
        "\n".join(
            [
                "Main Menu 1 💊",
                "-----",
                "",
                "Message test content 1",
                "",
                "1. No, thanks",
                "2. Pls give us feedback",
                "",
                "-----",
                "*Or reply:*",
                "3. ⬅️ Parent Title",
                BACK_TO_MAIN,
                GET_HELP,
            ]
        )
    )

    await tester.user_input("1")

    tester.assert_message(
        "\n".join(
            [
                "Okay, what would you like to talk about?",
                "",
                "1. Suggested Content 1",
                "2. Suggested Content 2",
                "-----",
                "*Or reply:*",
                "3. ⬅️ Parent Title",
                BACK_TO_MAIN,
                GET_HELP,
            ]
        )
    )


@pytest.mark.asyncio
async def test_state_display_page_detail_aaq_feature(
    tester: AppTester, contentrepo_api_mock, rapidpro_mock
):
    tester.setup_state("state_contentrepo_page")
    tester.user.metadata["selected_page_id"] = "1234"
    tester.user.metadata["current_message_id"] = 1
    tester.user.metadata["current_menu_level"] = 1
    tester.user.metadata["last_topic_viewed"] = "1"
    tester.user.metadata["suggested_content"] = {}

    tester.user.session_id = 123
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_message(
        "\n".join(
            [
                "Main Menu 1 💊",
                "-----",
                "",
                "Message test content 1",
                "",
                "1. Ask a Question",
                "2. Pls give us feedback",
                "",
                "-----",
                "*Or reply:*",
                "3. ⬅️ Parent Title",
                BACK_TO_MAIN,
                GET_HELP,
            ]
        )
    )

    await tester.user_input("1")

    tester.assert_state("state_start")


@pytest.mark.asyncio
async def test_state_display_page_detail_servicefinder_feature(
    tester: AppTester, contentrepo_api_mock, rapidpro_mock
):
    tester.setup_state("state_contentrepo_page")
    tester.user.metadata["selected_page_id"] = "1235"
    tester.user.metadata["current_message_id"] = 1
    tester.user.metadata["current_menu_level"] = 1
    tester.user.metadata["last_topic_viewed"] = "1"
    tester.user.metadata["suggested_content"] = {}

    tester.user.session_id = 123
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_message(
        "\n".join(
            [
                "Main Menu 1 💊",
                "-----",
                "",
                "Message test content 1",
                "",
                "1. Find a clinic",
                "2. Pls give us feedback",
                "",
                "-----",
                "*Or reply:*",
                "3. ⬅️ Parent Title",
                BACK_TO_MAIN,
                GET_HELP,
            ]
        )
    )

    await tester.user_input("1")

    tester.assert_state("state_servicefinder_start")


@pytest.mark.asyncio
@mock.patch("yal.pleasecallme.get_current_datetime")
async def test_state_display_page_detail_pleasecallme_feature(
    get_current_datetime, tester: AppTester, contentrepo_api_mock, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 20, 17, 30)
    tester.setup_state("state_contentrepo_page")
    tester.user.metadata["selected_page_id"] = "1236"
    tester.user.metadata["current_message_id"] = 1
    tester.user.metadata["current_menu_level"] = 1
    tester.user.metadata["last_topic_viewed"] = "1"
    tester.user.metadata["suggested_content"] = {}

    tester.user.session_id = 123
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_message(
        "\n".join(
            [
                "Main Menu 1 💊",
                "-----",
                "",
                "Message test content 1",
                "",
                "1. Call Lovelife",
                "2. Pls give us feedback",
                "",
                "-----",
                "*Or reply:*",
                "3. ⬅️ Parent Title",
                BACK_TO_MAIN,
                GET_HELP,
            ]
        )
    )

    await tester.user_input("1")

    tester.assert_state("state_in_hours")


@pytest.mark.asyncio
async def test_state_display_page_detail_next(
    tester: AppTester, contentrepo_api_mock, rapidpro_mock
):
    tester.setup_state("state_display_page")
    tester.user.metadata["page_type"] = "detail"
    tester.user.metadata["selected_page_id"] = "111"
    tester.user.metadata["title"] = "title"
    tester.user.metadata["body"] = "body"
    tester.user.metadata["current_menu_level"] = 1
    tester.user.metadata["current_message_id"] = 1
    tester.user.metadata["suggested_content"] = {}

    tester.user.metadata["next_prompt"] = "Continue"

    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_message(
        "\n".join(
            [
                "title",
                "-----",
                "",
                "body",
                "",
                "1. Continue",
                "",
                "-----",
                "*Or reply:*",
                BACK_TO_MAIN,
                GET_HELP,
            ]
        )
    )


@pytest.mark.asyncio
async def test_state_display_page_detail_back(
    tester: AppTester, contentrepo_api_mock, rapidpro_mock
):
    tester.setup_state("state_display_page")
    tester.user.metadata["page_type"] = "detail"
    tester.user.metadata["selected_page_id"] = "111"
    tester.user.metadata["title"] = "title"
    tester.user.metadata["body"] = "body"
    tester.user.metadata["current_menu_level"] = 3
    tester.user.metadata["current_message_id"] = 1
    tester.user.metadata["related_pages"] = None
    tester.user.metadata["suggested_content"] = {}

    tester.user.metadata["parent_title"] = "Previous thing"

    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_message(
        "\n".join(
            [
                "title",
                "-----",
                "",
                "body",
                "",
                "1. Pls give us feedback",
                "",
                "-----",
                "*Or reply:*",
                "2. ⬅️ Previous thing",
                BACK_TO_MAIN,
                GET_HELP,
            ]
        )
    )


@pytest.mark.asyncio
async def test_state_display_page_detail_next_and_back(
    tester: AppTester, contentrepo_api_mock, rapidpro_mock
):
    tester.setup_state("state_display_page")
    tester.user.metadata["page_type"] = "detail"
    tester.user.metadata["selected_page_id"] = "111"
    tester.user.metadata["title"] = "title"
    tester.user.metadata["body"] = "body"
    tester.user.metadata["current_menu_level"] = 3
    tester.user.metadata["current_message_id"] = 1
    tester.user.metadata["suggested_content"] = {}

    tester.user.metadata["next_prompt"] = "Continue"

    tester.user.metadata["parent_title"] = "Previous thing"

    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_message(
        "\n".join(
            [
                "title",
                "-----",
                "",
                "body",
                "",
                "1. Continue",
                "",
                "-----",
                "*Or reply:*",
                "2. ⬅️ Previous thing",
                BACK_TO_MAIN,
                GET_HELP,
            ]
        )
    )


@pytest.mark.asyncio
async def test_state_display_page_detail_related(
    tester: AppTester, contentrepo_api_mock, rapidpro_mock
):
    tester.setup_state("state_display_page")
    tester.user.metadata["page_type"] = "detail"
    tester.user.metadata["selected_page_id"] = "111"
    tester.user.metadata["title"] = "title"
    tester.user.metadata["body"] = "body"
    tester.user.metadata["current_menu_level"] = 1
    tester.user.metadata["current_message_id"] = 1
    tester.user.metadata["related_pages"] = {"123": "Related Content"}
    tester.user.metadata["suggested_content"] = {}

    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_message(
        "\n".join(
            [
                "title",
                "-----",
                "",
                "body",
                "",
                "1. Related Content",
                "2. Pls give us feedback",
                "",
                "-----",
                "*Or reply:*",
                BACK_TO_MAIN,
                GET_HELP,
            ]
        )
    )


@pytest.fixture
async def contentrepo_api_mock2(sanic_client):
    Sanic.test_mode = True
    app = Sanic("contentrepo_api_mock2")

    @app.route("/api/v2/pages/1", methods=["GET"])
    def get_page_detail_1(request):
        return response.json(
            build_message_detail(
                111,
                "Main Menu 1 💊",
                "Message test content 1",
                ["related_2"],
            )
        )

    @app.route("/api/v2/pages/2", methods=["GET"])
    def get_page_detail_2(request):
        return response.json(
            build_message_detail(
                222,
                "Main Menu 2 💊",
                "Message test content 2",
                related_pages=[
                    {"title": "Related Content 2", "value": 107, "id": "page-uuid"}
                ],
            )
        )

    @app.route("/api/v2/pages", methods=["GET"])
    def get_related_by_id(request):
        return response.json(
            {
                "count": 1,
                "results": [{"id": 111, "title": "Related Content"}],
            }
        )

    client = await sanic_client(app)
    url = config.CONTENTREPO_API_URL
    config.CONTENTREPO_API_URL = f"http://{client.host}:{client.port}"
    yield client
    config.CONTENTREPO_API_URL = url


@pytest.mark.asyncio
async def test_state_content_page_related_tags(
    tester: AppTester, contentrepo_api_mock2, rapidpro_mock
):
    tester.setup_state("state_contentrepo_page")
    tester.user.metadata["selected_page_id"] = "1"
    tester.user.metadata["current_message_id"] = 1
    tester.user.metadata["current_menu_level"] = 0
    tester.user.metadata["suggested_content"] = {"123": "Suggested"}

    tester.user.session_id = 123

    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_message(
        "\n".join(
            [
                "Main Menu 1 💊",
                "-----",
                "",
                "Message test content 1",
                "",
                "1. Related Content",
                "2. Pls give us feedback",
                "",
                "-----",
                "*Or reply:*",
                BACK_TO_MAIN,
                GET_HELP,
            ]
        )
    )


@pytest.mark.asyncio
async def test_state_content_page_related(
    tester: AppTester, contentrepo_api_mock2, rapidpro_mock
):
    tester.setup_state("state_contentrepo_page")
    tester.user.metadata["selected_page_id"] = "2"
    tester.user.metadata["current_message_id"] = 1
    tester.user.metadata["current_menu_level"] = 0
    tester.user.metadata["suggested_content"] = {"123": "Suggested"}

    tester.user.session_id = 123

    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_message(
        "\n".join(
            [
                "Main Menu 2 💊",
                "-----",
                "",
                "Message test content 2",
                "",
                "1. Related Content 2",
                "2. Pls give us feedback",
                "",
                "-----",
                "*Or reply:*",
                BACK_TO_MAIN,
                GET_HELP,
            ]
        )
    )


@pytest.mark.asyncio
async def test_state_prompt_info_found(tester: AppTester):
    tester.setup_state("state_prompt_info_found")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_message(
        "\n".join(
            [
                "Did you find the info you were looking for?",
                "",
                "Reply:",
                "1. 👍🏾 Yes",
                "2. 👎🏾 No",
                "",
                "--",
                "",
                "0. 🏠 *Back* to Main *MENU*",
                "#. 🆘Get *HELP*",
            ]
        )
    )


@pytest.mark.asyncio
async def test_state_prompt_info_found_no(tester: AppTester):
    tester.setup_state("state_prompt_info_found")
    await tester.user_input("no")

    tester.assert_message(
        "\n".join(
            [
                "Hmm, I'm sorry about that.😕",
                "Please tell me a bit more about what info you're looking for "
                "so that I can help you next time.",
            ]
        )
    )


@pytest.mark.asyncio
async def test_state_prompt_not_found_comment(tester: AppTester, turn_mock):
    tester.setup_state("state_prompt_not_found_comment")
    await tester.user_input("I don't know")

    tester.assert_message(
        "Ok got it. Thank you for the feedback, I'm working on it already👍🏾."
    )

    message_id = tester.application.inbound.message_id  # type: ignore
    label_request = turn_mock.app.requests[0]
    assert label_request.path == f"/v1/messages/{message_id}/labels"
    assert json.loads(label_request.body.decode("utf-8")) == {
        "labels": ["Priority Question"],
    }


@pytest.mark.asyncio
async def test_state_prompt_info_useful(tester: AppTester):
    tester.setup_state("state_prompt_info_found")
    await tester.user_input("1")

    tester.assert_message(
        "\n".join(
            [
                "Great.😊 Was the info useful?",
                "",
                "Reply:",
                "1. 👍🏾 Yes",
                "2. 👎🏾 No",
                "",
                "--",
                "",
                "0. 🏠 *Back* to Main *MENU*",
                "#. 🆘Get *HELP*",
            ]
        )
    )


@pytest.mark.asyncio
async def test_state_prompt_info_useful_emoticon(tester: AppTester):
    tester.setup_state("state_prompt_info_useful")
    await tester.user_input("👎🏾")
    tester.assert_state("state_prompt_feedback_comment")

    tester.setup_state("state_prompt_info_useful")
    await tester.user_input("👎")
    tester.assert_state("state_prompt_feedback_comment")


@pytest.mark.asyncio
async def test_state_prompt_info_useful_submit(tester: AppTester, contentrepo_api_mock):
    tester.setup_state("state_prompt_info_useful")
    tester.user.metadata["selected_page_id"] = "111"

    await tester.user_input("1")

    post_request = contentrepo_api_mock.app.requests[0]
    assert post_request.path == "/api/v2/custom/ratings/"
    assert json.loads(post_request.body.decode("utf-8")) == {
        "page": "111",
        "helpful": True,
        "comment": "",
        "data": {"session_id": 1, "user_addr": "27820001001"},
    }


@pytest.mark.asyncio
async def test_state_prompt_feedback_comment(tester: AppTester):
    tester.setup_state("state_prompt_info_useful")
    await tester.user_input("2")

    tester.assert_state("state_prompt_feedback_comment")


@pytest.mark.asyncio
async def test_state_prompt_feedback_comment_submit(
    tester: AppTester, contentrepo_api_mock, turn_mock
):
    tester.setup_state("state_prompt_feedback_comment")
    tester.user.metadata["selected_page_id"] = "111"
    tester.setup_answer("state_prompt_info_useful", "no")

    await tester.user_input("I don't understand")

    tester.assert_message(
        "Ok got it. Thank you for the feedback, I'm working on it already👍🏾."
    )

    post_request = contentrepo_api_mock.app.requests[0]
    assert post_request.path == "/api/v2/custom/ratings/"
    assert post_request.headers["authorization"] == "Token testtoken"
    assert json.loads(post_request.body.decode("utf-8")) == {
        "page": "111",
        "helpful": False,
        "comment": "I don't understand",
        "data": {"session_id": 1, "user_addr": "27820001001"},
    }

    message_id = tester.application.inbound.message_id  # type: ignore
    label_request = turn_mock.app.requests[0]
    assert label_request.path == f"/v1/messages/{message_id}/labels"
    assert json.loads(label_request.body.decode("utf-8")) == {
        "labels": ["Priority Question"],
    }
