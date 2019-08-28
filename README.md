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
    --mount type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock,rw \
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
Cioban will try to update your services every 5 minutes by default. You can adjust this value using the `SLEEP_TIME` variable.

You can prevent services from being updated by appending them to the `BLACKLIST_SERVICES` variable. This should be a space-separated list of service names.

Alternatively you can specify a filter for the services you want updated using the `FILTER_SERVICES` variable. This can be anything accepted by the filtering flag in `docker service ls`.

If you want to see all log messages about the update tries, set the `VERBOSE` variable.

You can enable private registry authentication by mounting your credentials file to `/root/.docker/config.json`

### Example:
```sh
docker service create \
    --name cioban \
    --constraint "node.role==manager" \
    --env SLEEP_TIME="5m" \
    --env BLACKLIST_SERVICES="cioban my-other-service" \
    --env FILTER_SERVICES="label=com.mydomain.autodeploy" \
    --env VERBOSE="true" \
    --mount type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock,rw \
    --mount type=bind,source=/root/.docker/config.json,target=/root/.docker/config.json,ro \
    ixdotai/cioban
```

### Logging example (without VERBOSE):
```
$ sudo docker service logs -f infra_cioban
infra_cioban.1.w78zwf6k9p3c@docker-a    | INIT: Server version is 19.03.1. Enabling synchronous service updates
infra_cioban.1.w78zwf6k9p3c@docker-a    | INIT: /root/.docker/config.json found. Sending registry authentication details to swarm agents
infra_cioban.1.w78zwf6k9p3c@docker-a    | INIT: Sleep time is set to 30s
infra_cioban.1.w78zwf6k9p3c@docker-a    | INIT: Starting
infra_cioban.1.w78zwf6k9p3c@docker-a    | RUN: Service exporters_gdax was updated!
infra_cioban.1.w78zwf6k9p3c@docker-a    | RUN: Service exporters_hitbtc was updated!
infra_cioban.1.w78zwf6k9p3c@docker-a    | RUN: Service exporters_kraken was updated!
```
## How does it work?
Cioban just triggers updates by updating the image specification for each service, removing the current digest.

Most of the work is done by Docker which [resolves the image tag, checks the registry for a newer version and updates running container tasks as needed](https://docs.docker.com/engine/swarm/services/#update-a-services-image-after-creation).

Also, Docker handles all the work of [applying rolling updates](https://docs.docker.com/engine/swarm/swarm-tutorial/rolling-update/). So at least with replicated services, there should be no noticeable downtime.

## Resources
* GitLab: https://gitlab.com/ix.ai/cioban
* Docker Hub: https://hub.docker.com/r/ixdotai/cioban

## Credits
Cioban is a fork of [shepherd](https://github.com/djmaze/shepherd).

### What is `cioban`?
Cioban is the Romanian translation of the word `shepherd`.
