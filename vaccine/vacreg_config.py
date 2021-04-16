from os import environ

ELIGIBILITY_AGE_GATE_MIN = int(environ.get("ELIGIBILITY_AGE_GATE_MIN", "60"))
EVDS_URL = environ.get("EVDS_URL", "https://registration.mezzanineapps.com")
EVDS_USERNAME = environ.get("EVDS_USERNAME")
EVDS_PASSWORD = environ.get("EVDS_PASSWORD")
EVDS_DATASET = environ.get("EVDS_DATASET", "evds-sa")
EVDS_VERSION = environ.get("EVDS_VERSION", "1")
