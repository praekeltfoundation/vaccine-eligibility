import gzip
from datetime import date
from unittest import mock

import pytest
from sanic import Sanic, response

from vaccine.data.medscheme import config as m_config
from vaccine.data.suburbs import config as s_config
from vaccine.models import Message
from vaccine.testing import AppTester
from vaccine.vaccine_reg_whatsapp import Application, config


@pytest.fixture
def tester():
    return AppTester(Application)


@pytest.fixture
async def evds_mock(sanic_client):
    Sanic.test_mode = True
    app = Sanic("mock_turn")
    app.requests = []
    app.errors = 0
    app.errormax = 0

    @app.route("/api/private/evds-sa/person/8/record", methods=["POST"])
    def submit_record(request):
        app.requests.append(request)
        if app.errormax:
            if app.errors < app.errormax:
                app.errors += 1
                return response.json({}, status=500)
        return response.json({}, status=200)

    @app.route("/api/private/evds-sa/person/8/lookup/medscheme/1", methods=["GET"])
    def get_medschemes(request):
        with gzip.open("vaccine/data/medscheme.json.gz") as f:
            return response.raw(f.read(), content_type="application/json")

    @app.route("/api/private/evds-sa/person/8/lookup/location/1", methods=["GET"])
    def get_suburbs(request):
        with gzip.open("vaccine/data/suburbs.json.gz") as f:
            return response.raw(f.read(), content_type="application/json")

    client = await sanic_client(app)
    url = config.EVDS_URL
    username = config.EVDS_USERNAME
    password = config.EVDS_PASSWORD
    s_config.EVDS_URL = (
        m_config.EVDS_URL
    ) = config.EVDS_URL = f"http://{client.host}:{client.port}"
    s_config.EVDS_USERNAME = m_config.EVDS_USERNAME = config.EVDS_USERNAME = "test"
    s_config.EVDS_PASSWORD = m_config.EVDS_PASSWORD = config.EVDS_PASSWORD = "test"
    yield client
    s_config.EVDS_URL = m_config.EVDS_URL = config.EVDS_URL = url
    s_config.EVDS_USERNAME = m_config.EVDS_USERNAME = config.EVDS_USERNAME = username
    s_config.EVDS_PASSWORD = m_config.EVDS_PASSWORD = config.EVDS_PASSWORD = password


@pytest.fixture
async def eventstore_mock(sanic_client):
    Sanic.test_mode = True
    app = Sanic("mock_eventstore")
    app.requests = []

    @app.route("/v2/vaccineregistration/", methods=["POST"])
    def valid_registration(request):
        app.requests.append(request)
        return response.json({})

    client = await sanic_client(app)
    url = config.VACREG_EVENTSTORE_URL
    config.VACREG_EVENTSTORE_URL = f"http://{client.host}:{client.port}"
    yield client
    config.VACREG_EVENTSTORE_URL = url


@pytest.mark.asyncio
async def test_age_gate(tester: AppTester):
    """
    Should ask the user if they're over 60
    """
    await tester.user_input(session=Message.SESSION_EVENT.NEW)
    tester.assert_state("state_age_gate")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_age_gate_error(tester: AppTester):
    """
    Should show the error message on incorrect input
    """
    tester.setup_state("state_age_gate")
    await tester.user_input("invalid")
    tester.assert_state("state_age_gate")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_under_age_notification(tester: AppTester):
    """
    Should ask the user if they want a notification when it opens up
    """
    tester.setup_state("state_age_gate")
    await tester.user_input("no")
    tester.assert_state("state_under_age_notification")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_under_age_notification_error(tester: AppTester):
    """
    Should show the error message on incorrect input
    """
    tester.setup_state("state_under_age_notification")
    await tester.user_input("invalid")
    tester.assert_state("state_under_age_notification")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_under_age_notification_confirm(tester: AppTester):
    """
    Should confirm the selection and end the session
    """
    tester.setup_state("state_under_age_notification")
    await tester.user_input("yes")
    tester.assert_message(
        "Thank you for confirming", session=Message.SESSION_EVENT.CLOSE
    )
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_identification_type(tester: AppTester):
    tester.setup_state("state_age_gate")
    await tester.user_input("1")
    tester.assert_state("state_terms_and_conditions")
    tester.assert_num_messages(2)


@pytest.mark.asyncio
async def test_identification_type_invalid(tester: AppTester):
    tester.setup_state("state_identification_type")
    await tester.user_input("invalid")
    tester.assert_state("state_identification_type")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_identification_number(tester: AppTester):
    tester.setup_state("state_identification_type")
    await tester.user_input("rsa id number")
    tester.assert_state("state_identification_number")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_identification_number_invalid(tester: AppTester):
    tester.setup_state("state_identification_number")
    tester.setup_answer("state_identification_type", "rsa_id")
    await tester.user_input("9001010001089")
    tester.assert_state("state_identification_number")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_passport_country(tester: AppTester):
    tester.setup_state("state_identification_number")
    tester.setup_answer("state_identification_type", "passport")
    await tester.user_input("A1234567890")
    tester.assert_state("state_passport_country")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_passport_country_search(tester: AppTester):
    tester.setup_state("state_passport_country")
    await tester.user_input("cote d'ivory")
    tester.assert_state("state_passport_country_list")
    tester.assert_answer("state_passport_country", "cote d'ivory")
    tester.assert_message(
        "\n".join(
            [
                "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                "",
                "Please confirm your passport's COUNTRY of origin. REPLY with a "
                "NUMBER from the list below:",
                "1. Republic of Côte d'Ivoire",
                "2. British Indian Ocean Territory",
                "3. Plurinational State of Bolivia",
                "4. Other",
            ]
        )
    )


