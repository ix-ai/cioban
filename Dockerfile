FROM docker:latest
LABEL maintainer="docker@ix.ai" \
      ai.ix.repository="ix.ai/cioban"

COPY cioban/requirements.txt /cioban/requirements.txt

RUN apk add --no-cache python3 && \
    pip3 install --no-cache-dir -r /cioban/requirements.txt

COPY cioban/ /cioban

EXPOSE 9308

ENTRYPOINT ["python3", "-m", "cioban"]
