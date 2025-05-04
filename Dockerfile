FROM python:3.12.4-slim

RUN apt-get update &&  \
    apt-get install -y \
    gcc \
    libpq-dev \
    pipx \
    curl \
    git \
    vim

RUN pipx install poetry==2.1.2
RUN pipx inject poetry poetry-plugin-bundle
RUN curl https://pyenv.run | bash

ENV HOME="/root"
ENV PYENV_ROOT="${HOME}/.pyenv"
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
#    POETRY_VIRTUALENVS_CREATE=false \
    PATH="/root/.local/bin:${PYENV_ROOT}/bin:${PATH}"

WORKDIR /app
COPY poetry.lock pyproject.toml ./

#CMD ["sleep", "9000"]

RUN poetry install --no-interaction --no-root

COPY . .

#EXPOSE 8000

#CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
#CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
#CMD [poetry run uvicorn "main:app" --host "0.0.0.0" --port 8000]
#ls -al .venv/lib/python3.12/site-packages

ENTRYPOINT ["poetry", "run", "main"]