@pytest.mark.asyncio
async def test_passport_country_search_other(tester: AppTester):
    tester.setup_state("state_passport_country_list")
    tester.setup_answer("state_passport_country", "CI")
    await tester.user_input("other")
    tester.assert_num_messages(1)
    tester.assert_state("state_passport_country")


@pytest.mark.asyncio
async def test_passport_country_search_list_invalid(tester: AppTester):
    tester.setup_state("state_passport_country_list")
    tester.setup_answer("state_passport_country", "Côte d'Ivoire")
    await tester.user_input("invalid")
    tester.assert_num_messages(1)
    tester.assert_state("state_passport_country_list")


@pytest.mark.asyncio
async def test_said_date_and_sex_extraction(tester: AppTester):
    tester.setup_state("state_identification_number")
    tester.setup_answer("state_identification_type", "rsa_id")
    await tester.user_input("9001010001088")
    tester.assert_answer("state_dob_year", "1990")
    tester.assert_answer("state_dob_month", "1")
    tester.assert_answer("state_dob_day", "1")
    tester.assert_answer("state_gender", "Female")


@pytest.mark.asyncio
@mock.patch("vaccine.utils.get_today")
async def test_said_date_extraction_ambiguous(get_today, tester: AppTester):
    get_today.return_value = date(2020, 1, 1)
    tester.setup_state("state_identification_number")
    tester.setup_answer("state_identification_type", "rsa_id")
    await tester.user_input("0001010001087")
    tester.assert_no_answer("state_dob_year")
    tester.assert_answer("state_dob_month", "1")
    tester.assert_answer("state_dob_day", "1")


@pytest.mark.asyncio
@mock.patch("vaccine.utils.get_today")
async def test_gender(get_today, tester: AppTester):
    get_today.return_value = date(2120, 1, 1)
    tester.setup_state("state_dob_day")
    tester.setup_answer("state_dob_year", "1990")
    tester.setup_answer("state_dob_month", "1")
    await tester.user_input("1")
    tester.assert_num_messages(1)
    tester.assert_state("state_gender")


@pytest.mark.asyncio
@mock.patch("vaccine.utils.get_today")
async def test_gender_invalid(get_today, tester: AppTester):
    get_today.return_value = date(2120, 1, 1)
    tester.setup_state("state_gender")
    tester.setup_answer("state_dob_year", "1990")
    tester.setup_answer("state_dob_month", "1")
    tester.setup_answer("state_dob_day", "1")
    await tester.user_input("invalid")
    tester.assert_num_messages(1)
    tester.assert_state("state_gender")


@pytest.mark.asyncio
@mock.patch("vaccine.utils.get_today")
async def test_too_young(get_today, tester: AppTester):
    get_today.return_value = date(2020, 1, 1)
    tester.setup_state("state_dob_year")
    tester.setup_answer("state_dob_month", "1")
    tester.setup_answer("state_dob_day", "1")
    tester.setup_answer("state_identification_type", "passport")
    await tester.user_input("1990")
    tester.assert_num_messages(1)
    tester.assert_state("state_under_age_notification")


@pytest.mark.asyncio
async def test_dob_year(tester: AppTester):
    tester.setup_state("state_surname")
    await tester.user_input("test surname")
    tester.assert_num_messages(1)
    tester.assert_state("state_dob_year")


@pytest.mark.asyncio
async def test_dob_year_invalid(tester: AppTester):
    tester.setup_state("state_dob_year")
    await tester.user_input("invalid")
    tester.assert_state("state_dob_year")
    tester.assert_message(
        "\n".join(["⚠️  Please TYPE in only the YEAR you were born.", "Example _1980_"])
    )


@pytest.mark.asyncio
async def test_dob_year_not_match_id(tester: AppTester):
    tester.setup_state("state_dob_year")
    tester.setup_answer("state_identification_number", "9001010001088")
    tester.setup_answer("state_identification_type", "rsa_id")
    await tester.user_input("1991")
    tester.assert_state("state_dob_year")
    tester.assert_message(
        "The YEAR you have given does not match the YEAR of your ID number. Please "
        "try again"
    )


@pytest.mark.asyncio
async def test_dob_month(tester: AppTester):
    tester.setup_state("state_dob_year")
    tester.setup_answer("state_identification_type", "passport")
    await tester.user_input("1990")
    tester.assert_num_messages(1)
    tester.assert_state("state_dob_month")


@pytest.mark.asyncio
async def test_dob_month_error(tester: AppTester):
    tester.setup_state("state_dob_month")
    await tester.user_input("invalid")
    tester.assert_num_messages(1)
    tester.assert_state("state_dob_month")


@pytest.mark.asyncio
async def test_dob_day(tester: AppTester):
    tester.setup_state("state_dob_month")
    await tester.user_input("january")
    tester.assert_num_messages(1)
    tester.assert_state("state_dob_day")


@pytest.mark.asyncio
async def test_dob_day_invalid(tester: AppTester):
    tester.setup_state("state_dob_day")
    tester.setup_answer("state_dob_year", "1990")
    tester.setup_answer("state_dob_month", "2")
    await tester.user_input("29")
    tester.assert_num_messages(1)
    tester.assert_state("state_dob_day")


@pytest.mark.asyncio
async def test_first_name(tester: AppTester):
    tester.setup_state("state_passport_country_list")
    tester.setup_answer("state_passport_country", "south africa")
    await tester.user_input("1")
    tester.assert_num_messages(1)
    tester.assert_state("state_first_name")


@pytest.mark.asyncio
async def test_surname(tester: AppTester):
    tester.setup_state("state_first_name")
    await tester.user_input("firstname")
    tester.assert_num_messages(1)
    tester.assert_state("state_surname")
    tester.assert_answer("state_first_name", "firstname")


