from os import environ

VACREG_EVENTSTORE_URL = environ.get("VACREG_EVENTSTORE_URL")
VACREG_EVENTSTORE_TOKEN = environ.get("VACREG_EVENTSTORE_TOKEN")
ELIGIBILITY_AGE_GATE_MIN = int(environ.get("ELIGIBILITY_AGE_GATE_MIN", "60"))
EVDS_URL = environ.get("EVDS_URL", "https://registration.mezzanineapps.com")
EVDS_USERNAME = environ.get("EVDS_USERNAME")
EVDS_PASSWORD = environ.get("EVDS_PASSWORD")
EVDS_DATASET = environ.get("EVDS_DATASET", "evds-sa")
EVDS_VERSION = environ.get("EVDS_VERSION", "8")
AMBIGUOUS_MAX_AGE = int(environ.get("AMBIGUOUS_MAX_AGE", "122"))
THROTTLE_PERCENTAGE = float(environ.get("THROTTLE_PERCENTAGE", "0.0"))
