from os import environ

AMQP_URL = environ.get("AMQP_URL", "amqp://guest:guest@127.0.0.1/")
CONCURRENCY = int(environ.get("CONCURRENCY", "20"))
TRANSPORT_NAME = environ.get("TRANSPORT_NAME", "whatsapp")
LOG_LEVEL = environ.get("LOG_LEVEL", "INFO")