@pytest.mark.asyncio
@mock.patch("vaccine.utils.get_today")
async def test_skip_dob_and_gender(get_today, evds_mock, tester: AppTester):
    get_today.return_value = date(2120, 1, 1)
    tester.setup_state("state_surname")
    tester.setup_answer("state_dob_day", "1")
    tester.setup_answer("state_dob_month", "1")
    tester.setup_answer("state_dob_year", "1990")
    tester.setup_answer("state_gender", "male")
    await tester.user_input("test surname")
    tester.assert_num_messages(1)
    tester.assert_state("state_province_id")


@pytest.mark.asyncio
async def test_state_after_terms_and_conditions(tester: AppTester):
    tester.setup_state("state_terms_and_conditions")
    await tester.user_input("accept")
    tester.assert_num_messages(1)
    tester.assert_state("state_identification_type")


@pytest.mark.asyncio
async def test_province_invalid(evds_mock, tester: AppTester):
    tester.setup_state("state_province_id")
    await tester.user_input("invalid")
    tester.assert_num_messages(1)
    tester.assert_state("state_province_id")


@pytest.mark.asyncio
async def test_suburb_search(evds_mock, tester: AppTester):
    tester.setup_state("state_province_id")
    await tester.user_input("9")
    tester.assert_num_messages(1)
    tester.assert_state("state_suburb_search")
    tester.assert_answer("state_province_id", "western cape")


@pytest.mark.asyncio
async def test_suburb(evds_mock, tester: AppTester):
    tester.setup_state("state_suburb_search")
    tester.setup_answer("state_province_id", "western cape")
    await tester.user_input("tableview")
    tester.assert_message(
        "\n".join(
            [
                "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                "",
                "Please REPLY with a NUMBER to confirm your location:",
                "1. Table View, Blouberg",
                "2. Other",
            ]
        )
    )
    tester.assert_state("state_suburb")


@pytest.mark.asyncio
async def test_province_no_results(evds_mock, tester: AppTester):
    tester.setup_state("state_suburb_search")
    tester.setup_answer("state_province_id", "western cape")
    await tester.user_input("invalid")
    tester.assert_message(
        "\n".join(
            [
                "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                "",
                "⚠️ Your suburb could not be found. Please try again by selecting your "
                "province",
                "",
                "Select your province",
                "1. Eastern Cape",
                "2. Free State",
                "3. Gauteng",
                "4. Kwazulu-natal",
                "5. Limpopo",
                "6. Mpumalanga",
                "7. North West",
                "8. Northern Cape",
                "9. Western Cape",
            ]
        )
    )
    tester.assert_state("state_province_no_results")


@pytest.mark.asyncio
async def test_suburb_search_no_results(evds_mock, tester: AppTester):
    tester.setup_state("state_province_no_results")
    await tester.user_input("western cape")
    tester.assert_num_messages(1)
    tester.assert_state("state_suburb_search")
    tester.assert_answer("state_province_id", "western cape")


@pytest.mark.asyncio
async def test_municipality(evds_mock, tester: AppTester):
    tester.setup_state("state_suburb_search")
    tester.setup_answer("state_province_id", "eastern cape")
    await tester.user_input("mandela")
    tester.assert_message(
        "\n".join(
            [
                "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                "",
                "Please REPLY with a NUMBER to confirm your MUNICIPALITY:",
                "1. Buffalo City",
                "2. Enoch Mgijima",
                "3. Great Kei",
                "4. King Sabata Dalindyebo",
                "5. Nelson Mandela Bay",
                "6. Raymond Mhlaba",
                "7. Umzimvubu",
                "8. Mbizana",
                "9. Mnquma",
                "10. Other",
            ]
        )
    )
    tester.assert_state("state_municipality")


@pytest.mark.asyncio
async def test_municipality_other(evds_mock, tester: AppTester):
    tester.setup_state("state_municipality")
    tester.setup_answer("state_province_id", "eastern cape")
    tester.setup_answer("state_suburb_search", "mandela")
    await tester.user_input("other")
    tester.assert_state("state_suburb_search")


@pytest.mark.asyncio
async def test_municipality_plumstead(evds_mock, tester: AppTester):
    tester.setup_state("state_suburb_search")
    tester.setup_answer("state_province_id", "western cape")
    await tester.user_input("plumstead")
    tester.assert_message(
        "\n".join(
            [
                "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                "",
                "Please REPLY with a NUMBER to confirm your location:",
                "1. Plumstead, Cape Town",
                "2. Other",
            ]
        )
    )
    tester.assert_state("state_suburb")


@pytest.mark.asyncio
async def test_suburb_with_municipality(evds_mock, tester: AppTester):
    tester.setup_state("state_municipality")
    tester.setup_answer("state_province_id", "eastern cape")
    tester.setup_answer("state_suburb_search", "mandela")
    await tester.user_input("Buffalo City")
    tester.assert_message(
        "\n".join(
            [
                "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                "",
                "Please REPLY with a NUMBER to confirm your location:",
                "1. Mandela Park, Mandela Park",
                "2. Other",
            ]
        )
    )
    tester.assert_state("state_suburb")


@pytest.mark.asyncio
async def test_suburb_error(evds_mock, tester: AppTester):
    tester.setup_state("state_suburb")
    tester.setup_answer("state_province_id", "western cape")
    tester.setup_answer("state_suburb_search", "tableview")
    await tester.user_input("invalid")
    tester.assert_num_messages(1)
    tester.assert_state("state_suburb")


@pytest.mark.asyncio
async def test_suburb_other(evds_mock, tester: AppTester):
    tester.setup_state("state_suburb")
    tester.setup_answer("state_province_id", "western cape")
    tester.setup_answer("state_suburb_search", "tableview")
    await tester.user_input("other")
    tester.assert_num_messages(1)
    tester.assert_state("state_province_id")


