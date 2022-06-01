from urllib.parse import parse_qs, urlparse

import pytest
from sanic import Sanic, response

from vaccine.models import Message
from vaccine.testing import AppTester
from yal import config
from yal.main import Application


@pytest.fixture
def tester():
    return AppTester(Application)


def build_message_detail(id, title, subtitle, content, tags, has_children):
    return {
        "id": id,
        "title": title,
        "subtitle": subtitle,
        "body": {
            "message": 1,
            "next_message": None,
            "previous_message": None,
            "total_messages": 1,
            "text": {
                "type": "Whatsapp_Message",
                "value": {"message": content},
                "id": "111b8f05-be1b-4461-ac85-562930747336",
            },
            "revision": id,
        },
        "tags": tags,
        "has_children": has_children,
    }


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
                "subtitle",
                "Message test content 1",
                ["test"],
                False,
            )
        )

    @app.route("/api/v2/pages/222", methods=["GET"])
    def get_page_detail_222(request):
        app.requests.append(request)
        return response.json(
            build_message_detail(
                222,
                "Main Menu 2 🤝",
                "subtitle",
                "Message test content 2",
                ["test"],
                True,
            )
        )

    @app.route("/api/v2/pages/333", methods=["GET"])
    def get_page_detail_333(request):
        app.requests.append(request)
        return response.json(
            build_message_detail(
                333,
                "Sub menu 1",
                "subtitle",
                "Sub menu test content 2",
                ["test"],
                True,
            )
        )

    @app.route("/api/v2/pages/444", methods=["GET"])
    def get_page_detail_444(request):
        app.requests.append(request)
        return response.json(
            build_message_detail(
                444,
                "Sub menu 2",
                "subtitle",
                "Sub menu test content 2",
                ["test"],
                False,
            )
        )

    client = await sanic_client(app)
    url = config.CONTENTREPO_API_URL
    config.CONTENTREPO_API_URL = f"http://{client.host}:{client.port}"
    yield client
    config.CONTENTREPO_API_URL = url


@pytest.mark.asyncio
async def test_state_mainmenu_start(tester: AppTester, contentrepo_api_mock):
    tester.setup_state("state_mainmenu")
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
                "*📞 NEED HELP OR ADVICE?*",
                "1. Please call me!",
                "2. Find clinics and services",
                "-----",
                "*Main Menu 1 💊*",
                "3. Sub menu 1",
                "4. Sub menu 2",
                "-----",
                "*Main Menu 2 🤝*",
                "5. Sub menu 1",
                "6. Sub menu 2",
                "-----",
                "*🤔 WHAT's EVERYONE ELSE ASKING?*",
                "7. FAQs",
                "-----",
                "*⚙️ CHAT SETTINGS*",
                "8. Change/Update Your Personal Info",
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


@pytest.mark.asyncio
async def test_state_mainmenu_static(tester: AppTester, contentrepo_api_mock):
    tester.setup_state("state_mainmenu")
    await tester.user_input("1")

    tester.assert_num_messages(1)
    tester.assert_message("TODO: Please Call Me")

    assert [r.path for r in contentrepo_api_mock.app.requests] == [
        "/api/v2/pages",
        "/api/v2/pages",
        "/api/v2/pages",
    ]


@pytest.mark.asyncio
async def test_state_mainmenu_contentrepo(tester: AppTester, contentrepo_api_mock):
    tester.setup_state("state_mainmenu")
    await tester.user_input("4")

    question = "\n".join(
        [
            "*Sub menu 2*",
            "subtitle",
            "-----",
            "",
            "Sub menu test content 2",
            "",
            "-----",
            "Or reply:",
            "",
            "0. 🏠 Back to Main MENU",
            "# 🆘 Get HELP",
        ]
    )

    tester.assert_num_messages(1)
    tester.assert_message(question)

    print([r.path for r in contentrepo_api_mock.app.requests])
    assert [r.path for r in contentrepo_api_mock.app.requests] == [
        "/api/v2/pages",
        "/api/v2/pages",
        "/api/v2/pages",
        "/api/v2/pages/444",
    ]


@pytest.mark.asyncio
async def test_state_mainmenu_contentrepo_children(
    tester: AppTester, contentrepo_api_mock
):
    tester.setup_state("state_mainmenu")
    await tester.user_input("3")

    question = "\n".join(
        [
            "*Sub menu 1*",
            "subtitle",
            "-----",
            "",
            "Sub menu test content 2",
            "",
            "1. Sub menu 1",
            "2. Sub menu 2",
            "",
            "-----",
            "Or reply:",
            "",
            "0. 🏠 Back to Main MENU",
            "# 🆘 Get HELP",
        ]
    )

    tester.assert_num_messages(1)
    tester.assert_message(question)

    await tester.user_input("2")

    question = "\n".join(
        [
            "*Sub menu 2*",
            "subtitle",
            "-----",
            "",
            "Sub menu test content 2",
            "",
            "-----",
            "Or reply:",
            "",
            "0. 🏠 Back to Main MENU",
            "# 🆘 Get HELP",
        ]
    )

    tester.assert_num_messages(1)
    tester.assert_message(question)

    assert [r.path for r in contentrepo_api_mock.app.requests] == [
        "/api/v2/pages",
        "/api/v2/pages",
        "/api/v2/pages",
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
