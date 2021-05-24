import gzip
import json
import string
from datetime import date

from faker import Faker

from vaccine.utils import luhn_checksum

faker = Faker()

suburbs = []

with gzip.open("vaccine/data/suburbs.json.gz") as f:
    for province in json.load(f)["data"]["items"]:
        for municipality in province["children"]:
            for city in municipality["children"]:
                for suburb in city["children"]:
                    suburbs.append({"text": suburb["text"], "value": suburb["value"]})


def generate_id_number(dob, gender):
    dob = date.fromisoformat(dob).strftime("%y%m%d")
    if gender == "Male":
        gender = faker.random_int(5000, 9999)
    elif gender == "Female":
        gender = faker.random_int(0, 4999)
    else:
        gender = faker.random_int(0, 9999)
    idnumber = f"{dob}{gender:04d}08"
    checksum = 10 - luhn_checksum(f"{idnumber}0")
    return f"{idnumber}{checksum}"


def random_alphanumeric():
    return "".join(
        faker.random_sample(
            string.ascii_uppercase + string.digits, faker.randomize_nb_elements(20)
        )
    )


def generate_vaccine_registration():
    data = {}
    data["gender"] = faker.random_element(("Male", "Female", "Other"))
    if data["gender"] == "Male":
        data["firstName"] = faker.first_name_male()
        data["surname"] = faker.last_name_male()
    if data["gender"] == "Female":
        data["firstName"] = faker.first_name_female()
        data["surname"] = faker.last_name_female()
    if data["gender"] == "Other":
        data["firstName"] = faker.first_name_nonbinary()
        data["surname"] = faker.last_name_nonbinary()
    data["dateOfBirth"] = faker.date_between("-100y", "-60y").isoformat()
    data["mobileNumber"] = faker.numerify("2782#######")
    (
        data["preferredVaccineScheduleTimeOfWeek"],
        data["preferredVacchineScheduleTimeOfDay"],
    ) = faker.random_element(
        (("weekday", "morning"), ("weekday", "afternoon"), ("weekend", "morning"))
    )
    data["preferredVaccineLocation"] = faker.random_element(suburbs)
    data["termsAndConditionsAccepted"] = True
    data["sourceId"] = "008c0f09-db09-4d60-83c5-63505c7f05ba"
    data["medicalAidMember"] = faker.boolean()
    reg_type = faker.random_element(("said", "refugee", "passport"))
    if reg_type == "said":
        data["iDNumber"] = generate_id_number(data["dateOfBirth"], data["gender"])
    elif reg_type == "refugee":
        data["refugeeNumber"] = random_alphanumeric()
    elif reg_type == "passport":
        data["passportNumber"] = random_alphanumeric()
        data["passportCountry"] = faker.country_code()
    return data


if __name__ == "__main__":
    for _ in range(100):
        print(json.dumps(generate_vaccine_registration))