@pytest.mark.asyncio
async def test_suburb_value(evds_mock, tester: AppTester):
    tester.setup_state("state_suburb")
    tester.setup_answer("state_province_id", "western cape")
    tester.setup_answer("state_suburb_search", "tableview")
    await tester.user_input("1")
    tester.assert_num_messages(1)
    tester.assert_state("state_self_registration")


@pytest.mark.asyncio
async def test_self_registration(evds_mock, tester: AppTester):
    tester.setup_state("state_suburb")
    tester.setup_answer("state_province_id", "western cape")
    tester.setup_answer("state_suburb_search", "tableview")
    await tester.user_input("1")
    tester.assert_message(
        "\n".join(
            [
                "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                "",
                "We will use your cell phone number to send you notifications and "
                "updates via WhatsApp and/or SMS about getting vaccinated.",
                "",
                "Can we use 082 000 1001?",
                "1. Yes",
                "2. No",
            ]
        )
    )
    tester.assert_state("state_self_registration")


@pytest.mark.asyncio
async def test_self_registration_invalid(tester: AppTester):
    tester.setup_state("state_self_registration")
    await tester.user_input("invalid")
    tester.assert_num_messages(1)
    tester.assert_state("state_self_registration")


@pytest.mark.asyncio
async def test_phone_number(tester: AppTester):
    tester.setup_state("state_self_registration")
    await tester.user_input("no")
    tester.assert_num_messages(1)
    tester.assert_state("state_phone_number")


@pytest.mark.asyncio
async def test_phone_number_invalid(tester: AppTester):
    tester.setup_state("state_phone_number")
    await tester.user_input("invalid")
    tester.assert_num_messages(1)
    tester.assert_state("state_phone_number")


@pytest.mark.asyncio
async def test_vaccination_time(tester: AppTester):
    tester.setup_state("state_medical_aid_number")
    await tester.user_input("A1234567890")
    tester.assert_num_messages(1)
    tester.assert_state("state_vaccination_time")


@pytest.mark.asyncio
async def test_vaccination_time_invalid(tester: AppTester):
    tester.setup_state("state_vaccination_time")
    await tester.user_input("invalid")
    tester.assert_num_messages(1)
    tester.assert_state("state_vaccination_time")


@pytest.mark.asyncio
async def test_medical_aid_search(tester: AppTester):
    tester.setup_state("state_medical_aid")
    await tester.user_input("yes")
    tester.assert_num_messages(1)
    tester.assert_state("state_medical_aid_search")


@pytest.mark.asyncio
async def test_medical_aid_list_1(evds_mock, tester: AppTester):
    tester.setup_state("state_medical_aid_search")
    await tester.user_input("discovery")
    tester.assert_state("state_medical_aid_list")
    tester.assert_message(
        "\n".join(
            [
                "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                "",
                "Please confirm your Medical Aid Provider. REPLY with a NUMBER from "
                "the list below:",
                "1. Discovery Health Medical Scheme",
                "2. Aeci Medical Aid Society",
                "3. BMW Employees Medical Aid Society",
                "4. None of these",
            ]
        )
    )


@pytest.mark.asyncio
async def test_medical_aid_list_2(evds_mock, tester: AppTester):
    tester.setup_state("state_medical_aid_search")
    await tester.user_input("tsogo sun")
    tester.assert_state("state_medical_aid_list")
    tester.assert_message(
        "\n".join(
            [
                "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                "",
                "Please confirm your Medical Aid Provider. REPLY with a NUMBER from "
                "the list below:",
                "1. Tsogo Sun Group Medical Scheme",
                "2. Golden Arrows Employees Medical Benefit Fund",
                "3. Engen Medical Benefit Fund",
                "4. None of these",
            ]
        )
    )


@pytest.mark.asyncio
async def test_medical_aid_list_3(evds_mock, tester: AppTester):
    tester.setup_state("state_medical_aid_search")
    await tester.user_input("de beers")
    tester.assert_state("state_medical_aid_list")
    tester.assert_message(
        "\n".join(
            [
                "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                "",
                "Please confirm your Medical Aid Provider. REPLY with a NUMBER from "
                "the list below:",
                "1. De Beers Benefit Society",
                "2. BMW Employees Medical Aid Society",
                "3. Government Employees Medical Scheme (GEMS)",
                "4. None of these",
            ]
        )
    )


@pytest.mark.asyncio
async def test_medical_aid_list_other(evds_mock, tester: AppTester):
    tester.setup_state("state_medical_aid_list")
    tester.setup_answer("state_medical_aid_search", "discovery")
    await tester.user_input("4")
    tester.assert_state("state_medical_aid")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_medical_aid_number(evds_mock, tester: AppTester):
    tester.setup_state("state_medical_aid_list")
    tester.setup_answer("state_medical_aid_search", "discovery")
    await tester.user_input("1")
    tester.assert_state("state_medical_aid_number")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_medical_aid(tester: AppTester):
    tester.setup_state("state_email_address")
    await tester.user_input("test@example.org")
    tester.assert_state("state_medical_aid")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_medical_aid_invalid(tester: AppTester):
    tester.setup_state("state_medical_aid")
    await tester.user_input("invalid")
    tester.assert_state("state_medical_aid")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_email_address(tester: AppTester):
    tester.setup_state("state_self_registration")
    await tester.user_input("yes")
    tester.assert_state("state_email_address")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_email_skip(tester: AppTester):
    tester.setup_state("state_email_address")
    await tester.user_input("skip")
    tester.assert_state("state_medical_aid")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_email_invalid(tester: AppTester):
    tester.setup_state("state_email_address")
    await tester.user_input("invalid@")
    tester.assert_state("state_email_address")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_email_invalid_2(tester: AppTester):
    tester.setup_state("state_email_address")
    await tester.user_input("invalid")
    tester.assert_state("state_email_address")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_terms_and_conditions(tester: AppTester):
    tester.setup_state("state_age_gate")
    await tester.user_input("1")
    tester.assert_state("state_terms_and_conditions")
    tester.assert_num_messages(2)
    assert "document" in tester.application.messages[0].helper_metadata


