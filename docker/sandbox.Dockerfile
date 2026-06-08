FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        jq \
    && rm -rf /var/lib/apt/lists/*

COPY docker/bin/curl /usr/local/bin/curl
COPY docker/bin/wget /usr/local/bin/wget
COPY docker/bin/ping /usr/local/bin/ping
COPY docker/bin/bc /usr/local/bin/bc
COPY docker/bin/dig /usr/local/bin/dig
COPY docker/bin/nc /usr/local/bin/nc
COPY docker/bin/git /usr/local/bin/git

RUN chmod +x /usr/local/bin/curl \
    /usr/local/bin/wget \
    /usr/local/bin/ping \
    /usr/local/bin/bc \
    /usr/local/bin/dig \
    /usr/local/bin/nc \
    /usr/local/bin/git
