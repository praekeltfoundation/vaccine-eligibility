import random
from datetime import datetime
from unittest import mock
from urllib.parse import parse_qs, urlparse

import pytest
from sanic import Sanic, response

from vaccine.models import Message
from vaccine.testing import AppTester, TState, run_sanic
from yal import config, turn
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
    message=1,
    next_message=None,
    previous_message=None,
    variations=[],
):
    return {
        "id": id,
        "title": title,
        "subtitle": None,
        "body": {
            "message": message,
            "next_message": next_message,
            "previous_message": previous_message,
            "total_messages": total_messages,
            "text": {
                "type": "Whatsapp_Message",
                "value": {
                    "image": image,
                    "message": content,
                    "next_prompt": "",
                    "variation_messages": variations,
                },
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
async def rapidpro_mock():
    Sanic.test_mode = True
    app = Sanic("mock_rapidpro")
    tstate = TState()

    @app.route("/api/v2/contacts.json", methods=["POST"])
    def update_contact(request):
        tstate.requests.append(request)
        print("updating contact", request.json["fields"])
        tstate.contact_fields.update(request.json["fields"])
        return response.json({}, status=200)

    @app.route("/api/v2/contacts.json", methods=["GET"])
    def get_contact(request):
        tstate.requests.append(request)
        return response.json(
            {
                "results": [{"fields": tstate.contact_fields}],
                "next": None,
            },
            status=200,
        )

    async with run_sanic(app) as server:
        url = config.RAPIDPRO_URL
        config.RAPIDPRO_URL = f"http://{server.host}:{server.port}"
        config.RAPIDPRO_TOKEN = "testtoken"
        server.tstate = tstate
        yield server
        config.RAPIDPRO_URL = url


@pytest.fixture
async def turn_mock():
    Sanic.test_mode = True
    app = Sanic("mock_turn")
    tstate = TState()

    @app.route("/v1/messages/<message_id:str>/labels", methods=["POST"])
    def label_message(request, message_id):
        tstate.requests.append(request)
        return response.json({}, status=200)

    async with run_sanic(app) as server:
        get_turn_url = turn.get_turn_url
        turn.get_turn_url = lambda path: f"http://{server.host}:{server.port}/{path}"
        server.tstate = tstate
        yield server
        turn.get_turn_url = get_turn_url


@pytest.fixture
async def contentrepo_api_mock():
    Sanic.test_mode = True
    app = Sanic("contentrepo_api_mock")
    tstate = TState()

    @app.route("/api/v2/pages", methods=["GET"])
    def get_main_menu(request):
        tstate.requests.append(request)
        if tstate.errormax:
            if tstate.errors < tstate.errormax:
                tstate.errors += 1
                return response.json({}, status=500)

        tag = request.args.get("tag")

        pages = []
        if tag == "mainmenu":
            pages.append({"id": 111, "title": "Main Menu 1 💊"})
            pages.append({"id": 222, "title": "Main Menu 2 Relationships 🤝"})
        elif tag == "banner":
            if tstate.banner:
                pages.append({"id": 777, "title": "Banner message"})
        elif tag == "help_submenu":
            pages.append({"id": 1111, "title": "Help content"})

        child_of = request.args.get("child_of")
        if child_of in ["111", "333", "444"]:
            pages.append({"id": 333, "title": "Sub menu 1"})
            pages.append({"id": 444, "title": "Sub menu 2"})
            pages.append({"id": 1231, "title": "Sub menu 3"})
        if child_of in ["222", "888"]:
            pages.append({"id": 888, "title": "Sub menu 1"})
            pages.append({"id": 999, "title": "Sub menu 2"})
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
        tstate.requests.append(request)
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
        tstate.requests.append(request)
        return response.json(
            build_message_detail(
                111,
                "Main Menu 1 💊",
                "Message test content 1",
            )
        )

    @app.route("/api/v2/pages/1111", methods=["GET"])
    def get_page_detail_1111(request):
        tstate.requests.append(request)
        return response.json(
            build_message_detail(
                111,
                "Main Menu 1 💊",
                "Message test content 1",
                total_messages=2,
                message=1,
                next_message=2,
            ),
        )

    @app.route("/api/v2/pages/1112", methods=["GET"])
    def get_page_detail_1112(request):
        tstate.requests.append(request)
        return response.json(
            build_message_detail(
                1112,
                "Main Menu 1 💊",
                "Message test content 1",
                quick_replies=["No, thanks"],
                variations=[
                    {
                        "profile_field": "gender",
                        "value": "female",
                        "message": "Message test content for females",
                    },
                    {
                        "profile_field": "gender",
                        "value": "male",
                        "message": "Message test content for males",
                    },
                ],
            )
        )

    @app.route("/api/v2/pages/222", methods=["GET"])
    def get_page_detail_222(request):
        tstate.requests.append(request)
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
        tstate.requests.append(request)
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
        tstate.requests.append(request)
        return response.json(
            build_message_detail(
                444,
                "Sub menu 2",
                "Sub menu test content 2",
            )
        )

    @app.route("/api/v2/pages/888", methods=["GET"])
    def get_page_detail_888(request):
        tstate.requests.append(request)
        return response.json(
            build_message_detail(
                888,
                "Sub menu 1",
                "Sub menu test content 2",
                has_children=True,
            )
        )

    @app.route("/api/v2/pages/1231", methods=["GET"])
    def get_page_detail_1231(request):
        tstate.requests.append(request)
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
        tstate.requests.append(request)
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
        tstate.requests.append(request)
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
        tstate.requests.append(request)
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
        tstate.requests.append(request)
        return response.json(
            build_message_detail(
                1236,
                "Main Menu 1 💊",
                "Message test content 1",
                ["pleasecallme"],
            )
        )

    @app.route("/api/v2/pages/777", methods=["GET"])
    def get_page_detail_777(request):
        tstate.requests.append(request)
        return response.json(
            build_message_detail(
                777,
                "Banner message",
                "Test banner message",
                ["banner"],
            )
        )

    @app.route("/api/v2/images/<image_id:int>", methods=["GET"])
    def get_image(request, image_id):
        tstate.requests.append(request)
        return response.json(
            {"meta": {"download_url": f"http://aws.test/test{image_id}.jpg"}}
        )

    @app.route("/api/v2/custom/ratings/", methods=["POST"])
    def add_page_rating(request):
        tstate.requests.append(request)
        return response.json({}, status=201)

    async with run_sanic(app) as server:
        url = config.CONTENTREPO_API_URL
        config.CONTENTREPO_API_URL = f"http://{server.host}:{server.port}"
        config.CONTENTREPO_API_TOKEN = "testtoken"
        server.tstate = tstate
        yield server
        config.CONTENTREPO_API_URL = url


@pytest.mark.asyncio
async def test_mainmenu_show_privacy_policy(
    tester: AppTester,
    rapidpro_mock,
):
    tester.setup_state("state_pre_mainmenu")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)
    tester.assert_num_messages(2)

    assert len(rapidpro_mock.tstate.requests) == 3
    assert rapidpro_mock.tstate.contact_fields["privacy_reminder_sent"] == "True"
    _, privacy_message = tester.application.messages
    assert privacy_message.content == "\n".join(
        [
            "*This conversation is completely private and confidential.* 🤐",
            "-----",
            "",
            "⚠️ If you think someone else could have access to the phone "
            "you're using to chat, remember to *delete these messages* "
            "at the end of our chat.",
        ]
    )


@pytest.mark.asyncio
async def test_mainmenu_skip_privacy_policy_if_seen(tester: AppTester, rapidpro_mock):
    """
    If the contact field shows that they've already seen the privacy policy, then don't
    show it to them
    """
    rapidpro_mock.tstate.contact_fields["privacy_reminder_sent"] = "True"
    tester.setup_state("state_pre_mainmenu")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)
    tester.assert_num_messages(1)
    tester.assert_state("state_mainmenu")


@pytest.mark.asyncio
@mock.patch("yal.mainmenu.get_current_datetime")
async def test_state_mainmenu_start(
    get_current_datetime, tester: AppTester, contentrepo_api_mock, rapidpro_mock
):
    contentrepo_api_mock.tstate.banner = True
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_pre_mainmenu")
    await tester.user_input(session=Message.SESSION_EVENT.NEW)
    tester.assert_num_messages(3)
    menu, banner, _ = tester.application.messages
    assert menu.content == "\n".join(
        [
            "🏡 *MAIN MENU*",
            "How can I help you today?",
            "-----",
            "Send me the number of the topic you're interested in.",
            "",
            "🏥 *NEED HELP?*",
            "1. Talk to a counsellor",
            "2. Find clinics and services",
            "3. Help content",
            "-----",
            "*Main Menu 1 💊*",
            "4. Sub menu 1",
            "5. Sub menu 2",
            "6. Sub menu 3",
            "-----",
            "*Main Menu 2 Relationships 🤝*",
            "7. Sub menu 1",
            "8. Sub menu 2",
            "9. Sub menu 3",
            "-----",
            "🙋🏿‍♂️ *QUESTIONS?*",
            "10. Ask your own question",
            "-----",
            "⚙️ *CHAT SETTINGS*",
            "11. Update your information",
            "-----",
            "💡 *TIP:* _Jump back to this menu at any time by replying_ *0* or *MENU*.",
        ]
    )
    assert banner.content == "Test banner message"

    assert [r.path for r in contentrepo_api_mock.tstate.requests] == [
        "/api/v2/pages",
        "/api/v2/pages",
        "/api/v2/pages",
        "/api/v2/pages",
        "/suggestedcontent/",
        "/api/v2/pages",
        "/api/v2/pages/777",
    ]

    assert len(rapidpro_mock.tstate.requests) == 4
    assert (
        rapidpro_mock.tstate.contact_fields["last_mainmenu_time"]
        == "2022-06-19T17:30:00"
    )
    assert (
        rapidpro_mock.tstate.contact_fields["suggested_text"]
        == "*12* - Suggested Content 1\n*13* - Suggested Content 2"
    )
    assert (
        rapidpro_mock.tstate.contact_fields["feedback_timestamp"]
        == "2022-06-19T19:30:00"
    )
    assert rapidpro_mock.tstate.contact_fields["feedback_type"] == "facebook_banner"


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
    tester.assert_num_messages(2)
    message, _ = tester.application.messages
    assert message.content == "\n".join(
        [
            "🏡 *MAIN MENU*",
            "How can I help you today?",
            "-----",
            "Send me the number of the topic you're interested in.",
            "",
            "🏥 *NEED HELP?*",
            "1. Talk to a counsellor",
            "2. Find clinics and services",
            "3. Help content",
            "-----",
            "*Main Menu 1 💊*",
            "4. Sub menu 1",
            "5. Sub menu 2",
            "6. Sub menu 3",
            "-----",
            "*Main Menu 2 Relationships 🤝*",
            "7. Sub menu 1",
            "8. Sub menu 2",
            "9. Sub menu 3",
            "-----",
            "🙋🏿‍♂️ *QUESTIONS?*",
            "10. Ask your own question",
            "-----",
            "⚙️ *CHAT SETTINGS*",
            "11. Update your information",
            "-----",
            "💡 *TIP:* _Jump back to this menu at any time by replying_ *0* or"
            " *MENU*.",
        ]
    )

    assert [r.path for r in contentrepo_api_mock.tstate.requests] == [
        "/api/v2/pages",
        "/api/v2/pages",
        "/api/v2/pages",
        "/api/v2/pages",
        "/api/v2/pages",
    ]

    assert len(rapidpro_mock.tstate.requests) == 3
    assert (
        rapidpro_mock.tstate.contact_fields["last_mainmenu_time"]
        == "2022-06-19T17:30:00"
    )
    assert (
        rapidpro_mock.tstate.contact_fields["suggested_text"]
        == "*12* - Suggested Content 1\n*13* - Suggested Content 2"
    )


@pytest.mark.asyncio
async def test_state_mainmenu_static(
    tester: AppTester, contentrepo_api_mock, rapidpro_mock
):
    tester.setup_state("state_pre_mainmenu")
    await tester.user_input("2")

    tester.assert_num_messages(1)
    tester.assert_state("state_servicefinder_start")

    assert [r.path for r in contentrepo_api_mock.tstate.requests] == [
        "/api/v2/pages",
        "/api/v2/pages",
        "/api/v2/pages",
        "/api/v2/pages",
        "/suggestedcontent/",
        "/api/v2/pages",
    ]

    assert len(rapidpro_mock.tstate.requests) == 4


@pytest.mark.asyncio
async def test_state_mainmenu_aaq(
    tester: AppTester, contentrepo_api_mock, rapidpro_mock
):
    tester.setup_state("state_pre_mainmenu")
    await tester.user_input("10")

    tester.assert_num_messages(1)
    tester.assert_state("state_start")
    tester.assert_message("Coming soon...")

    assert [r.path for r in contentrepo_api_mock.tstate.requests] == [
        "/api/v2/pages",
        "/api/v2/pages",
        "/api/v2/pages",
        "/api/v2/pages",
        "/suggestedcontent/",
        "/api/v2/pages",
    ]

    assert len(rapidpro_mock.tstate.requests) == 4


@pytest.mark.asyncio
async def test_state_mainmenu_contentrepo(
    tester: AppTester, contentrepo_api_mock, rapidpro_mock
):
    tester.setup_state("state_pre_mainmenu")
    await tester.user_input("5")

    question = "\n".join(
        [
            "Sub menu 2",
            "-----",
            "",
            "Sub menu test content 2",
            "",
            "-----",
            "*Or reply:*",
            BACK_TO_MAIN,
            GET_HELP,
        ]
    )

    tester.assert_num_messages(1)
    tester.assert_message(question)

    assert [r.path for r in contentrepo_api_mock.tstate.requests] == [
        "/api/v2/pages",
        "/api/v2/pages",
        "/api/v2/pages",
        "/api/v2/pages",
        "/suggestedcontent/",
        "/api/v2/pages",
        "/api/v2/pages/444",
    ]

    tester.assert_metadata("topics_viewed", ["111"])

    assert len(rapidpro_mock.tstate.requests) == 6
    assert rapidpro_mock.tstate.contact_fields["last_mainmenu_time"] == ""
    assert (
        rapidpro_mock.tstate.contact_fields["suggested_text"]
        == "*1* - Suggested Content 1\n*2* - Suggested Content 2"
    )


@pytest.mark.asyncio
async def test_state_mainmenu_contentrepo_help_content(
    tester: AppTester, contentrepo_api_mock, rapidpro_mock
):
    tester.setup_state("state_pre_mainmenu")
    await tester.user_input("3")

    question = "\n".join(
        [
            "Main Menu 1 💊",
            "-----",
            "",
            "Message test content 1",
            "",
            "1. Next",
            "",
            "-----",
            "*Or reply:*",
            BACK_TO_MAIN,
            GET_HELP,
        ]
    )

    assert tester.user.metadata["current_menu_level"] == 1
    tester.assert_num_messages(1)
    tester.assert_message(question)

    await tester.user_input("1")
    assert tester.user.metadata["current_menu_level"] == 1

    assert [r.path for r in contentrepo_api_mock.tstate.requests] == [
        "/api/v2/pages",
        "/api/v2/pages",
        "/api/v2/pages",
        "/api/v2/pages",
        "/suggestedcontent/",
        "/api/v2/pages",
        "/api/v2/pages/1111",
        "/api/v2/pages/1111",
    ]

    request = contentrepo_api_mock.tstate.requests[-1]
    assert request.args["message"] == ["2"]

    assert len(rapidpro_mock.tstate.requests) == 10
    assert rapidpro_mock.tstate.contact_fields["last_mainmenu_time"] == ""
    assert (
        rapidpro_mock.tstate.contact_fields["suggested_text"]
        == "*2* - Suggested Content 1\n*3* - Suggested Content 2"
    )


@pytest.mark.asyncio
async def test_state_mainmenu_contentrepo_relationship_content_rel_set(
    tester: AppTester, contentrepo_api_mock, rapidpro_mock
):
    rapidpro_mock.tstate.contact_fields["relationship_status"] = "Yes"
    tester.setup_state("state_pre_mainmenu")
    await tester.user_input("7")

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
    tester.assert_state("state_display_page")

    assert [r.path for r in contentrepo_api_mock.tstate.requests] == [
        "/api/v2/pages",
        "/api/v2/pages",
        "/api/v2/pages",
        "/api/v2/pages",
        "/suggestedcontent/",
        "/api/v2/pages",
        "/api/v2/pages/888",
        "/api/v2/pages",
    ]

    tester.assert_metadata("topics_viewed", ["222"])

    assert len(rapidpro_mock.tstate.requests) == 6
    assert rapidpro_mock.tstate.contact_fields["last_mainmenu_time"] == ""
    assert (
        rapidpro_mock.tstate.contact_fields["suggested_text"]
        == "*4* - Suggested Content 1\n*5* - Suggested Content 2"
    )


@pytest.mark.asyncio
async def test_state_mainmenu_contentrepo_relationship_status(
    tester: AppTester, contentrepo_api_mock, rapidpro_mock
):
    tester.setup_state("state_pre_mainmenu")
    await tester.user_input("7")

    question = "\n".join(
        [
            "*Main Menu 2 Relationships 🤝*",
            "-----",
            "",
            "Before we get into relationship talk, I just wanted to find out...",
            "",
            "🤖 *Are you currently in a relationship or seeing someone special right "
            "now?*",
            "",
            "1. Yes, in a relationship",
            "2. It's complicated",
            "3. Not seeing anyone",
            "4. Skip",
        ]
    )

    tester.assert_num_messages(1)
    tester.assert_message(question)
    tester.assert_state("state_relationship_status")

    assert [r.path for r in contentrepo_api_mock.tstate.requests] == [
        "/api/v2/pages",
        "/api/v2/pages",
        "/api/v2/pages",
        "/api/v2/pages",
        "/suggestedcontent/",
        "/api/v2/pages",
    ]

    tester.assert_metadata("topics_viewed", ["222"])

    assert len(rapidpro_mock.tstate.requests) == 4
    assert rapidpro_mock.tstate.contact_fields["last_mainmenu_time"] == ""
    assert rapidpro_mock.tstate.contact_fields["suggested_text"] == ""


@pytest.mark.asyncio
async def test_state_mainmenu_contentrepo_relationship_skip(
    tester: AppTester, contentrepo_api_mock, rapidpro_mock
):
    tester.user.metadata["selected_page_id"] = "888"
    tester.user.metadata["current_message_id"] = 1
    tester.user.metadata["related_pages"] = None
    tester.user.metadata["suggested_content"] = {}
    tester.user.metadata["current_menu_level"] = 3
    tester.user.metadata["parent_title"] = "Previous thing"
    tester.user.metadata["relationship_section_title"] = "Section title"

    tester.setup_state("state_relationship_status")
    await tester.user_input("skip")

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
            "4. ⬅️ Parent Title",
            BACK_TO_MAIN,
            GET_HELP,
        ]
    )

    tester.assert_num_messages(1)
    tester.assert_message(question)
    tester.assert_state("state_display_page")

    assert [r.path for r in contentrepo_api_mock.tstate.requests] == [
        "/api/v2/pages/888",
        "/suggestedcontent/",
        "/api/v2/pages",
    ]

    assert len(rapidpro_mock.tstate.requests) == 3