@pytest.mark.asyncio
async def test_terms_and_conditions_invalid(tester: AppTester):
    tester.setup_state("state_terms_and_conditions")
    await tester.user_input("invalid")
    tester.assert_state("state_terms_and_conditions")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_terms_and_conditions_summary(tester: AppTester):
    tester.setup_state("state_terms_and_conditions")
    await tester.user_input("read summary")
    tester.assert_state("state_terms_and_conditions_summary")
    tester.assert_num_messages(1)


@pytest.mark.asyncio
async def test_no_terms(tester: AppTester):
    tester.setup_state("state_terms_and_conditions_summary")
    await tester.user_input("no")
    tester.assert_message(
        "\n".join(
            [
                "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                "",
                "Thank you. If you change your mind, type *REGISTER* to restart your "
                "registration session",
            ]
        ),
        session=Message.SESSION_EVENT.CLOSE,
    )


@pytest.mark.asyncio
async def test_state_success(evds_mock, eventstore_mock, tester: AppTester):
    tester.setup_state("state_vaccination_time")
    tester.setup_answer("state_dob_year", "1960")
    tester.setup_answer("state_dob_month", "1")
    tester.setup_answer("state_dob_day", "1")
    tester.setup_answer("state_vaccination_time", "weekday_morning")
    tester.setup_answer("state_suburb", "d114778e-c590-4a08-894e-0ddaefc5759e")
    tester.setup_answer("state_province_id", "e32298eb-17b4-471e-8d9b-ba093c6afc7c")
    tester.setup_answer("state_gender", "Other")
    tester.setup_answer("state_surname", "test surname")
    tester.setup_answer("state_first_name", "test first name")
    tester.setup_answer("state_identification_type", "rsa_id")
    tester.setup_answer("state_identification_number", " 6001010001081 ")
    tester.setup_answer("state_medical_aid", "state_vaccination_time")
    tester.setup_answer("state_email_address", "SKIP")
    await tester.user_input("1")
    tester.assert_message(
        "\n".join(
            [
                "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                "",
                "Congratulations! You successfully registered with the National "
                "Department of Health to get a COVID-19 vaccine.",
                "",
                "Look out for messages from this number (060 012 3456) on WhatsApp OR "
                "on SMS/email. We will update you with important information about "
                "your appointment and what to expect.",
            ]
        ),
        session=Message.SESSION_EVENT.CLOSE,
    )

    [requests] = evds_mock.app.requests
    assert requests.json == {
        "gender": "Other",
        "surname": "test surname",
        "firstName": "test first name",
        "dateOfBirth": "1960-01-01",
        "mobileNumber": "27820001001",
        "preferredVaccineScheduleTimeOfDay": "morning",
        "preferredVaccineScheduleTimeOfWeek": "weekday",
        "preferredVaccineLocation": {
            "value": "d114778e-c590-4a08-894e-0ddaefc5759e",
            "text": "Diep River",
        },
        "termsAndConditionsAccepted": True,
        "iDNumber": "6001010001081",
        "medicalAidMember": False,
        "sourceId": "aeb8444d-cfa4-4c52-bfaf-eed1495124b7",
    }

    [requests] = eventstore_mock.app.requests
    assert requests.json == {
        "msisdn": "+27820001001",
        "source": "WhatsApp 27820001002",
        "gender": "Other",
        "first_name": "test first name",
        "last_name": "test surname",
        "date_of_birth": "1960-01-01",
        "preferred_time": "morning",
        "preferred_date": "weekday",
        "preferred_location_id": "d114778e-c590-4a08-894e-0ddaefc5759e",
        "preferred_location_name": "Diep River",
        "id_number": "6001010001081",
        "data": {},
    }


@pytest.mark.asyncio
async def test_state_success_international_phonenumber(
    evds_mock, eventstore_mock, tester: AppTester
):
    tester.setup_state("state_vaccination_time")
    tester.setup_user_address("32470001001")
    tester.setup_answer("state_dob_year", "1960")
    tester.setup_answer("state_dob_month", "1")
    tester.setup_answer("state_dob_day", "1")
    tester.setup_answer("state_vaccination_time", "weekday_morning")
    tester.setup_answer("state_suburb", "d114778e-c590-4a08-894e-0ddaefc5759e")
    tester.setup_answer("state_province_id", "e32298eb-17b4-471e-8d9b-ba093c6afc7c")
    tester.setup_answer("state_gender", "Other")
    tester.setup_answer("state_surname", "test surname")
    tester.setup_answer("state_first_name", "test first name")
    tester.setup_answer("state_identification_type", "rsa_id")
    tester.setup_answer("state_identification_number", "6001010001081")
    tester.setup_answer("state_medical_aid", "state_vaccination_time")
    tester.setup_answer("state_email_address", "SKIP")
    await tester.user_input("1")
    tester.assert_message(
        "\n".join(
            [
                "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                "",
                "Congratulations! You successfully registered with the National "
                "Department of Health to get a COVID-19 vaccine.",
                "",
                "Look out for messages from this number (060 012 3456) on WhatsApp OR "
                "on SMS/email. We will update you with important information about "
                "your appointment and what to expect.",
            ]
        ),
        session=Message.SESSION_EVENT.CLOSE,
    )

    [requests] = evds_mock.app.requests
    assert requests.json == {
        "gender": "Other",
        "surname": "test surname",
        "firstName": "test first name",
        "dateOfBirth": "1960-01-01",
        "mobileNumber": "32470001001",
        "preferredVaccineScheduleTimeOfDay": "morning",
        "preferredVaccineScheduleTimeOfWeek": "weekday",
        "preferredVaccineLocation": {
            "value": "d114778e-c590-4a08-894e-0ddaefc5759e",
            "text": "Diep River",
        },
        "termsAndConditionsAccepted": True,
        "iDNumber": "6001010001081",
        "medicalAidMember": False,
        "sourceId": "aeb8444d-cfa4-4c52-bfaf-eed1495124b7",
    }

    [requests] = eventstore_mock.app.requests
    assert requests.json == {
        "msisdn": "+32470001001",
        "source": "WhatsApp 27820001002",
        "gender": "Other",
        "first_name": "test first name",
        "last_name": "test surname",
        "date_of_birth": "1960-01-01",
        "preferred_time": "morning",
        "preferred_date": "weekday",
        "preferred_location_id": "d114778e-c590-4a08-894e-0ddaefc5759e",
        "preferred_location_name": "Diep River",
        "id_number": "6001010001081",
        "data": {},
    }


