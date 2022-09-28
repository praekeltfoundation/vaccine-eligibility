import pytest
from sanic import Sanic, response

from vaccine.models import Message
from vaccine.testing import AppTester
from vaccine.vaccine_cert import Application, config


@pytest.fixture
def tester():
    return AppTester(Application)


@pytest.fixture
async def whatsapp_mock(sanic_client, tester):
    Sanic.test_mode = True
    app = Sanic("mock_whatsapp")

    @app.route("/v1/media/<media_id>", methods=["GET"])
    def valid_registration(request, media_id):
        return response.file(f"vaccine/data/{media_id}")

    client = await sanic_client(app)
    whatsapp_media_url = tester.application.whatsapp_media_url
    tester.application.whatsapp_media_url = (
        lambda media_id: f"http://{client.host}:{client.port}/v1/media/{media_id}"
    )
    yield client
    tester.application.whatsapp_media_url = whatsapp_media_url


@pytest.mark.asyncio
async def test_exit_keywords(tester: AppTester):
    await tester.user_input("menu")
    tester.assert_message("", session=Message.SESSION_EVENT.CLOSE)
    assert tester.application.messages[0].helper_metadata["automation_handle"] is True
    tester.assert_state(None)
    assert tester.user.answers == {}


@pytest.mark.asyncio
async def test_timeout(tester: AppTester):
    await tester.user_input(session=Message.SESSION_EVENT.CLOSE)
    tester.assert_message(
        "We haven't heard from you in while. This session is timed out due to "
        "inactivity. Send in the keyword *CERTIFICATE* to try again."
    )


@pytest.mark.asyncio
async def test_start(tester: AppTester):
    await tester.user_input(session=Message.SESSION_EVENT.NEW)
    tester.assert_message(
        "\n".join(
            [
                "*Vaccine certificate validation*",
                "",
                "Please send a photo that contains the QR code on your vaccine "
                "certificate",
            ]
        )
    )


@pytest.mark.asyncio
async def test_display_details(tester: AppTester, whatsapp_mock):
    await tester.user_input(
        None,
        transport_metadata={"message": {"type": "image", "image": {"id": "qr.jpg"}}},
    )
    tester.assert_message(
        "\n".join(
            [
                "The scanned vaccine certificate has the following details:",
                "Identification Type: RSAID",
                "Identification Value: 9001010001081",
                "Name: Test Name",
                "Date of Birth: 1990-01-01",
                "",
                "Vaccines:",
                "2021-08-23 Comirnaty ABC123DEF",
                "2021-10-07 Comirnaty GHI456JKL",
                "",
                "Reply *CERTIFICATE* if you want to check another vaccine certificate",
            ]
        ),
        session=Message.SESSION_EVENT.CLOSE,
    )


def test_whatsapp_media_url():
    config.API_HOST = "example.org"
    assert (
        Application.whatsapp_media_url("testid")
        == "https://example.org/v1/media/testid"
    )


@pytest.mark.asyncio
async def test_no_image(tester: AppTester, whatsapp_mock):
    await tester.user_input(None)
    tester.assert_message(
        "Sorry, that is not a photo. Please try sending a photo that contains the QR "
        "code on the vaccine certificate again, or reply *MENU* to quit."
    )


@pytest.mark.asyncio
async def test_no_qr(tester: AppTester, whatsapp_mock):
    await tester.user_input(
        None,
        transport_metadata={"message": {"type": "image", "image": {"id": "blank.jpg"}}},
    )
    tester.assert_message(
        "Sorry, we cannot find any QR codes in that photo. Please try again by sending "
        "another photo, or reply *MENU* to quit."
    )


@pytest.mark.asyncio
async def test_non_vaccine_qr(tester: AppTester, whatsapp_mock):
    await tester.user_input(
        None,
        transport_metadata={
            "message": {"type": "image", "image": {"id": "nonvaccineqr.jpg"}}
        },
    )
    tester.assert_message(
        "Sorry, the QR code is not a valid vaccine certificate QR code. Please try "
        "sending a photo that contains the vaccine certificate QR code, or reply "
        "*MENU* to quit."
    )


@pytest.mark.asyncio
async def test_multiple_qr(tester: AppTester, whatsapp_mock):
    await tester.user_input(
        None,
        transport_metadata={
            "message": {"type": "image", "image": {"id": "doubleqr.jpg"}}
        },
    )
    tester.assert_message(
        "Sorry, we found more than one QR code in that photo. Please try again by "
        "sending another photo that contains only a single QR code, or reply *MENU* to "
        "quit"
    )
