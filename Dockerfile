FROM alpine:latest
LABEL maintainer="docker@ix.ai" \
      ai.ix.repository="ix.ai/cioban"

COPY cioban/requirements.txt /cioban/requirements.txt

RUN apk add --no-cache python3 py3-cryptography py3-pip && \
    pip3 install --no-cache-dir -r /cioban/requirements.txt

COPY cioban/ /cioban
COPY cioban.sh /usr/local/bin/cioban.sh

EXPOSE 9308

ENTRYPOINT ["/usr/local/bin/cioban.sh"]