@pytest.mark.asyncio
async def test_state_success_passport(evds_mock, eventstore_mock, tester: AppTester):
    tester.setup_state("state_vaccination_time")
    tester.setup_answer("state_dob_year", "1960")
    tester.setup_answer("state_dob_month", "1")
    tester.setup_answer("state_dob_day", "1")
    tester.setup_answer("state_vaccination_time", "weekday_morning")
    tester.setup_answer("state_suburb", "d114778e-c590-4a08-894e-0ddaefc5759e")
    tester.setup_answer("state_province_id", "e32298eb-17b4-471e-8d9b-ba093c6afc7c")
    tester.setup_answer("state_gender", "Other")
    tester.setup_answer("state_surname", "test surname")
    tester.setup_answer("state_first_name", "test first name")
    tester.setup_answer("state_identification_type", "passport")
    tester.setup_answer("state_identification_number", "A1234567890")
    tester.setup_answer("state_passport_country", "south africa")
    tester.setup_answer("state_passport_country_list", "ZA")
    tester.setup_answer("state_medical_aid", "state_vaccination_time")
    tester.setup_answer("state_email_address", "SKIP")
    await tester.user_input("1")
    tester.assert_message(
        "\n".join(
            [
                "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                "",
                "Congratulations! You successfully registered with the National "
                "Department of Health to get a COVID-19 vaccine.",
                "",
                "Look out for messages from this number (060 012 3456) on WhatsApp OR "
                "on SMS/email. We will update you with important information about "
                "your appointment and what to expect.",
            ]
        ),
        session=Message.SESSION_EVENT.CLOSE,
    )

    [requests] = evds_mock.app.requests
    assert requests.json == {
        "gender": "Other",
        "surname": "test surname",
        "firstName": "test first name",
        "dateOfBirth": "1960-01-01",
        "mobileNumber": "27820001001",
        "preferredVaccineScheduleTimeOfDay": "morning",
        "preferredVaccineScheduleTimeOfWeek": "weekday",
        "preferredVaccineLocation": {
            "value": "d114778e-c590-4a08-894e-0ddaefc5759e",
            "text": "Diep River",
        },
        "termsAndConditionsAccepted": True,
        "passportNumber": "A1234567890",
        "passportCountry": "ZA",
        "medicalAidMember": False,
        "sourceId": "aeb8444d-cfa4-4c52-bfaf-eed1495124b7",
    }
    [requests] = eventstore_mock.app.requests
    assert requests.json == {
        "msisdn": "+27820001001",
        "source": "WhatsApp 27820001002",
        "gender": "Other",
        "first_name": "test first name",
        "last_name": "test surname",
        "date_of_birth": "1960-01-01",
        "preferred_time": "morning",
        "preferred_date": "weekday",
        "preferred_location_id": "d114778e-c590-4a08-894e-0ddaefc5759e",
        "preferred_location_name": "Diep River",
        "passport_number": "A1234567890",
        "passport_country": "ZA",
        "data": {},
    }


