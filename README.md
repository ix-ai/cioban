# cioban

[![Pipeline Status](https://gitlab.com/ix.ai/cioban/badges/master/pipeline.svg)](https://gitlab.com/ix.ai/cioban/)
[![Docker Stars](https://img.shields.io/docker/stars/ixdotai/cioban.svg)](https://hub.docker.com/r/ixdotai/cioban/)
[![Docker Pulls](https://img.shields.io/docker/pulls/ixdotai/cioban.svg)](https://hub.docker.com/r/ixdotai/cioban/)
[![Gitlab Project](https://img.shields.io/badge/GitLab-Project-554488.svg)](https://gitlab.com/ix.ai/cioban/)


A docker swarm service for automatically updating your services to the latest image tag push. You can enable telegram or gotify notifications, so you get a message after every successful update.

## Usage Examples

### CLI
```sh
docker service create \
    --name cioban \
    --constraint "node.role==manager" \
    --mount type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock \
    ixdotai/cioban
```

### docker-compose
```yml
version: "3.7"

services:
  cioban:
    image: ixdotai/cioban
    volumes:
      - '/var/run/docker.sock:/var/run/docker.sock:rw'
      - '/root/.docker/config.json:/root/.docker/config.json:ro'
    environment:
      SLEEP_TIME: 30s
    deploy:
      placement:
        constraints:
        - node.role == manager
```

## Configuration

You can enable private registry authentication by mounting your credentials file to `/root/.docker/config.json`.

Cioban will try to update your services every 5 minutes by default. The following environment settings are recognized:

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
| `NOTIFY_INCLUDE_IMAGE`      | -           | Set this variable to anything to include the image name (without digest) in the update notification |
| `NOTIFY_INCLUDE_NEW_IMAGE`  | -           | Set this variable to anything to include the new image (**including** digest) in the update notification |
| `NOTIFY_INCLUDE_OLD_IMAGE`  | -           | Set this variable to anything to include the old image (**including** digest) in the update notification |
| `LOGLEVEL`                  | `INFO`      | [Logging Level](https://docs.python.org/3/library/logging.html#levels) |
| `GELF_HOST`                 | -           | If set, GELF UDP logging to this host will be enabled |
| `GELF_PORT`                 | `12201`     | Ignored, if `GELF_HOST` is unset. The UDP port for GELF logging |
| `PORT`                      | `9308`      | The port for prometheus metrics |


## Deprecated

The following environment variables are deprecated and have been removed:

| **Variable**        | **Description**                                                                                |
|:--------------------|:-----------------------------------------------------------------------------------------------|
| `TIMEOUT`           | Timeout in seconds for the update command                                                      |
| `VERBOSE`           | Displayed the log messages about the update tries                                              |
| `DISABLE_HEARTBEAT` | Disabled the `HEARTBEAT: Sleeping ${SLEEP_TIME}` and `HEARTBEAT: Starting update run` messages |

### Example:
```sh
docker service create \
    --name cioban \
    --publish 9308:9308 \
    --constraint "node.role==manager" \
    --env SLEEP_TIME="3m" \
    --env BLACKLIST_SERVICES="cioban karma_karma karma_oauth" \
    --env FILTER_SERVICES="label=com.mydomain.autodeploy=true" \
    --env LOGLEVEL="WARNING" \
    --env TIMEOUT="30" \
    --env TELEGRAM_TOKEN="000000000:zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz" \
    --env TELEGRAM_CHAT_ID="-0000000000000" \
    --env NOTIFY_INCLUDE_NEW_IMAGE="yes please" \
    --env NOTIFY_INCLUDE_OLD_IMAGE="aha" \
    --mount type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock \
    --mount type=bind,source=/root/.docker/config.json,target=/root/.docker/config.json,ro \
    ixdotai/cioban
```

#### Logs:
With `LOGLEVEL=DEBUG`
```
2020-02-04 07:17:01.446 INFO [__main__.<module>] FILTER_SERVICES: "{'label': 'ai.ix.auto-update=true'}"
2020-02-04 07:17:01.446 INFO [__main__.<module>] BLACKLIST_SERVICES: "['websites_tool-ix-ai']"
2020-02-04 07:17:01.446 INFO [__main__.<module>] TELEGRAM_TOKEN is set
2020-02-04 07:17:01.446 INFO [__main__.<module>] TELEGRAM_CHAT_ID is set
2020-02-04 07:17:01.446 INFO [__main__.<module>] NOTIFY_INCLUDE_NEW_IMAGE is set
2020-02-04 07:17:01.446 INFO [__main__.<module>] NOTIFY_INCLUDE_OLD_IMAGE is set
2020-02-04 07:17:01.446 INFO [__main__.<module>] SLEEP_TIME: 10s
2020-02-04 07:17:01.446 INFO [__main__.<module>] PORT: 9308
2020-02-04 07:17:01.447 WARNING [__main__.<module>] Starting cioban None-None with prometheus metrics on port 9308
2020-02-04 07:17:01.447 DEBUG [core.register] Registering telegram
2020-02-04 07:17:01.634 DEBUG [telegram_notifier.__init__] Initialized
2020-02-04 07:17:01.634 DEBUG [core.register] Registered telegram
2020-02-04 07:17:01.634 DEBUG [cioban.__init__] Registered telegram
2020-02-04 07:17:01.634 DEBUG [cioban.__init__] Cioban initialized
2020-02-04 07:17:01.646 INFO [cioban.run] Starting update run
2020-02-04 07:17:01.669 DEBUG [cioban.get_services] Blacklisted websites_tool-ix-ai
2020-02-04 07:17:03.996 DEBUG [cioban.__get_updated_image] containous/whoami:latest@sha256:c0d68a0f9acde95c5214bd057fd3ff1c871b2ef12dae2a9e2d2a3240fdd9214b: No update available
2020-02-04 07:17:03.997 INFO [cioban.run] Sleeping for 10 seconds
2020-02-04 07:17:13.997 INFO [cioban.run] Starting update run
2020-02-04 07:17:14.014 DEBUG [cioban.get_services] Blacklisted websites_tool-ix-ai
2020-02-04 07:17:16.427 INFO [cioban.__update_image] Updating service websites_whoami with image containous/whoami:latest@sha256:c0d68a0f9acde95c5214bd057fd3ff1c871b2ef12dae2a9e2d2a3240fdd9214b
2020-02-04 07:17:16.532 WARNING [cioban.__update_image] Service websites_whoami has been updated
2020-02-04 07:17:16.543 DEBUG [cioban._run] Service websites_whoami is in status `updating`. Waiting 1s...
2020-02-04 07:17:17.558 DEBUG [cioban._run] Service websites_whoami is in status `updating`. Waiting 1s...
2020-02-04 07:17:18.568 DEBUG [cioban._run] Service websites_whoami is in status `updating`. Waiting 1s...
2020-02-04 07:17:19.578 DEBUG [cioban._run] Service websites_whoami is in status `updating`. Waiting 1s...
2020-02-04 07:17:20.586 DEBUG [cioban._run] Service websites_whoami is in status `updating`. Waiting 1s...
2020-02-04 07:17:21.599 DEBUG [cioban._run] Service websites_whoami is in status `updating`. Waiting 1s...
2020-02-04 07:17:22.607 DEBUG [cioban._run] Service websites_whoami is in status `updating`. Waiting 1s...
2020-02-04 07:17:23.620 DEBUG [cioban._run] Service websites_whoami is in status `updating`. Waiting 1s...
2020-02-04 07:17:24.630 DEBUG [cioban._run] Service websites_whoami is in status `updating`. Waiting 1s...
2020-02-04 07:17:25.640 DEBUG [cioban._run] Service websites_whoami is in status `updating`. Waiting 1s...
2020-02-04 07:17:26.649 DEBUG [cioban._run] Service websites_whoami has converged.
2020-02-04 07:17:26.649 DEBUG [core.notify] Sending notification
2020-02-04 07:17:26.649 DEBUG [telegram_notifier.notify] Sending notification to telegram
2020-02-04 07:17:26.840 INFO [telegram_notifier.__post_message] Sent message to telegram.
2020-02-04 07:17:26.840 DEBUG [telegram_notifier.__post_message] Message: ☑ <b>CIOBAN: Service Updated</b> ☑
<b>Service Name</b>: websites_whoami
<b>Service Short Id</b>: z76ynth8m3
<b>Old Image</b>: containous/whoami:latest
<b>New Image</b>: containous/whoami:latest@sha256:c0d68a0f9acde95c5214bd057fd3ff1c871b2ef12dae2a9e2d2a3240fdd9214b

2020-02-04 07:17:26.841 INFO [cioban.run] Sleeping for 10 seconds
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
* `dev-branch` - the last build on a feature/development branch
* `dev-master` - the last build on the master branch

## Resources
* GitLab: https://gitlab.com/ix.ai/cioban
* GitHub: https://github.com/ix-ai/cioban
* Docker Hub: https://hub.docker.com/r/ixdotai/cioban
* ix.ai CI templates: https://gitlab.com/ix.ai/ci-templates

## Credits
Cioban is a fork of [shepherd](https://github.com/djmaze/shepherd). It has been completely rewritten in python.

### What is `cioban`?
Cioban is the Romanian translation of the word `shepherd`.
