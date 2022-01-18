import json

import pytest
from sanic import Sanic, response

from vaccine import real411_config as config
from vaccine.models import Message
from vaccine.real411 import BLANK_PNG, Application
from vaccine.testing import AppTester


@pytest.fixture
def tester():
    return AppTester(Application)


@pytest.fixture
async def real411_mock(sanic_client):
    Sanic.test_mode = True
    app = Sanic("real411_mock")
    app.requests = []

    @app.route("/complaint-type", methods=["GET"])
    def complaint_type(request):
        with open("vaccine/tests/real411.json") as f:
            data = json.load(f)
        complaints = [
            c for c in data["ComplaintType"] if c["code"] == request.args.get("code")
        ]
        return response.json(
            {
                "success": True,
                "message": "",
                "data": {"rows": complaints, "total": len(complaints)},
                "errors": None,
            }
        )

    @app.route("/language", methods=["GET"])
    def language(request):
        with open("vaccine/tests/real411.json") as f:
            data = json.load(f)
        languages = [
            c for c in data["Language"] if c["code"] == request.args.get("code")
        ]
        return response.json(
            {
                "success": True,
                "message": "",
                "data": {"rows": languages, "total": len(languages)},
                "errors": None,
            }
        )

    @app.route("/source", methods=["GET"])
    def source(request):
        with open("vaccine/tests/real411.json") as f:
            data = json.load(f)
        sources = [c for c in data["Source"] if c["code"] == request.args.get("code")]
        return response.json(
            {
                "success": True,
                "message": "",
                "data": {"rows": sources, "total": len(sources)},
                "errors": None,
            }
        )

    @app.route("/file_upload", methods=["PUT"])
    def file_upload(request):
        app.requests.append(request)
        return response.text("")

    @app.route("/complaint", methods=["POST"])
    def submit(request):
        app.requests.append(request)
        file_count = len(request.json["file_names"])
        return response.json(
            {
                "success": True,
                "data": {
                    "complaint_ref": "WDM88J4P",
                    "file_urls": [
                        app.url_for("file_upload", _external=True)
                        for _ in range(file_count)
                    ],
                    "real411_backlink": "https://example.org",
                },
                "errors": None,
            }
        )

    @app.route("/complaint/finalize", methods=["POST"])
    def finalise(request):
        app.requests.append(request)
        return response.json(
            {"success": True, "message": "Complaint finalised", "errors": None}
        )

    client = await sanic_client(app)
    app.config.SERVER_NAME = f"http://{client.host}:{client.port}"
    url = config.REAL411_URL
    token = config.REAL411_TOKEN
    config.REAL411_URL = app.config.SERVER_NAME
    config.REAL411_TOKEN = "testtoken"
    yield client
    config.REAL411_URL = url
    config.REAL411_TOKEN = token


@pytest.fixture
async def whatsapp_mock(sanic_client):
    Sanic.test_mode = True
    app = Sanic("whatsapp_mock")
    app.requests = []

    @app.route("/v1/media/<media_id>", methods=["GET"])
    def get_media(request, media_id):
        app.requests.append(request)
        return response.raw(b"testfile")

    client = await sanic_client(app)
    url = config.WHATSAPP_URL
    token = config.WHATSAPP_TOKEN
    config.WHATSAPP_URL = f"http://{client.host}:{client.port}"
    config.WHATSAPP_TOKEN = "testtoken"
    yield client
    config.WHATSAPP_URL = url
    config.WHATSAPP_TOKEN = token


@pytest.fixture
async def healthcheck_mock(sanic_client):
    Sanic.test_mode = True
    app = Sanic("healthcheck_mock")
    app.requests = []

    @app.route("/v2/real411/complaint/", methods=["POST"])
    def store_complaint_ref(request):
        app.requests.append(request)
        return response.json({})

    client = await sanic_client(app)
    url = config.HEALTHCHECK_URL
    config.HEALTHCHECK_URL = f"http://{client.host}:{client.port}"
    yield client
    config.HEALTHCHECK_URL = url


@pytest.mark.asyncio
async def test_exit_keywords(tester: AppTester):
    await tester.user_input("Main Menu")
    tester.assert_message("", session=Message.SESSION_EVENT.CLOSE)
    assert tester.application.messages[0].helper_metadata["automation_handle"] is True
    tester.assert_state(None)
    assert tester.user.answers == {}


