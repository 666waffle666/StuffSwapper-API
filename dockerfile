FROM python:3.13-slim

WORKDIR /api

COPY pyproject.toml poetry.lock ./

RUN pip install poetry
RUN poetry install --no-root

COPY . .

CMD ["uvicorn", "api:api", "--host", "0.0.0.0", "--port", "8000"]
