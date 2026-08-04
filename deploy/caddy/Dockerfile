FROM node:24.14.0-bookworm-slim AS frontend-builder

ENV PNPM_HOME=/pnpm
ENV PATH=$PNPM_HOME:$PATH

RUN npm install --global pnpm@11.9.0
WORKDIR /build/frontend
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY frontend/ ./
RUN pnpm build

FROM python:3.12.13-slim-bookworm AS django-static-builder

ARG PIP_INDEX_URL=https://pypi.org/simple
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build/backend
COPY backend/requirements/base.txt /tmp/requirements/base.txt
RUN python -m pip install --index-url "$PIP_INDEX_URL" --requirement /tmp/requirements/base.txt
COPY backend/ ./
RUN DJANGO_SETTINGS_MODULE=config.settings.build python manage.py collectstatic --noinput

FROM caddy:2.10.2-alpine

COPY deploy/Caddyfile /etc/caddy/Caddyfile
COPY --from=frontend-builder /build/frontend/dist /srv/app
COPY --from=django-static-builder /build/backend/staticfiles /srv/django-static
