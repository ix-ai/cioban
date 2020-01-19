# cioban

[![Pipeline Status](https://gitlab.com/ix.ai/cioban/badges/master/pipeline.svg)](https://gitlab.com/ix.ai/cioban/)
[![Docker Stars](https://img.shields.io/docker/stars/ixdotai/cioban.svg)](https://hub.docker.com/r/ixdotai/cioban/)
[![Docker Pulls](https://img.shields.io/docker/pulls/ixdotai/cioban.svg)](https://hub.docker.com/r/ixdotai/cioban/)
[![Gitlab Project](https://img.shields.io/badge/GitLab-Project-554488.svg)](https://gitlab.com/ix.ai/cioban/)


A docker swarm service for automatically updating your services to the latest image tag push.

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

| **Variable**         | **Default** | **Description**                                                                                         |
|:---------------------|:-----------:|:--------------------------------------------------------------------------------------------------------|
| `SLEEP_TIME`         | `5s`        | Adjust the sleeping time. Accepted are numbers ending in one of `s`, `m`, `h`, `d`, `w`                 |
| `TIMEOUT`            | `60`        | Timeout in seconds for the update command                                                               |
| `BLACKLIST_SERVICES` | -           | Space-separated list of service names to exclude from updates                                           |
| `FILTER_SERVICES`    | -           | Anything accepted by the filtering flag in `docker service ls`. Example: `label=ai.ix.auto-update=true` |
| `LOGLEVEL`           | `WARNING`   | [Logging Level](https://docs.python.org/3/library/logging.html#levels)                                  |
| `GELF_HOST`          | -           | If set, GELF UDP logging to this host will be enabled                                                   |
| `GELF_PORT`          | `12201`     | Ignored, if `GELF_HOST` is unset. The UDP port for GELF logging                                         |
| `PORT`               | `9308`      | The port for prometheus metrics                                                                         |


## Deprecated

The following environment variables are deprecated:

| **Variable**        | **Description**                                                                                |
|:--------------------|:-----------------------------------------------------------------------------------------------|
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
    --env LOGLEVEL="INFO" \
    --env TIMEOUT="30" \
    --mount type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock \
    --mount type=bind,source=/root/.docker/config.json,target=/root/.docker/config.json,ro \
    ixdotai/cioban
```

#### Logs:
With `LOGLEVEL=DEBUG`
```
$ sudo docker service logs -f infra_cioban
infra_cioban.1.w78zwf6k9p3c@docker-a    | WARNING {cioban} [__init__] FILTER_SERVICES="label=com.mydomain.autodeploy=true"
infra_cioban.1.w78zwf6k9p3c@docker-a    | WARNING {cioban} [__init__] BLACKLIST_SERVICES="cioban karma_karma karma_oauth"
infra_cioban.1.w78zwf6k9p3c@docker-a    | WARNING {cioban} [__init__] DISABLE_HEARTBEAT is not set
infra_cioban.1.w78zwf6k9p3c@docker-a    | WARNING {cioban} [__init__] SLEEP_TIME="3m"
infra_cioban.1.w78zwf6k9p3c@docker-a    | WARNING {cioban} [run] Starting cioban with prometheus metrics on port 9308
infra_cioban.1.w78zwf6k9p3c@docker-a    | INFO {config} [find_config_file] Trying paths: ['/root/.docker/config.json', '/root/.dockercfg']
infra_cioban.1.w78zwf6k9p3c@docker-a    | INFO {config} [find_config_file] Found file at path: /root/.docker/config.json
infra_cioban.1.w78zwf6k9p3c@docker-a    | INFO {auth} [load_config] Found 'auths' section
infra_cioban.1.w78zwf6k9p3c@docker-a    | INFO {auth} [parse_auth] Found entry (registry='registry.gitlab.com', username='XXX-REDACTED-XXX')
infra_cioban.1.w78zwf6k9p3c@docker-a    | INFO {auth} [parse_auth] Auth data for https://index.docker.io/v1/ is absent. Client might be using a credentials store instead.
infra_cioban.1.w78zwf6k9p3c@docker-a    | INFO {auth} [load_config] Found 'credsStore' section
infra_cioban.1.w78zwf6k9p3c@docker-a    | WARNING {cioban} [run] Starting update run
infra_cioban.1.w78zwf6k9p3c@docker-a    | INFO {connectionpool} [_make_request] http://localhost:None "GET /v1.35/services HTTP/1.1" 200 None
infra_cioban.1.w78zwf6k9p3c@docker-a    | INFO {cioban} [get_services] Blacklisted karma_karma
infra_cioban.1.w78zwf6k9p3c@docker-a    | INFO {cioban} [get_services] Blacklisted karma_oauth
infra_cioban.1.w78zwf6k9p3c@docker-a    | INFO {cioban} [_run] Trying to update service smtp_smtp with image registry.gitlab.com/ix.ai/smtp:latest
infra_cioban.1.w78zwf6k9p3c@docker-a    | INFO {cioban} [_run] Update command: ["docker", "service", "update", "--with-registry-auth", "--image=registry.gitlab.com/ix.ai/smtp:latest", "pqs6wtscm1tq6yiqrmu4wv0of"]
infra_cioban.1.w78zwf6k9p3c@docker-a    | DEBUG {cioban} [_run] Update STDOUT: [b'pqs6wtscm1tq6yiqrmu4wv0of\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\ntu9j903lfdkp: host-mode port already in use on 1 node\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 0 out of 1 tasks\noverall progress: 1 out of 1 tasks\nverify: Waiting 5 seconds to verify that tasks are stable...\nverify: Waiting 5 seconds to verify that tasks are stable...\nverify: Waiting 5 seconds to verify that tasks are stable...\nverify: Waiting 5 seconds to verify that tasks are stable...\nverify: Waiting 5 seconds to verify that tasks are stable...\nverify: Waiting 4 seconds to verify that tasks are stable...\nverify: Waiting 4 seconds to verify that tasks are stable...\nverify: Waiting 4 seconds to verify that tasks are stable...\nverify: Waiting 4 seconds to verify that tasks are stable...\nverify: Waiting 4 seconds to verify that tasks are stable...\nverify: Waiting 3 seconds to verify that tasks are stable...\nverify: Waiting 3 seconds to verify that tasks are stable...\nverify: Waiting 3 seconds to verify that tasks are stable...\nverify: Waiting 3 seconds to verify that tasks are stable...\nverify: Waiting 3 seconds to verify that tasks are stable...\nverify: Waiting 2 seconds to verify that tasks are stable...\nverify: Waiting 2 seconds to verify that tasks are stable...\nverify: Waiting 2 seconds to verify that tasks are stable...\nverify: Waiting 2 seconds to verify that tasks are stable...\nverify: Waiting 1 seconds to verify that tasks are stable...\nverify: Waiting 1 seconds to verify that tasks are stable...\nverify: Waiting 1 seconds to verify that tasks are stable...\nverify: Waiting 1 seconds to verify that tasks are stable...\nverify: Waiting 1 seconds to verify that tasks are stable...\nverify: Service converged]\n'
infra_cioban.1.w78zwf6k9p3c@docker-a    | INFO {connectionpool} [_make_request] http://localhost:None "GET /v1.35/services/pqs6wtscm1tq6yiqrmu4wv0of HTTP/1.1" 200 None
infra_cioban.1.w78zwf6k9p3c@docker-a    | WARNING {cioban} [_run] Service smtp_smtp has been updated
infra_cioban.1.w78zwf6k9p3c@docker-a    | WARNING {cioban} [run] Sleeping for 3 minutes
infra_cioban.1.w78zwf6k9p3c@docker-a    | WARNING {cioban} [run] Starting update run
infra_cioban.1.w78zwf6k9p3c@docker-a    | INFO {connectionpool} [_make_request] http://localhost:None "GET /v1.35/services HTTP/1.1" 200 None
infra_cioban.1.w78zwf6k9p3c@docker-a    | INFO {cioban} [get_services] Blacklisted karma_karma
infra_cioban.1.w78zwf6k9p3c@docker-a    | INFO {cioban} [get_services] Blacklisted karma_oauth
infra_cioban.1.w78zwf6k9p3c@docker-a    | INFO {cioban} [_run] Trying to update service smtp_smtp with image registry.gitlab.com/ix.ai/smtp:latest
infra_cioban.1.w78zwf6k9p3c@docker-a    | INFO {cioban} [_run] Update command: ["docker", "service", "update", "--with-registry-auth", "--image=registry.gitlab.com/ix.ai/smtp:latest", "pqs6wtscm1tq6yiqrmu4wv0of"]
infra_cioban.1.w78zwf6k9p3c@docker-a    | DEBUG {cioban} [_run] Update STDOUT: b'pqs6wtscm1tq6yiqrmu4wv0of\noverall progress: 0 out of 1 tasks\noverall progress: 1 out of 1 tasks\nverify: Waiting 5 seconds to verify that tasks are stable...\nverify: Waiting 5 seconds to verify that tasks are stable...\nverify: Waiting 5 seconds to verify that tasks are stable...\nverify: Waiting 5 seconds to verify that tasks are stable...\nverify: Waiting 5 seconds to verify that tasks are stable...\nverify: Waiting 4 seconds to verify that tasks are stable...\nverify: Waiting 4 seconds to verify that tasks are stable...\nverify: Waiting 4 seconds to verify that tasks are stable...\nverify: Waiting 4 seconds to verify that tasks are stable...\nverify: Waiting 4 seconds to verify that tasks are stable...\nverify: Waiting 3 seconds to verify that tasks are stable...\nverify: Waiting 3 seconds to verify that tasks are stable...\nverify: Waiting 3 seconds to verify that tasks are stable...\nverify: Waiting 3 seconds to verify that tasks are stable...\nverify: Waiting 3 seconds to verify that tasks are stable...\nverify: Waiting 2 seconds to verify that tasks are stable...\nverify: Waiting 2 seconds to verify that tasks are stable...\nverify: Waiting 2 seconds to verify that tasks are stable...\nverify: Waiting 2 seconds to verify that tasks are stable...\nverify: Waiting 1 seconds to verify that tasks are stable...\nverify: Waiting 1 seconds to verify that tasks are stable...\nverify: Waiting 1 seconds to verify that tasks are stable...\nverify: Waiting 1 seconds to verify that tasks are stable...\nverify: Waiting 1 seconds to verify that tasks are stable...\nverify: Service converged\n'
infra_cioban.1.w78zwf6k9p3c@docker-a    | INFO {connectionpool} [_make_request] http://localhost:None "GET /v1.35/services/pqs6wtscm1tq6yiqrmu4wv0of HTTP/1.1" 200 None
infra_cioban.1.w78zwf6k9p3c@docker-a    | INFO {cioban} [_run] No updates for service smtp_smtp
infra_cioban.1.w78zwf6k9p3c@docker-a    | WARNING {cioban} [run] Sleeping for 3 minutes
```
With `LOGLEVEL=WARNING`
```
$ sudo docker service logs -f infra_cioban
infra_cioban.1.vr1ef401y9ql@docker-a    | WARNING {cioban} [__init__] FILTER_SERVICES="label=com.mydomain.autodeploy=true"
infra_cioban.1.vr1ef401y9ql@docker-a    | WARNING {cioban} [__init__] BLACKLIST_SERVICES="cioban karma_karma karma_oauth"
infra_cioban.1.vr1ef401y9ql@docker-a    | WARNING {cioban} [__init__] DISABLE_HEARTBEAT is not set
infra_cioban.1.vr1ef401y9ql@docker-a    | WARNING {cioban} [__init__] SLEEP_TIME="3m"
infra_cioban.1.vr1ef401y9ql@docker-a    | WARNING {cioban} [run] Starting cioban with prometheus metrics on port 9308
infra_cioban.1.vr1ef401y9ql@docker-a    | WARNING {cioban} [run] Starting update run
infra_cioban.1.vr1ef401y9ql@docker-a    | WARNING {cioban} [_run] Service smtp_smtp has been updated
infra_cioban.1.vr1ef401y9ql@docker-a    | WARNING {cioban} [run] Sleeping for 3 minutes
infra_cioban.1.vr1ef401y9ql@docker-a    | WARNING {cioban} [run] Starting update run
infra_cioban.1.vr1ef401y9ql@docker-a    | WARNING {cioban} [run] Sleeping for 3 minutes
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
Cioban just triggers updates by updating the image specification for each service, removing the current digest.

Most of the work is done by Docker which [resolves the image tag, checks the registry for a newer version and updates running container tasks as needed](https://docs.docker.com/engine/swarm/services/#update-a-services-image-after-creation).

Also, Docker handles all the work of [applying rolling updates](https://docs.docker.com/engine/swarm/swarm-tutorial/rolling-update/). So at least with replicated services, there should be no noticeable downtime.

## Tags and Arch

Starting with version 0.8.0, the images are multi-arch, with builds for amd64, arm64 and armv7.
* `vN.N.N` - for example 0.8.0
* `latest` - always pointing to the latest version
* `dev-branch` - the last build on a feature/development branch
* `dev-master` - the last build on the master branch

## Resources
* GitLab: https://gitlab.com/ix.ai/cioban
* Docker Hub: https://hub.docker.com/r/ixdotai/cioban
* ix.ai CI templates: https://gitlab.com/ix.ai/ci-templates

## Credits
Cioban is a fork of [shepherd](https://github.com/djmaze/shepherd). It has been completely rewritten in python.

### What is `cioban`?
Cioban is the Romanian translation of the word `shepherd`.