@pytest.mark.asyncio
async def test_timeout(tester: AppTester):
    await tester.user_input(session=Message.SESSION_EVENT.CLOSE)
    tester.assert_message(
        "We haven't heard from you in while. Reply *0* to return to the main *MENU*, "
        "or *REPORT* to try again."
    )


@pytest.mark.asyncio
async def test_start(tester: AppTester):
    await tester.user_input(session=Message.SESSION_EVENT.NEW)
    tester.assert_message(
        "\n".join(
            [
                "*REPORT* 📵 Powered by ```Real411```",
                "",
                "There is a lot of information going around on WhatsApp related to the "
                "COVID-19 pandemic. Some of this information may be false and "
                "potentially harmful. Help to stop the spread of inaccurate or "
                "misleading information on WhatsApp by reporting it here",
            ]
        ),
        buttons=["Tell me more", "View and Accept T&Cs"],
    )

    await tester.user_input("invalid")
    tester.assert_state("state_start")
    tester.assert_message(
        "This service works best when you use the options given. Please try using "
        "the buttons below or reply *0* to return the main *MENU*."
    )

    await tester.user_input("View and Accept T&Cs")
    tester.assert_state("state_terms")


@pytest.mark.asyncio
async def test_tell_me_more(tester: AppTester):
    await tester.user_input("tell me more")
    tester.assert_state("state_tell_me_more")
    tester.assert_message(
        "\n".join(
            [
                "*REPORT* 📵 Powered by ```Real411``` allows you to report digital "
                "offences encountered on WhatsApp.",
                "",
                "You can report 4 types of digital offences here namely, "
                "Disinformation, hate speech, incitement to violence and journalist "
                "harassment. Disinformation is false, inaccurate or misleading "
                "information designed, "
                "presented and promoted online to intentionally cause public harm. "
                "Hate speech suggests messages with malicious intent to harm or "
                "dehumanise and may lead to incitement of violence. Incitement is the "
                "encouragement of others to commit a crime, in this case violent "
                "actions, which may cause harm, damage or even death. Journalists can "
                "report unwanted conduct that is persistent or serious and demeans, "
                "humiliates or creates a hostile or intimidating environment to induce "
                "submission by actual or threatened adverse consequences.",
            ]
        )
    )

    await tester.user_input("invalid")
    tester.assert_state("state_tell_me_more")
    tester.assert_message(
        "This service works best when you use the options given. Please try using the "
        "buttons below."
    )

    await tester.user_input("continue")
    tester.assert_state("state_terms")


@pytest.mark.asyncio
async def test_terms(tester: AppTester):
    """
    PDF document with terms and conditions, and ask whether they accept
    """
    await tester.user_input("View and Accept T&Cs")
    tester.assert_state("state_terms")
    document = tester.application.messages.pop(0)
    assert (
        document.helper_metadata["document"]
        == "https://healthcheck-rasa-images.s3.af-south-1.amazonaws.com/"
        "Real411_Privacy+Policy_WhatsApp_02112021.docx.pdf"
    )
    tester.assert_message(
        "\n".join(
            [
                "*REPORT* 📵 Powered by ```Real411```",
                "",
                "Your information is kept private and confidential and only used with "
                "your consent for the purpose of reporting disinformation.",
                "",
                "Do you agree to the attached PRIVACY POLICY?",
            ]
        ),
        buttons=["I agree", "No thanks"],
    )

    await tester.user_input("invalid")
    tester.assert_message(
        "\n".join(
            [
                "This service works best when you use the options given. Try using the "
                "buttons below or reply *0* to return the main *MENU*.",
                "",
                "Do you agree to our PRIVACY POLICY?",
            ]
        )
    )

    await tester.user_input("I agree")
    tester.assert_state("state_first_name")


@pytest.mark.asyncio
async def test_refuse_terms(tester: AppTester):
    tester.setup_state("state_terms")
    await tester.user_input("no thanks")
    tester.assert_message(
        "\n".join(
            [
                "*REPORT* 📵 Powered by ```Real411```",
                "",
                "If you change your mind, type *REPORT* anytime.",
                "Reply *0* to return to the main *MENU*",
            ]
        ),
        session=Message.SESSION_EVENT.CLOSE,
    )


