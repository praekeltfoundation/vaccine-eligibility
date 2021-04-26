import gzip
import json
import os
from datetime import date

from locust import HttpUser, between, task

from vaccine.tests.generate_test_ussd_data import generate_vaccine_registration

PATH = os.environ["HTTP_PATH"]
ADDRESS = os.environ["ADDRESS"]
PROVIDER = os.environ["PROVIDER"]

suburbs = {}
with gzip.open("vaccine/data/suburbs.json.gz") as f:
    for province in json.load(f)["data"]["items"]:
        for municipality in province["children"]:
            for city in municipality["children"]:
                for suburb in city["children"]:
                    {"text": suburb["text"], "value": suburb["value"]}
                    suburbs[suburb["value"]] = (
                        province["text"],
                        municipality["text"],
                        suburb["text"],
                    )


class VaccineRegUser(HttpUser):
    wait_time = between(1.0, 5.0)

    def start_session(self, msisdn):
        return self.client.get(
            PATH, params={"msisdn": msisdn, "request": ADDRESS, "provider": PROVIDER}
        )

    def send_message(self, msisdn, message, catch_response=False):
        return self.client.get(
            PATH,
            params={
                "msisdn": msisdn,
                "request": message,
                "provider": PROVIDER,
                "to_addr": ADDRESS,
            },
            catch_response=catch_response,
        )

    @task
    def vaccine_registration(self):
        registration = generate_vaccine_registration()
        msisdn = registration["mobileNumber"]
        dob = date.fromisoformat(registration["dateOfBirth"])

        self.start_session(msisdn)
        # menu
        self.send_message(msisdn, "1")
        # age gate
        self.send_message(msisdn, "1")
        # terms
        self.send_message(msisdn, "1")
        self.send_message(msisdn, "1")
        self.send_message(msisdn, "1")
        # ID
        if "iDNumber" in registration:
            self.send_message(msisdn, "1")
            response = self.send_message(msisdn, registration["iDNumber"])
            # date of birth
            if "YEAR" in response.text:
                self.send_message(msisdn, str(dob.year))
        elif "refugeeNumber" in registration:
            self.send_message(msisdn, "4")
            self.send_message(msisdn, registration["refugeeNumber"])
            self.send_message(msisdn, registration["gender"])
            # date of birth
            self.send_message(msisdn, str(dob.year))
            self.send_message(msisdn, str(dob.month))
            self.send_message(msisdn, str(dob.day))
        elif "passportNumber" in registration:
            self.send_message(msisdn, "2")
            self.send_message(msisdn, registration["passportNumber"])
            self.send_message(msisdn, "8")  # other
            self.send_message(msisdn, registration["passportCountry"])
            self.send_message(msisdn, "1")
            self.send_message(msisdn, registration["gender"])
            # date of birth
            self.send_message(msisdn, str(dob.year))
            self.send_message(msisdn, str(dob.month))
            self.send_message(msisdn, str(dob.day))
        # name
        self.send_message(msisdn, registration["firstName"])
        self.send_message(msisdn, registration["surname"])
        # confirmation
        self.send_message(msisdn, "1")
        # suburb
        prv, mun, sub = suburbs[registration["preferredVaccineLocation"]["value"]]
        self.send_message(msisdn, prv)
        response = self.send_message(msisdn, sub)
        if "municipality" in response.text:
            self.send_message(msisdn, mun)
        self.send_message(msisdn, "1")
        # self registration
        self.send_message(msisdn, "1")
        # vaccination time
        self.send_message(msisdn, "1")
        # medical aid
        if registration["medicalAidMember"]:
            medaid = "1"
        else:
            medaid = "2"
        with self.send_message(msisdn, medaid, catch_response=True) as response:
            if "SUCCESSFULLY" not in response.text:
                response.failure("Did not get registration success message")
