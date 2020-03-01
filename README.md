# cioban

[![Pipeline Status](https://gitlab.com/ix.ai/cioban/badges/master/pipeline.svg)](https://gitlab.com/ix.ai/cioban/)
[![Docker Stars](https://img.shields.io/docker/stars/ixdotai/cioban.svg)](https://hub.docker.com/r/ixdotai/cioban/)
[![Docker Pulls](https://img.shields.io/docker/pulls/ixdotai/cioban.svg)](https://hub.docker.com/r/ixdotai/cioban/)
[![Image Layers](https://images.microbadger.com/badges/image/ixdotai/cioban.svg)](https://hub.docker.com/r/ixdotai/cioban/)
[![Latest Version](https://images.microbadger.com/badges/version/ixdotai/cioban.svg)](https://hub.docker.com/r/ixdotai/cioban/)
[![Gitlab Project](https://img.shields.io/badge/GitLab-Project-554488.svg)](https://gitlab.com/ix.ai/cioban/)


A docker swarm service for automatically updating your services to the latest image tag push. You can enable telegram or gotify notifications, so you get a message after every successful update.

## Contributing

Please read [how to contribute](CONTRIBUTING.md) and the [code of conduct](CODE_OF_CONDUCT.md).

## Configuration

You can enable private registry authentication by mounting your credentials file to `/root/.docker/config.json`.

Cioban will try to update your services every 5 minutes by default. The following environment settings are recognised:

### Environment

| **Variable**                | **Default** | **Description**                                                                                         |
|:----------------------------|:-----------:|:--------------------------------------------------------------------------------------------------------|
| `SLEEP_TIME`                | `5m`        | Adjust the sleeping time. Accepted are numbers ending in one of `s`, `m`, `h`, `d`, `w`|
| `BLACKLIST_SERVICES`        | -           | Space-separated list of service names to exclude from updates |
| `FILTER_SERVICES`           | -           | Anything accepted by the filtering flag in `docker service ls`. Example: `label=ai.ix.auto-update=true` |
| `TELEGRAM_TOKEN`            | -           | See the [Telegram documentation](https://core.telegram.org/bots#creating-a-new-bot) how to get a new token |
| `TELEGRAM_CHAT_ID`          | -           | See this question on [stackoverflow](https://stackoverflow.com/questions/32423837/telegram-bot-how-to-get-a-group-chat-id) |
| `GOTIFY_URL`                | -           | The URL of the [Gotify](https://gotify.net/) server |
| `GOTIFY_TOKEN`              | -           | The APP token for Gotify |
| `NOTIFY_INCLUDE_IMAGE`      | -           | Set this variable to `yes` to include the image name (without digest) in the update notification |
| `NOTIFY_INCLUDE_NEW_IMAGE`  | -           | Set this variable to `yes` to include the new image (**including** digest) in the update notification |
| `NOTIFY_INCLUDE_OLD_IMAGE`  | -           | Set this variable to `yes` to include the old image (**including** digest) in the update notification |
| `LOGLEVEL`                  | `INFO`      | [Logging Level](https://docs.python.org/3/library/logging.html#levels) |
| `GELF_HOST`                 | -           | If set, GELF UDP logging to this host will be enabled |
| `GELF_PORT`                 | `12201`     | Ignored, if `GELF_HOST` is unset. The UDP port for GELF logging |
| `PORT`                      | `9308`      | The port for prometheus metrics |

Additionally, these environment variables are [supported](https://docker-py.readthedocs.io/en/stable/client.html#docker.client.from_env) by the [Python library for the Docker Engine API](https://github.com/docker/docker-py):

| **Variable**         | **Description**                                                                                         |
|:--------------------:|:--------------------------------------------------------------------------------------------------------|
| `DOCKER_HOST`        | The URL to the Docker host. |
| `BLACKLIST_SERVICES` | Verify the host against a CA certificate. |
| `FILTER_SERVICES`    | A path to a directory containing TLS certificates to use when connecting to the Docker host. (**Note**: this path needs to be present inside the `ixdotai/cioban` image) |


## Webhooks

Starting with version `0.12.0`, `ixdotai/cioban` supports simple webhooks for each service, that are configured in the service labels.

The following labels are supported:

| **Label**                            | **Default**     | **Description** |
|:-------------------------------------|:---------------:|:----------------|
| `cioban.webhook.http.url`            | -               | The full URL of the webhook |
| `cioban.webhook.http.method`         | `post`          | The HTTP method to use (one of `get`, `post`) |
| `cioban.webhook.auth.basic.username` | -               | The username, if using basic authentication |
| `cioban.webhook.auth.basic.password` | -               | The password, if using basic authentication |
| `cioban.webhook.auth.token.header`   | `Authorization` | The name of the header that will be used for the token |
| `cioban.webhook.auth.token.type`     | `token`         | The type of authorisation token (usually `token` or `access_token`) |
| `cioban.webhook.auth.token.token`    | -               | The actual token |

**Note**: `cioban.webhook.auth.basic` uses the header `Authorization` and it's incompatible with the default `cioban.webhook.auth.token.header`.

## Examples

### Start `ixdotai/cioban`as a Docker Swarm service
```sh
docker service create \
    --name cioban \
    --publish 9308:9308 \
    --constraint "node.role==manager" \
    --env SLEEP_TIME="3m" \
    --env BLACKLIST_SERVICES="cioban karma_karma karma_oauth" \
    --env FILTER_SERVICES="label=ai.ix.auto-update=true" \
    --env LOGLEVEL="WARNING" \
    --env TELEGRAM_TOKEN="000000000:zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz" \
    --env TELEGRAM_CHAT_ID="-0000000000000" \
    --env NOTIFY_INCLUDE_NEW_IMAGE="yes" \
    --env NOTIFY_INCLUDE_OLD_IMAGE="y" \
    --mount type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock \
    --mount type=bind,source=/root/.docker/config.json,target=/root/.docker/config.json,ro \
    ixdotai/cioban
```

### Add a webhook for a service

```yml
version: "3.7"

services:
  spielwiese:
    image: ixdotai/spielwiese
    networks:
      - websites
    deploy:
      labels:
        - "ai.ix.auto-update"
        - "cioban.webhook.http.url=http://spielwiese:8080/json"
        - "cioban.webhook.http.timeout=5"
        - "cioban.webhook.auth.basic.username=foo"
        - "cioban.webhook.auth.basic.password=${WEBHOOK_BASIC_PASS}"
        - "cioban.webhook.auth.token.token=${WEBHOOK_TOKEN}"
        - "cioban.webhook.auth.token.header=SECRET-TOKEN"
  cioban:
    image: ixdotai/cioban:latest
    deploy:
      placement:
        constraints:
          - node.role == manager
      labels:
        ai.ix.auto-update: 'true' # cioban updates cioban
        cioban.webhook.http.url: http://spielwiese:8080/json
        cioban.webhook.auth.basic.username: foo
        cioban.webhook.auth.basic.password: ${WEBHOOK_BASIC_PASS}
        cioban.webhook.auth.token.token: ${WEBHOOK_TOKEN}
        cioban.webhook.auth.token.header: SECRET-TOKEN
    volumes:
      - '/var/run/docker.sock:/var/run/docker.sock:rw'
      - '/root/.docker/config.json:/root/.docker/config.json:ro'
    environment:
      GELF_HOST: graylog
      SLEEP_TIME: '5m'
      BLACKLIST_SERVICES: 'gitlab_register-git-ix-ai-runner gitlab_register-gitlab-com-ix-ai-runner'
      FILTER_SERVICES: 'label=ai.ix.auto-update'
      NOTIFY_INCLUDE_IMAGE: 'yes'
      GOTIFY_URL: "${GOTIFY_URL?err}"
      GOTIFY_TOKEN: "${GOTIFY_TOKEN?err}"
      TELEGRAM_TOKEN: "${TELEGRAM_TOKEN?err}"
      TELEGRAM_CHAT_ID: "${TELEGRAM_CHAT_ID?err}"
      LOGLEVEL: INFO
networks:
  websites: {}
```

### Prometheus metrics

In addition to the metrics exporter by [prometheus/client_python/](https://github.com/prometheus/client_python/), the following metrics are exposed by cioban:
```
# HELP update_run_seconds Time spent processing updates
# TYPE update_run_seconds summary
update_run_seconds_count 1.0
update_run_seconds_sum 43.92592599400086
# TYPE update_run_seconds_created gauge
update_run_seconds_created 1.5672812321329722e+09
# HELP service_updated_total Shows if a service has been updated
# TYPE service_updated_total counter
service_updated_total{id="pqs6wtscm1tq6yiqrmu4wv0of",name="smtp_smtp",short_id="pqs6wtscm1"} 1.0
# TYPE service_updated_created gauge
service_updated_created{id="pqs6wtscm1tq6yiqrmu4wv0of",name="smtp_smtp",short_id="pqs6wtscm1"} 1.567281276077023e+09
# HELP cioban_info Information about cioban
# TYPE cioban_info gauge
cioban_info{version="0.7.0"} 1.0
# HELP cioban_state The current state of cioban
# TYPE cioban_state gauge
cioban_state{cioban_state="running"} 0.0
cioban_state{cioban_state="sleeping"} 1.0
```

## How does it work?
Cioban just triggers updates by checking the registry for a different digest than the current running image. If the current image does not have a digest, the service gets restarted with a digest.

Cioban is handling connecting to the registry, getting the information about the image, comparing it with the running version. The update is done by docker and cioban moves forward once the service is not in status `updating` anymore.

Docker handles all the work of [applying rolling updates](https://docs.docker.com/engine/swarm/swarm-tutorial/rolling-update/). So at least with replicated services, there should be no noticeable downtime.

## Tags and Arch

Starting with version 0.8.1, the images are multi-arch, with builds for amd64, arm64, armv7 and armv6.
* `vN.N.N` - for example 0.8.0
* `latest` - always pointing to the latest version
* `dev-master` - the last build on the master branch

## Resources
* GitLab: https://gitlab.com/ix.ai/cioban
* GitHub: https://github.com/ix-ai/cioban
* Docker Hub: https://hub.docker.com/r/ixdotai/cioban

## Credits
Cioban is a fork of [shepherd](https://github.com/djmaze/shepherd). It has been completely rewritten in python.

### What is `cioban`?
Cioban is the Romanian translation of the word `shepherd`.