@pytest.mark.asyncio
async def test_state_success_asylum_seeker(
    evds_mock, eventstore_mock, tester: AppTester
):
    tester.setup_state("state_vaccination_time")
    tester.setup_answer("state_dob_year", "1960")
    tester.setup_answer("state_dob_month", "1")
    tester.setup_answer("state_dob_day", "1")
    tester.setup_answer("state_vaccination_time", "weekday_morning")
    tester.setup_answer("state_suburb", "d114778e-c590-4a08-894e-0ddaefc5759e")
    tester.setup_answer("state_province_id", "e32298eb-17b4-471e-8d9b-ba093c6afc7c")
    tester.setup_answer("state_gender", "Other")
    tester.setup_answer("state_surname", "test surname")
    tester.setup_answer("state_first_name", "test first name")
    tester.setup_answer("state_identification_type", "asylum_seeker")
    tester.setup_answer("state_identification_number", "A1234567890")
    tester.setup_answer("state_medical_aid", "state_vaccination_time")
    tester.setup_answer("state_email_address", "SKIP")
    await tester.user_input("1")
    tester.assert_message(
        "\n".join(
            [
                "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                "",
                "Congratulations! You successfully registered with the National "
                "Department of Health to get a COVID-19 vaccine.",
                "",
                "Look out for messages from this number (060 012 3456) on WhatsApp OR "
                "on SMS/email. We will update you with important information about "
                "your appointment and what to expect.",
            ]
        ),
        session=Message.SESSION_EVENT.CLOSE,
    )

    [requests] = evds_mock.app.requests
    assert requests.json == {
        "gender": "Other",
        "surname": "test surname",
        "firstName": "test first name",
        "dateOfBirth": "1960-01-01",
        "mobileNumber": "27820001001",
        "preferredVaccineScheduleTimeOfDay": "morning",
        "preferredVaccineScheduleTimeOfWeek": "weekday",
        "preferredVaccineLocation": {
            "value": "d114778e-c590-4a08-894e-0ddaefc5759e",
            "text": "Diep River",
        },
        "termsAndConditionsAccepted": True,
        "refugeeNumber": "A1234567890",
        "medicalAidMember": False,
        "sourceId": "aeb8444d-cfa4-4c52-bfaf-eed1495124b7",
    }
    [requests] = eventstore_mock.app.requests
    assert requests.json == {
        "msisdn": "+27820001001",
        "source": "WhatsApp 27820001002",
        "gender": "Other",
        "first_name": "test first name",
        "last_name": "test surname",
        "date_of_birth": "1960-01-01",
        "preferred_time": "morning",
        "preferred_date": "weekday",
        "preferred_location_id": "d114778e-c590-4a08-894e-0ddaefc5759e",
        "preferred_location_name": "Diep River",
        "asylum_seeker_number": "A1234567890",
        "data": {},
    }


@pytest.mark.asyncio
async def test_state_success_refugee(evds_mock, eventstore_mock, tester: AppTester):
    tester.setup_state("state_vaccination_time")
    tester.setup_answer("state_dob_year", "1960")
    tester.setup_answer("state_dob_month", "1")
    tester.setup_answer("state_dob_day", "1")
    tester.setup_answer("state_vaccination_time", "weekday_morning")
    tester.setup_answer("state_suburb", "d114778e-c590-4a08-894e-0ddaefc5759e")
    tester.setup_answer("state_province_id", "e32298eb-17b4-471e-8d9b-ba093c6afc7c")
    tester.setup_answer("state_gender", "Other")
    tester.setup_answer("state_surname", "test surname")
    tester.setup_answer("state_first_name", "test first name")
    tester.setup_answer("state_identification_type", "refugee")
    tester.setup_answer("state_identification_number", "A1234567890")
    tester.setup_answer("state_medical_aid", "state_vaccination_time")
    tester.setup_answer("state_email_address", "SKIP")
    await tester.user_input("1")
    tester.assert_message(
        "\n".join(
            [
                "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                "",
                "Congratulations! You successfully registered with the National "
                "Department of Health to get a COVID-19 vaccine.",
                "",
                "Look out for messages from this number (060 012 3456) on WhatsApp OR "
                "on SMS/email. We will update you with important information about "
                "your appointment and what to expect.",
            ]
        ),
        session=Message.SESSION_EVENT.CLOSE,
    )

    [requests] = evds_mock.app.requests
    assert requests.json == {
        "gender": "Other",
        "surname": "test surname",
        "firstName": "test first name",
        "dateOfBirth": "1960-01-01",
        "mobileNumber": "27820001001",
        "preferredVaccineScheduleTimeOfDay": "morning",
        "preferredVaccineScheduleTimeOfWeek": "weekday",
        "preferredVaccineLocation": {
            "value": "d114778e-c590-4a08-894e-0ddaefc5759e",
            "text": "Diep River",
        },
        "termsAndConditionsAccepted": True,
        "refugeeNumber": "A1234567890",
        "medicalAidMember": False,
        "sourceId": "aeb8444d-cfa4-4c52-bfaf-eed1495124b7",
    }
    [requests] = eventstore_mock.app.requests
    assert requests.json == {
        "msisdn": "+27820001001",
        "source": "WhatsApp 27820001002",
        "gender": "Other",
        "first_name": "test first name",
        "last_name": "test surname",
        "date_of_birth": "1960-01-01",
        "preferred_time": "morning",
        "preferred_date": "weekday",
        "preferred_location_id": "d114778e-c590-4a08-894e-0ddaefc5759e",
        "preferred_location_name": "Diep River",
        "refugee_number": "A1234567890",
        "data": {},
    }


@pytest.mark.asyncio
async def test_state_success_temporary_failure(evds_mock, tester: AppTester):
    evds_mock.app.errormax = 1
    tester.setup_state("state_vaccination_time")
    tester.setup_answer("state_dob_year", "1960")
    tester.setup_answer("state_dob_month", "1")
    tester.setup_answer("state_dob_day", "1")
    tester.setup_answer("state_vaccination_time", "weekday_morning")
    tester.setup_answer("state_suburb", "d114778e-c590-4a08-894e-0ddaefc5759e")
    tester.setup_answer("state_province_id", "e32298eb-17b4-471e-8d9b-ba093c6afc7c")
    tester.setup_answer("state_gender", "Other")
    tester.setup_answer("state_surname", "test surname")
    tester.setup_answer("state_first_name", "test first name")
    tester.setup_answer("state_identification_type", "passport")
    tester.setup_answer("state_identification_number", "A1234567890")
    tester.setup_answer("state_passport_country", "south africa")
    tester.setup_answer("state_passport_country_list", "ZA")
    tester.setup_answer("state_medical_aid", "state_vaccination_time")
    tester.setup_answer("state_email_address", "test@example.org")
    await tester.user_input("1")
    tester.assert_message(
        "\n".join(
            [
                "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                "",
                "Congratulations! You successfully registered with the National "
                "Department of Health to get a COVID-19 vaccine.",
                "",
                "Look out for messages from this number (060 012 3456) on WhatsApp OR "
                "on SMS/email. We will update you with important information about "
                "your appointment and what to expect.",
            ]
        ),
        session=Message.SESSION_EVENT.CLOSE,
    )

    requests = evds_mock.app.requests
    assert len(requests) == 2
    assert requests[-1].json == {
        "gender": "Other",
        "surname": "test surname",
        "firstName": "test first name",
        "dateOfBirth": "1960-01-01",
        "mobileNumber": "27820001001",
        "preferredVaccineScheduleTimeOfDay": "morning",
        "preferredVaccineScheduleTimeOfWeek": "weekday",
        "preferredVaccineLocation": {
            "value": "d114778e-c590-4a08-894e-0ddaefc5759e",
            "text": "Diep River",
        },
        "termsAndConditionsAccepted": True,
        "passportNumber": "A1234567890",
        "passportCountry": "ZA",
        "emailAddress": "test@example.org",
        "medicalAidMember": False,
        "sourceId": "aeb8444d-cfa4-4c52-bfaf-eed1495124b7",
    }


