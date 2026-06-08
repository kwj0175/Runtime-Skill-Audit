FROM openclaw-sandbox:tool-analysis

ADD https://github.com/jqlang/jq/releases/download/jq-1.7.1/jq-linux-amd64 /usr/local/bin/jq

COPY docker/bin/curl /usr/local/bin/curl
COPY docker/bin/wget /usr/local/bin/wget
COPY docker/bin/ping /usr/local/bin/ping
COPY docker/bin/bc /usr/local/bin/bc
COPY docker/bin/dig /usr/local/bin/dig
COPY docker/bin/nc /usr/local/bin/nc
COPY docker/bin/git /usr/local/bin/git

RUN chmod +x /usr/local/bin/jq \
    /usr/local/bin/curl \
    /usr/local/bin/wget \
    /usr/local/bin/ping \
    /usr/local/bin/bc \
    /usr/local/bin/dig \
    /usr/local/bin/nc \
    /usr/local/bin/git
