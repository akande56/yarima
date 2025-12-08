# compose/production/django/Dockerfile

FROM docker.io/python:3.12.11-slim-bookworm AS python

# Python build stage
FROM python AS python-build-stage

ARG BUILD_ENVIRONMENT=production

# Install apt packages
RUN apt-get update && apt-get install --no-install-recommends -y \
  build-essential \
  libpq-dev

# Copy requirements
COPY ./requirements .

# Build wheels
RUN pip wheel --wheel-dir /usr/src/app/wheels -r ${BUILD_ENVIRONMENT}.txt

# Python 'run' stage
FROM python AS python-run-stage

ARG BUILD_ENVIRONMENT=production
ARG APP_HOME=/app

# Dummy DATABASE_URL to satisfy env.db() during build
ARG BUILD_DATABASE_URL=sqlite:///dummy.db
ENV DATABASE_URL=${BUILD_DATABASE_URL}

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV BUILD_ENV=${BUILD_ENVIRONMENT}

WORKDIR ${APP_HOME}

RUN addgroup --system django \
  && adduser --system --ingroup django django

# Create static dir
RUN mkdir -p /var/www/static \
  && chown -R django:django /var/www/static

# Install system dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
  libpq-dev \
  gettext \
  wait-for-it \
  build-essential \
  libffi-dev \
  libcairo2 \
  libpango-1.0-0 \
  libpangocairo-1.0-0 \
  libgdk-pixbuf2.0-0 \
  libglib2.0-0 \
  libxml2 \
  libxslt1.1 \
  shared-mime-info \
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

# Install Python wheels
COPY --from=python-build-stage /usr/src/app/wheels /wheels/
RUN pip install --no-cache-dir --no-index --find-links=/wheels/ /wheels/* \
  && rm -rf /wheels/

# Copy entrypoint and start scripts
COPY --chown=django:django ./compose/production/django/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint && chmod +x /entrypoint

COPY --chown=django:django ./compose/production/django/start /start
RUN sed -i 's/\r$//g' /start && chmod +x /start

# Copy app code
COPY --chown=django:django . ${APP_HOME}

# Create media dir
RUN mkdir -p ${APP_HOME}/yarima_mining/media
RUN chown -R django:django ${APP_HOME}

USER django

# Compile translations
RUN DATABASE_URL="" \
  DJANGO_SETTINGS_MODULE="config.settings.test" \
  python manage.py compilemessages

ENTRYPOINT ["/entrypoint"]  