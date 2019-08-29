FROM docker:latest

LABEL maintainer='ix.ai <docker@ix.ai>'

ARG SLEEP_TIME='5m'
ARG FILTER_SERVICES=''
ARG BLACKLIST_SERVICES=''

WORKDIR /app

COPY src/ /app

ENV SLEEP_TIME=${SLEEP_TIME}
ENV FILTER_SERVICES=${FILTER_SERVICES}
ENV BLACKLIST_SERVICES=${BLACKLIST_SERVICES}

RUN chmod 755 /app/*.sh &&\
    apk add --update --no-cache bash

ENTRYPOINT ["/app/cioban.sh"]
