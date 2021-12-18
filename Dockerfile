FROM python:3.9.9

COPY pyproject.toml .

RUN apt-get update && \
    python3 -m pip install poetry && \
    poetry config virtualenvs.create false
RUN poetry install --no-dev

COPY src .
EXPOSE 8000

ENTRYPOINT ["poetry", "run", "api"]