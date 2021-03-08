from vaccine.main import app


def test_metrics():
    _, response = app.test_client.get(app.url_for("metrics"))
    assert response.status == 200
    assert "sanic_request_latency_sec" in response.text
