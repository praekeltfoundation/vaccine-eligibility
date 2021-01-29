# vaccine-eligibility
Demo application for what a vaccine eligibility flow could look like

## Development
This project uses [poetry](https://python-poetry.org/docs/) for packaging and dependancy
management. Once poetry is installed, install dependancies by running
```bash
poetry install
```

You will also need an AMQP broker like rabbitmq installed and running to run the local
server, or to run tests.

To run a development worker, run
```bash
poetry run python vaccine/worker.py
```

To run autoformatting and linting, run
```bash
poetry run black .
poetry run isort .
poetry run mypy .
poetry run flake8
```

To run the tests, run
```bash
poetry run pytest
```

## Configuration
Configuration is done through the following environment variables:

`AMQP_URL` - How to connect to the AMQP server. Defaults to
`amqp://guest:guest@127.0.0.1/`

`CONCURRENCY` - How many messages to process concurrently. Defaults to 20.

`TRANSPORT_NAME` - The name of the transport to consume messages from. Defaults to
`whatsapp`

`LOG_LEVEL` - The level of logs to output. Defaults to `INFO`

`REDIS_URL` - How to connect to the Redis server. Defaults to `redis://127.0.0.1:6379`

`TTL` - The number of time, in seconds, to keep user state data in redis. Defaults to
3600 or 1 hour
