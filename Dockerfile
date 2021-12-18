FROM python:3.9.9

COPY pyproject.toml .
COPY poetry.lock .

RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install -v --no-interaction --no-ansi

COPY src .
EXPOSE 8000

ENTRYPOINT ["poetry", "run", "api"]