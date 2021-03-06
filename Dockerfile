FROM praekeltfoundation/python-base:3.9-buster as build

# Requirements to build wheels where there are no python 3.9 wheels
RUN apt-get-install.sh gcc libc-dev
RUN pip install "poetry==1.1.4"
COPY . ./
RUN poetry config virtualenvs.in-project true \
    && poetry install --no-dev --no-interaction --no-ansi

CMD ["./.venv/bin/python", "vaccine/worker.py"]
