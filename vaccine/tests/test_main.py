import pytest

from vaccine.main import app


def test_metrics():
    _, response = app.test_client.get(app.url_for("metrics"))
    assert response.status == 200
    assert "sanic_request_latency_sec" in response.text


def test_health():
    _, response = app.test_client.get(app.url_for("health"))
    assert response.status == 200
    assert isinstance(response.json["amqp"].pop("time_since_last_heartbeat"), float)
    assert response.json == {"status": "ok", "amqp": {"connection": True}}


@pytest.mark.asyncio
async def test_health_amqp_down():
    # Simulate connection being down
    app.worker.connection.connection = None
    _, response = await app.asgi_client.get(app.url_for("health"))
    assert response.status == 500
    assert response.json() == {"status": "down", "amqp": {"connection": False}}
