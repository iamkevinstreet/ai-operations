########################################################################
#                                                                      #
#                              Dockerfile                              #
#                                                                      #
########################################################################
# Author:            Kevin Street
# Created on:        2026-11-08
# Last modified on:  2026-11-08
#
# Airflow 3 with uv and the project's locked environment, for local
# runs through compose.yaml. The repository is mounted at
# /opt/data-platform, so the DAGs and models are the working copy's;
# the packages are the lockfile's, installed once at build.

FROM apache/airflow:3.4.0-python3.12

COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /usr/local/bin/uv

# uv fetches the workbench packages from their git commit, so git is needed.
USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*
USER airflow

# Airflow runs from the project's own environment, with the airflow group, so
# the DAGs and the tasks see the same locked packages the tests ran with.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PATH=/opt/venv/bin:$PATH

WORKDIR /opt/data-platform
COPY --chown=airflow:root pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project --no-dev --group airflow