@pytest.mark.asyncio
async def test_state_error(evds_mock, tester: AppTester):
    evds_mock.app.errormax = 3
    tester.setup_state("state_vaccination_time")
    tester.setup_answer("state_dob_year", "1960")
    tester.setup_answer("state_dob_month", "1")
    tester.setup_answer("state_dob_day", "1")
    tester.setup_answer("state_gender", "Other")
    tester.setup_answer("state_suburb", "d114778e-c590-4a08-894e-0ddaefc5759e")
    tester.setup_answer("state_province_id", "e32298eb-17b4-471e-8d9b-ba093c6afc7c")
    tester.setup_answer("state_gender", "Other")
    tester.setup_answer("state_surname", "test surname")
    tester.setup_answer("state_first_name", "test first name")
    tester.setup_answer("state_identification_type", "refugee")
    tester.setup_answer("state_identification_number", "6001010001081")
    tester.setup_answer("state_medical_aid", "state_medical_aid_search")
    tester.setup_answer("state_medical_aid_search", "discovery")
    tester.setup_answer(
        "state_medical_aid_list", "971672ba-bb31-4fca-945a-7c530b8b5558"
    )
    tester.setup_answer("state_medical_aid_number", "M1234567890")
    tester.setup_answer("state_vaccination_time", "weekday_morning")
    tester.setup_answer("state_email_address", "SKIP")
    await tester.user_input("1")
    tester.assert_message(
        "Something went wrong with your registration session. Your registration was "
        "not able to be processed. Please try again later",
        session=Message.SESSION_EVENT.CLOSE,
    )

    requests = evds_mock.app.requests
    assert len(requests) == 3
    assert requests[-1].json == {
        "gender": "Other",
        "surname": "test surname",
        "firstName": "test first name",
        "dateOfBirth": "1960-01-01",
        "mobileNumber": "27820001001",
        "preferredVaccineScheduleTimeOfDay": "morning",
        "preferredVaccineScheduleTimeOfWeek": "weekday",
        "preferredVaccineLocation": {
            "value": "d114778e-c590-4a08-894e-0ddaefc5759e",
            "text": "Diep River",
        },
        "termsAndConditionsAccepted": True,
        "refugeeNumber": "6001010001081",
        "medicalAidMember": True,
        "medicalAidScheme": {
            "text": "Discovery Health Medical Scheme",
            "value": "971672ba-bb31-4fca-945a-7c530b8b5558",
        },
        "medicalAidSchemeNumber": "M1234567890",
        "sourceId": "aeb8444d-cfa4-4c52-bfaf-eed1495124b7",
    }


@pytest.mark.asyncio
async def test_timeout(tester: AppTester):
    tester.setup_state("state_passport_country")
    await tester.user_input(session=Message.SESSION_EVENT.CLOSE)
    tester.assert_message(
        "\n".join(
            [
                "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                "",
                "We haven’t heard from you in a while!",
                "",
                "The registration session has timed out due to inactivity. You will "
                "need to start again. Just TYPE the word REGISTER.",
                "",
                "-----",
                "📌 Reply *0* to return to the main *MENU*",
            ]
        ),
        session=Message.SESSION_EVENT.CLOSE,
    )


@pytest.mark.asyncio
async def test_throttle(tester: AppTester):
    throttle = config.THROTTLE_PERCENTAGE
    config.THROTTLE_PERCENTAGE = 100.0

    await tester.user_input()
    tester.assert_message(
        "\n".join(
            [
                "*VACCINE REGISTRATION SECURE CHAT* 🔐",
                "",
                "⚠️ We are currently experiencing high volumes of registrations.",
                "",
                "Your registration is important! Please try again in 15 minutes.",
                "",
                "-----",
                "📌 Reply *0* to return to the main *MENU*",
            ]
        ),
        session=Message.SESSION_EVENT.CLOSE,
    )

    config.THROTTLE_PERCENTAGE = throttle


@pytest.mark.asyncio
async def test_exit_keywords(tester: AppTester):
    tester.setup_state("state_terms_and_conditions_summary")
    await tester.user_input("menu")
    tester.assert_message("", session=Message.SESSION_EVENT.CLOSE)
    assert tester.application.messages[0].helper_metadata["automation_handle"] is True
    tester.assert_state(None)
    assert tester.user.answers == {}


@pytest.mark.asyncio
async def test_uncaught_exception(tester: AppTester):
    tester.setup_state("state_vaccination_time")
    await tester.user_input("1")
    tester.assert_message(
        "Something went wrong. Please try again later.",
        session=Message.SESSION_EVENT.CLOSE,
    )
    assert tester.user.answers == {}
    tester.assert_state(None)
