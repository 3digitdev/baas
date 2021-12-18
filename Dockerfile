FROM python:3.9.9

COPY pyproject.toml .

RUN apt-get update && \
    python3 -m pip install poetry
RUN poetry config virtualenvs.path "/home/.cache/pypoetry/virtualenvs"
RUN poetry install --no-dev

COPY src .
EXPOSE 8000

ENTRYPOINT ["poetry", "run", "api"]