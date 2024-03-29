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

with gzip.open("vaccine/data/medscheme.json.gz") as f:
    medschemes = json.load(f)["data"]["items"]


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


for _ in range(100):
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
    data["sourceId"] = "aeb8444d-cfa4-4c52-bfaf-eed1495124b7"
    data["medicalAidMember"] = faker.boolean()
    reg_type = faker.random_element(("said", "refugee", "passport"))
    if reg_type == "said":
        data["iDNumber"] = generate_id_number(data["dateOfBirth"], data["gender"])
    elif reg_type == "refugee":
        data["refugeeNumber"] = random_alphanumeric()
    elif reg_type == "passport":
        data["passportNumber"] = random_alphanumeric()
        data["passportCountry"] = faker.country_code()
    if faker.boolean():
        data["emailAddress"] = faker.email()
    if data["medicalAidMember"]:
        data["medicalAidScheme"] = faker.random_element(medschemes)
        data["medicalAidSchemeNumber"] = random_alphanumeric()

    print(json.dumps(data))
