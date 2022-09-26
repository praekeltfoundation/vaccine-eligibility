FROM ghcr.io/praekeltfoundation/python-base-nw:3.9-bullseye as build

# Requirements to build wheels where there are no python 3.9 wheels
RUN apt-get-install.sh gcc libc-dev make
RUN pip install "poetry==1.2.0"
RUN poetry config virtualenvs.in-project true

# Install just the deps so we use cached layers if they haven't changed
COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-root --no-interaction --no-ansi

COPY . ./
RUN poetry install --only main --no-interaction --no-ansi


FROM ghcr.io/praekeltfoundation/python-base-nw:3.9-bullseye

COPY --from=build .venv .venv
COPY . ./

CMD [".venv/bin/sanic", "--host", "0.0.0.0", "vaccine.main.app"]