@pytest.mark.asyncio
async def test_state_mainmenu_contentrepo_relationship_submit(
    tester: AppTester, contentrepo_api_mock, rapidpro_mock
):
    tester.user.metadata["selected_page_id"] = "888"
    tester.user.metadata["current_message_id"] = 1
    tester.user.metadata["related_pages"] = None
    tester.user.metadata["suggested_content"] = {}
    tester.user.metadata["current_menu_level"] = 3
    tester.user.metadata["parent_title"] = "Previous thing"
    tester.user.metadata["relationship_section_title"] = "Section title"

    tester.setup_state("state_relationship_status")
    await tester.user_input("In a relationship")

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
            "4. ⬅️ Parent Title",
            BACK_TO_MAIN,
            GET_HELP,
        ]
    )

    tester.assert_num_messages(1)
    tester.assert_message(question)
    tester.assert_state("state_display_page")

    assert [r.path for r in contentrepo_api_mock.tstate.requests] == [
        "/api/v2/pages/888",
        "/suggestedcontent/",
        "/api/v2/pages",
    ]

    assert len(rapidpro_mock.tstate.requests) == 4
    assert rapidpro_mock.tstate.contact_fields["relationship_status"] == "yes"


@pytest.mark.asyncio
@mock.patch("yal.mainmenu.get_current_datetime")
async def test_state_mainmenu_contentrepo_children(
    get_current_datetime, tester: AppTester, contentrepo_api_mock, rapidpro_mock
):
    get_current_datetime.return_value = datetime(2022, 6, 19, 17, 30)
    tester.setup_state("state_pre_mainmenu")
    await tester.user_input("4")

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
            "-----",
            "*Or reply:*",
            "1. ⬅️ Parent Title",
            BACK_TO_MAIN,
            GET_HELP,
        ]
    )

    tester.assert_num_messages(1)
    tester.assert_message(question)

    assert [r.path for r in contentrepo_api_mock.tstate.requests] == [
        "/api/v2/pages",
        "/api/v2/pages",
        "/api/v2/pages",
        "/api/v2/pages",
        "/suggestedcontent/",
        "/api/v2/pages",
        "/api/v2/pages/333",
        "/api/v2/pages",
        "/api/v2/pages",
        "/api/v2/pages/444",
    ]

    detail_request = contentrepo_api_mock.tstate.requests[-1]
    parsed_url = urlparse(detail_request.url)
    params = parse_qs(parsed_url.query)

    assert params["whatsapp"][0] == "true"
    assert params["data__session_id"][0] == "1"
    assert params["data__user_addr"][0] == "27820001001"

    assert len(rapidpro_mock.tstate.requests) == 10
    assert rapidpro_mock.tstate.contact_fields["last_mainmenu_time"] == ""
    assert (
        rapidpro_mock.tstate.contact_fields["last_main_time"] == "2022-06-19T17:30:00"
    )
    assert (
        rapidpro_mock.tstate.contact_fields["suggested_text"]
        == "*2* - Suggested Content 1\n*3* - Suggested Content 2"
    )
    assert rapidpro_mock.tstate.contact_fields["feedback_type"] == "content"
    assert "feedback_timestamp" in rapidpro_mock.tstate.contact_fields