@pytest.mark.asyncio
async def test_first_name(tester: AppTester):
    tester.setup_state("state_terms")
    await tester.user_input("I agree")
    tester.assert_state("state_first_name")
    tester.assert_message(
        "\n".join(
            ["*REPORT* 📵 Powered by ```Real411```", "", "Reply with your FIRST NAME:"]
        )
    )

    await tester.user_input("test name")
    tester.assert_state("state_surname")


@pytest.mark.asyncio
async def test_surname(tester: AppTester):
    tester.setup_answer("state_first_name", "firstname")
    tester.setup_state("state_first_name")
    await tester.user_input("test name")
    tester.assert_state("state_surname")
    tester.assert_message(
        "\n".join(
            ["*REPORT* 📵 Powered by ```Real411```", "", "Reply with your SURNAME:"]
        )
    )

    await tester.user_input("test surname")
    tester.assert_state("state_confirm_name")


@pytest.mark.asyncio
async def test_confirm_name(tester: AppTester):
    tester.setup_answer("state_first_name", "firstname")
    tester.setup_state("state_surname")
    await tester.user_input("surname")
    tester.assert_state("state_confirm_name")
    tester.assert_message(
        "\n".join(
            [
                "*REPORT* 📵 Powered by ```Real411```",
                "",
                "Please confirm your full name as firstname surname",
            ]
        ),
        buttons=["Confirm", "Edit name"],
    )

    await tester.user_input("invalid")
    tester.assert_message(
        "\n".join(
            [
                "This service works best when you use the options given. Try using the "
                "buttons below or reply *0* to return the main *MENU*.",
                "",
                "Please confirm your full name as firstname surname",
            ]
        )
    )

    await tester.user_input("confirm")
    tester.assert_state("state_email")


@pytest.mark.asyncio
async def test_email(tester: AppTester):
    tester.setup_answer("state_first_name", "firstname")
    tester.setup_answer("state_surname", "surname")
    tester.setup_state("state_confirm_name")
    await tester.user_input("confirm")
    tester.assert_state("state_email")
    tester.assert_message(
        "\n".join(
            [
                "*REPORT* 📵 Powered by ```Real411```",
                "",
                "Please TYPE your EMAIL address. (Or type SKIP if you are unable to "
                "share an email address.)",
            ]
        )
    )

    await tester.user_input("invalid")
    tester.assert_message(
        "\n".join(
            [
                "*REPORT* 📵 Powered by ```Real411```",
                "",
                "Please TYPE a valid EMAIL address or type *SKIP* if you are unable to "
                "share an email address",
            ]
        )
    )

    await tester.user_input("skip")
    tester.assert_state("state_description")

    tester.setup_state("state_email")
    await tester.user_input("valid@example.org")
    tester.assert_state("state_description")


@pytest.mark.asyncio
async def test_description(tester: AppTester):
    tester.setup_state("state_email")
    await tester.user_input("test@example.org")
    tester.assert_state("state_description")
    tester.assert_message(
        "\n".join(
            [
                "*REPORT* 📵 Powered by ```Real411```",
                "",
                "Please describe the information being reported in your own words or "
                "simply forward a message that you would like to report:",
            ]
        )
    )

    await tester.user_input("test description")
    tester.assert_state("state_media")


@pytest.mark.asyncio
async def test_media(tester: AppTester):
    tester.setup_state("state_description")
    await tester.user_input("test description")
    tester.assert_state("state_media")
    tester.assert_message(
        "\n".join(
            [
                "*REPORT* 📵 Powered by ```Real411```",
                "",
                "Please share any additional information such as screenshots, photos, "
                "voicenotes or links (or type SKIP)",
            ]
        )
    )

    await tester.user_input("SKIP")
    tester.assert_state("state_opt_in")


@pytest.mark.asyncio
async def test_opt_in(tester: AppTester):
    tester.setup_state("state_media")
    await tester.user_input("SKIP")
    tester.assert_state("state_opt_in")
    tester.assert_message(
        "\n".join(
            [
                "*REPORT* 📵 Powered by ```Real411```",
                "",
                "To complete your report please confirm that all the information is "
                "accurate to the best of your knowledge and that you give ContactNDOH "
                "permission to send you message about the outcome of your report",
            ]
        ),
        buttons=["I agree", "No"],
    )

    await tester.user_input("invalid")
    tester.assert_message(
        "\n".join(
            [
                "This service works best when you use the options given. Please try "
                "using the buttons below or reply *0* to return the main *MENU*.",
                "",
                "Do you agree to share your report with Real411?",
            ]
        )
    )


