import json

import pytest
from sanic import Sanic, response

from vaccine import real411_config as config
from vaccine.models import Message
from vaccine.real411 import Application
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
                "*REPORT* 📵 powered by ```Real411.org```",
                "",
                "There is a lot of information about COVID-19 being shared on "
                "WhatsApp. Some of this information is false and could be harmful. "
                "Report misleading or inaccurate information here to help stop its "
                "spread on WhatsApp.",
            ]
        ),
        buttons=["Learn more", "Continue"],
    )

    await tester.user_input("invalid")
    tester.assert_state("state_start")
    tester.assert_message(
        "This service works best when you use the options given. Please try using "
        "the buttons below or reply *0* to return the main *MENU*."
    )

    await tester.user_input("Continue")
    tester.assert_state("state_terms")


@pytest.mark.asyncio
async def test_tell_me_more(tester: AppTester):
    await tester.user_input("learn more")
    tester.assert_state("state_tell_me_more")
    tester.assert_message(
        "\n".join(
            [
                "*REPORT* 📵 powered by ```Real411.org``` allows you to report "
                "WhatsApp messages that include:",
                "- disinformation",
                "- hate speech",
                "- incitement to violence",
                "- harassment of a journalist",
                "",
                "*Disinformation* is false, inaccurate or misleading information that "
                "aims to cause public harm on purpose.",
                "",
                "*Hate speech* includes messages that intend to harm a person or "
                "group, or make them feel less than other people.",
                "",
                "*Incitement to violence* includes messages that encourage violence "
                "that could cause harm, damage or even death.",
                "",
                "*Harrassment of a journalist* includes messages to members of the "
                "media that aim to humiliate, shame, threaten or intimidate them.",
                "",
                "Use this service to report WhatsApp messages that were forwarded to "
                "you personally or to a WhatsApp group that your are a member of. You "
                "can report what you've seen on social media, websites, TV or radio at "
                "www.real411.org/complaints-create.",
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
    await tester.user_input("Continue")
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
                "*REPORT* 📵 powered by ```Real411.org```",
                "",
                "Your information is kept private and confidential. It is only used "
                "with your permission to report disinformation.",
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
                "*REPORT* 📵 Powered by ```Real411.org```",
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
            [
                "*REPORT* 📵 Powered by ```Real411.org```",
                "",
                "Reply with your FIRST NAME:",
            ]
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
            ["*REPORT* 📵 Powered by ```Real411.org```", "", "Reply with your SURNAME:"]
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
                "*REPORT* 📵 Powered by ```Real411.org```",
                "",
                "Please confirm that your full name is firstname surname",
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
                "*REPORT* 📵 powered by ```Real411.org```",
                "",
                "Please TYPE your EMAIL address. (Or type SKIP if you can't share an "
                "email address.)",
            ]
        )
    )

    await tester.user_input("invalid")
    tester.assert_message(
        "\n".join(
            [
                "*REPORT* 📵 powered by ```Real411.org```",
                "",
                "Please TYPE a valid EMAIL address or type *SKIP* if you can't share "
                "an email address",
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
                "*REPORT* 📵 powered by ```Real411.org```",
                "",
                "To report a WhatsApp message that contains misinformation about "
                "COVID-19, please type a description of the complaint in your own "
                "words OR simply forward the message that you would like to report.",
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
                "*REPORT* 📵 powered by ```Real411.org```",
                "",
                "Please share any extra information, such as screenshots, photos, "
                "voicenotes or links (or type SKIP)",
            ]
        )
    )

    await tester.user_input("SKIP")
    tester.assert_state("state_opt_in")


@pytest.mark.asyncio
async def test_media_invalid_mimetype(tester: AppTester):
    tester.setup_state("state_description")
    await tester.user_input(
        "test description",
        transport_metadata={
            "message": {"type": "document", "mime_type": "application/msword"}
        },
    )
    tester.assert_state("state_description")
    tester.assert_message(
        "\n".join(
            [
                "I'm afraid we cannot read the file that you sent through.",
                "",
                "We can only read video, image, document or audio files that have "
                "these letters at the end of the file name:",
                ".amr",
                ".aac",
                ".m4a",
                ".mp3",
                ".mp4",
                ".jpeg",
                ".png",
                ".pdf",
                ".ogg",
                ".wave",
                ".x-wav",
                "",
                "If you cannot send one of these files, don't worry. We will "
                "investigate based on the description of the problem that you already "
                "typed in.",
            ]
        )
    )


@pytest.mark.asyncio
async def test_opt_in(tester: AppTester):
    tester.setup_state("state_media")
    await tester.user_input("SKIP")
    tester.assert_state("state_opt_in")
    tester.assert_message(
        "\n".join(
            [
                "*REPORT* 📵 powered by ```Real411.org```",
                "",
                "To complete your report, please confirm that all the information "
                "you've given is accurate to the best of your knowledge and that you "
                "give ContactNDOH permission to send you a message about the outcome "
                "of your report",
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
                "Do you agree to share your report with Real411.org?",
            ]
        )
    )


@pytest.mark.asyncio
async def test_success(
    tester: AppTester, real411_mock, whatsapp_mock, healthcheck_mock
):
    await tester.user_input("Continue")  # start
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
                "*REPORT* 📵 Powered by ```Real411.org```",
                "_Complaint ID: WDM88J4P_",
                "",
                "Thank you for helping to stop the spread of inaccurate or misleading "
                "information!",
                "",
                "Look out for messages from us in the next few days",
                "",
                "To track the status of your report, visit https://example.org",
                "",
                "Reply 0 to return to the main MENU",
            ]
        ),
        session=Message.SESSION_EVENT.CLOSE,
    )
    [msg] = tester.fake_worker.outbound_messages
    assert msg.content == "\n".join(
        [
            "*REPORT* 📵 powered by ```Real411.org```",
            "",
            "Thank you for your submission",
            "⏳ Please wait while we process your submission to give you a reference "
            "number and a link to track your submission",
        ]
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
    await tester.user_input("Continue")  # start
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
        "email": "reporting@praekelt.org",
    }
    with open("vaccine/data/real411_placeholder.png", "rb") as f:
        assert upload.body == f.read()
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
                "*REPORT* 📵 powered by ```Real411.org```",
                "",
                "Your report will not be shared.",
                "",
                "If you have seen or heard anything on other platforms, including "
                "social media, websites or even TV or radio, you can also report them "
                "at www.real411.org/complaints-create.",
                "",
                "Reply *REPORT *to start over",
                "Reply *0 *to return to the main *MENU*",
            ]
        )
    )
