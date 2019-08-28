FROM docker:latest

LABEL maintainer='ix.ai <docker@ix.ai>'

ARG SLEEP_TIME='5m'
ARG FILTER_SERVICES=''
ARG BLACKLIST_SERVICES=''

ENV SLEEP_TIME=${SLEEP_TIME}
ENV FILTER_SERVICES=${FILTER_SERVICES}
ENV BLACKLIST_SERVICES=${BLACKLIST_SERVICES}

COPY src/cioban.sh /usr/local/bin/cioban

RUN chmod 755 /usr/local/bin/cioban &&\
    apk add --update --no-cache bash

ENTRYPOINT ["/usr/local/bin/cioban"]
