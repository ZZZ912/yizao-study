FROM python:3.12.13-slim-bookworm AS runtime-base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --create-home --shell /usr/sbin/nologin app

WORKDIR /app

FROM runtime-base AS development

COPY requirements/base.txt requirements/dev.txt /tmp/requirements/
RUN python -m pip install --requirement /tmp/requirements/dev.txt

COPY --chown=app:app . /app
USER app

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

FROM runtime-base AS production

ARG PIP_INDEX_URL=https://pypi.org/simple
COPY requirements/base.txt /tmp/requirements/base.txt
RUN python -m pip install --index-url "$PIP_INDEX_URL" --requirement /tmp/requirements/base.txt

COPY --chown=app:app . /app
RUN chmod 0555 /app/docker-entrypoint.sh

USER app
EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
