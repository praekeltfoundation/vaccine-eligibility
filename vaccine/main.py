from prometheus_client import CONTENT_TYPE_LATEST
from prometheus_client.exposition import generate_latest
from sanic import Sanic
from sanic.request import Request
from sanic.response import HTTPResponse, json, raw

from vaccine import config
from vaccine.metrics import setup_metrics_middleware
from vaccine.worker import Worker

app = Sanic("vaccine")
app.update_config(config)
setup_metrics_middleware(app)


@app.listener("before_server_start")
async def setup_worker(app, loop):
    app.worker = Worker()
    await app.worker.setup()


@app.listener("after_server_stop")
async def shutdown_worker(app, loop):
    await app.worker.teardown()


@app.route("/")
async def health(request: Request) -> HTTPResponse:
    return json({"status": "ok"})


@app.route("/metrics")
async def metrics(request: Request) -> HTTPResponse:
    return raw(generate_latest(), content_type=CONTENT_TYPE_LATEST)
