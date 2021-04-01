from datetime import datetime, timezone
from uuid import uuid4


def random_id():
    return uuid4().hex


def current_timestamp():
    return datetime.now(timezone.utc)
