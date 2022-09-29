from sanic import Sanic
from sanic_testing import TestManager
from sentry_sdk.integrations import sanic as si_sanic

from vaccine.main import app

# Fix multiple additions of sentry signal handlers.
if hasattr(si_sanic, "old_startup"):

    async def conditional_sentry_startup(self):
        if getattr(self.ctx, "sentry_startup_has_run", False):
            await si_sanic._startup(self)
            self.ctx.sentry_startup_has_run = True
        else:
            await si_sanic.old_startup(self)

    Sanic._startup = conditional_sentry_startup


TestManager(app)


def test_metrics():
    _, response = app.test_client.get(app.url_for("metrics"))
    assert response.status == 200
    assert "sanic_request_latency_sec" in response.text


def test_health():
    _, response = app.test_client.get(app.url_for("health"))
    assert response.status == 200
    assert isinstance(response.json["amqp"].pop("time_since_last_heartbeat"), float)
    assert isinstance(response.json["redis"].pop("response_time"), float)
    assert response.json == {
        "status": "ok",
        "amqp": {"connection": True},
        "redis": {"connection": True},
    }


# TODO: Tests for when services are down. These tests are currently done manually