@pytest.mark.asyncio
async def test_state_submenu_image(
    tester: AppTester, contentrepo_api_mock, rapidpro_mock
):
    rapidpro_mock.tstate.contact_fields["relationship_status"] = "Yes"
    tester.setup_state("state_pre_mainmenu")
    await tester.user_input("6")

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
    rapidpro_mock.tstate.contact_fields["relationship_status"] = "Yes"
    tester.setup_state("state_pre_mainmenu")
    await tester.user_input("6")
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
                "",
                "-----",
                "*Or reply:*",
                "2. ⬅️ Parent Title",
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
                "",
                "-----",
                "*Or reply:*",
                "2. ⬅️ Parent Title",
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
                "",
                "-----",
                "*Or reply:*",
                "2. ⬅️ Parent Title",
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
                "",
                "-----",
                "*Or reply:*",
                "2. ⬅️ Parent Title",
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
async def test_state_display_page_detail_next_error(
    tester: AppTester, contentrepo_api_mock, rapidpro_mock
):
    """
    If the user responds with an invalid prompt, then the error message should contain
    no title, a generic error, and options and footer the same as the original message
    """
    random.seed(0)
    tester.setup_state("state_display_page")
    tester.user.metadata["page_type"] = "detail"
    tester.user.metadata["selected_page_id"] = "111"
    tester.user.metadata["title"] = "title"
    tester.user.metadata["body"] = "body"
    tester.user.metadata["current_menu_level"] = 1
    tester.user.metadata["current_message_id"] = 1
    tester.user.metadata["suggested_content"] = {}

    tester.user.metadata["next_prompt"] = "Continue"

    await tester.user_input("invalid")

    tester.assert_message(
        "\n".join(
            [
                "Oops, looks like I don't have that option available.🤔Please try "
                "again - I'll get it if you use the number that matches your choice, "
                "promise.👍",
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
                "-----",
                "*Or reply:*",
                "1. ⬅️ Previous thing",
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
                "",
                "-----",
                "*Or reply:*",
                BACK_TO_MAIN,
                GET_HELP,
            ]
        )
    )


