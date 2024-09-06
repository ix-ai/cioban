FROM alpine:latest@sha256:beefdbd8a1da6d2915566fde36db9db0b524eb737fc57cd1367effd16dc0d06d as builder

COPY cioban/requirements.txt /work/cioban/requirements.txt

ENV CRYPTOGRAPHY_DONT_BUILD_RUST="1"

RUN set -xeu; \
    mkdir -p /work/wheels; \
    apk add \
      py3-pip \
      python3-dev \
      openssl-dev \
      gcc \
      musl-dev \
      libffi-dev \
      make \
      openssl-dev \
      cargo \
    ; \
    pip3 install -U --break-system-packages \
      wheel \
      pip

RUN pip3 wheel --prefer-binary -r /work/cioban/requirements.txt -w /work/wheels

FROM alpine:latest@sha256:beefdbd8a1da6d2915566fde36db9db0b524eb737fc57cd1367effd16dc0d06d

LABEL maintainer="docker@ix.ai" \
      ai.ix.repository="ix.ai/cioban"

COPY --from=builder /work /

RUN set -xeu; \
    ls -lashi /wheels; \
    apk upgrade --no-cache; \
    apk add --no-cache py3-pip; \
    pip3 install --no-cache-dir --break-system-packages -U pip;\
    pip3 install \
      --no-index \
      --no-cache-dir \
      --find-links /wheels \
      --break-system-packages \
      --requirement /cioban/requirements.txt \
    ; \
    rm -rf /wheels

COPY cioban/ /cioban
COPY cioban.sh /usr/local/bin/cioban.sh

EXPOSE 9308

ENTRYPOINT ["/usr/local/bin/cioban.sh"]
