# vaccine-eligibility
Demo application for what a vaccine eligibility flow could look like

## Development
This project uses [poetry](https://python-poetry.org/docs/) for packaging and dependancy
management. Once poetry is installed, install dependancies by running
```bash
poetry install
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
