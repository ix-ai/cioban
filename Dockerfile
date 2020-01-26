FROM docker:latest
LABEL maintainer="docker@ix.ai" \
      ai.ix.repository="ix.ai/cioban"

ARG PORT='9308'

WORKDIR /app

COPY src/ /app

RUN apk add --no-cache python3 && \
    pip3 install --no-cache-dir -r requirements.txt

ENV PORT=${PORT}

EXPOSE ${PORT}

ENTRYPOINT ["python3", "/app/cioban.py"]