@pytest.mark.asyncio
async def test_success(
    tester: AppTester, real411_mock, whatsapp_mock, healthcheck_mock
):
    await tester.user_input("View and Accept T&Cs")  # start
    await tester.user_input("I agree")  # terms
    await tester.user_input("first name")  # first_name
    await tester.user_input("surname")  # surname
    await tester.user_input("confirm")  # confirm name
    await tester.user_input("test@example.org")  # email
    await tester.user_input(
        "test video description",
        transport_metadata={
            "message": {
                "type": "video",
                "video": {"id": "vid1", "mime_type": "video/mp4"},
            }
        },
    )  # description
    await tester.user_input(
        "test image description",
        transport_metadata={
            "message": {
                "type": "image",
                "image": {"id": "img1", "mime_type": "image/jpeg"},
            }
        },
    )  # media
    await tester.user_input("I agree")  # opt_in
    tester.assert_message(
        "\n".join(
            [
                "*REPORT* 📵 Powered by ```Real411```",
                "",
                "Thank you for helping to stop the spread of inaccurate or misleading "
                "information!",
                "",
                "Look out for messages from us in the next few days",
                "",
                "Reply 0 to return to the main MENU",
            ]
        ),
        session=Message.SESSION_EVENT.CLOSE,
    )
    [submit, uploadvid, uploadimg, finalise] = real411_mock.app.requests
    assert submit.json == {
        "agree": True,
        "name": "first name surname",
        "phone": "+27820001001",
        "complaint_types": '[{"id": 5, "reason": "test video description\\n\\ntest '
        'image description"}]',
        "language": 13,
        "source": 1,
        "email": "test@example.org",
        "file_names": [
            {"name": "vid1", "type": "video/mp4"},
            {"name": "img1", "type": "image/jpeg"},
        ],
    }
    assert uploadvid.body == b"testfile"
    assert uploadvid.headers["content-type"] == "video/mp4"
    assert uploadimg.body == b"testfile"
    assert uploadimg.headers["content-type"] == "image/jpeg"
    assert finalise.json == {"ref": "WDM88J4P"}

    [complaint] = healthcheck_mock.app.requests
    assert complaint.json == {"complaint_ref": "WDM88J4P", "msisdn": "27820001001"}


@pytest.mark.asyncio
async def test_success_no_media(
    tester: AppTester, real411_mock, whatsapp_mock, healthcheck_mock
):
    """
    Uploads a blank 1x1 PNG if there is no media
    """
    await tester.user_input("View and Accept T&Cs")  # start
    await tester.user_input("I agree")  # terms
    await tester.user_input("first name")  # first_name
    await tester.user_input("surname")  # surname
    await tester.user_input("confirm")  # confirm name
    await tester.user_input("SKIP")  # email
    await tester.user_input("test description")  # description
    await tester.user_input("SKIP")  # media
    await tester.user_input("I agree")  # opt_in
    [submit, upload, finalise] = real411_mock.app.requests
    assert submit.json == {
        "agree": True,
        "name": "first name surname",
        "phone": "+27820001001",
        "complaint_types": '[{"id": 5, "reason": "test description\\n\\nSKIP"}]',
        "language": 13,
        "source": 1,
        "file_names": [{"name": "placeholder", "type": "image/png"}],
        "email": "placeholder@example.org",
    }
    assert upload.body == BLANK_PNG
    assert upload.headers["content-type"] == "image/png"
    assert finalise.json == {"ref": "WDM88J4P"}

    [complaint] = healthcheck_mock.app.requests
    assert complaint.json == {"complaint_ref": "WDM88J4P", "msisdn": "27820001001"}


@pytest.mark.asyncio
async def test_no_opt_in(tester: AppTester):
    tester.setup_state("state_opt_in")
    await tester.user_input("no")
    tester.assert_message(
        "\n".join(
            [
                "*REPORT* 📵 Powered by ```Real411```",
                "",
                "Your report will not be shared",
                "",
                "Reply *REPORT* to start over",
                "Reply *0* to return to the main *MENU*",
            ]
        )
    )