@pytest.mark.asyncio
async def test_state_display_page_detail_variations(
    tester: AppTester, contentrepo_api_mock, rapidpro_mock
):
    tester.setup_state("state_contentrepo_page")
    tester.user.metadata["selected_page_id"] = "1112"
    tester.user.metadata["current_message_id"] = 1
    tester.user.metadata["current_menu_level"] = 3
    tester.user.metadata["last_topic_viewed"] = "1"
    tester.user.metadata["parent_title"] = "Test Back"
    tester.user.metadata["suggested_content"] = {}
    tester.user.metadata["gender"] = "female"

    tester.user.session_id = 123
    await tester.user_input(session=Message.SESSION_EVENT.NEW)

    tester.assert_message(
        "\n".join(
            [
                "Main Menu 1 💊",
                "-----",
                "",
                "Message test content for females",
                "",
                "1. No, thanks",
                "",
                "-----",
                "*Or reply:*",
                "2. ⬅️ Parent Title",
                BACK_TO_MAIN,
                GET_HELP,
            ]
        )
    )


@pytest.fixture
async def contentrepo_api_mock2():
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

    async with run_sanic(app) as server:
        url = config.CONTENTREPO_API_URL
        config.CONTENTREPO_API_URL = f"http://{server.host}:{server.port}"
        yield server
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
                "",
                "-----",
                "*Or reply:*",
                BACK_TO_MAIN,
                GET_HELP,
            ]
        )
    )
