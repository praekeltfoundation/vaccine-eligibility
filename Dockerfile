FROM ghcr.io/praekeltfoundation/python-base-nw:3.9-bullseye as build

COPY . /app

RUN pip install -e .


FROM ghcr.io/praekeltfoundation/python-base-nw:3.9-bullseye

# Copy over translations
COPY locales locales
# Everything else is installed in the venv, so no reason to copy . anymore
COPY --from=build .venv .venv

CMD [".venv/bin/sanic", "--host", "0.0.0.0", "vaccine.main.app"]
