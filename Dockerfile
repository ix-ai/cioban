FROM alpine:latest@sha256:21dc6063fd678b478f57c0e13f47560d0ea4eeba26dfc947b2a4f81f686b9f45 as builder

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

FROM alpine:latest@sha256:21dc6063fd678b478f57c0e13f47560d0ea4eeba26dfc947b2a4f81f686b9f45

LABEL maintainer="docker@ix.ai" \
      ai.ix.repository="ix.ai/cioban" \
      org.opencontainers.image.source="https://gitlab.com/ix.ai/cioban"

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
