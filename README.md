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

You can enable private registry authentication by mounting your credentials file to `/root/.docker/config.json`.

By setting `DISABLE_HEARTBEAT` you can disable the `HEARTBEAT: Sleeping ${SLEEP_TIME}` messages.

### Example:
```sh
docker service create \
    --name cioban \
    --constraint "node.role==manager" \
    --env SLEEP_TIME="3m" \
    --env BLACKLIST_SERVICES="cioban my-other-service" \
    --env FILTER_SERVICES="label=com.mydomain.autodeploy" \
    --env VERBOSE="true" \
    --env DISABLE_HEARTBEAT="true" \
    --mount type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock,rw \
    --mount type=bind,source=/root/.docker/config.json,target=/root/.docker/config.json,ro \
    ixdotai/cioban
```

#### Logs:
```
$ sudo docker service logs -f infra_cioban
infra_cioban.1.w78zwf6k9p3c@docker-a    | INIT: Server version is 19.03.1. Enabling synchronous service updates
infra_cioban.1.w78zwf6k9p3c@docker-a    | INIT: /root/.docker/config.json found. Sending registry authentication details to swarm agents
infra_cioban.1.w78zwf6k9p3c@docker-a    | INIT: Sleep time is set to 3m
infra_cioban.1.w78zwf6k9p3c@docker-a    | INIT: Excluding services: cioban my-other-service
infra_cioban.1.w78zwf6k9p3c@docker-a    | INIT: Service filter is set to: label=com.mydomain.autodeploy
infra_cioban.1.w78zwf6k9p3c@docker-a    | INIT: Heartbeat logging is disabled
infra_cioban.1.w78zwf6k9p3c@docker-a    | INIT: Verbose logging is enabled
infra_cioban.1.w78zwf6k9p3c@docker-a    | INIT: Starting
infra_cioban.1.w78zwf6k9p3c@docker-a    | DEBUG: Starting update
infra_cioban.1.w78zwf6k9p3c@docker-a    | DEBUG: Trying to update service karma_karma with image lmierzwa/karma:latest
infra_cioban.1.w78zwf6k9p3c@docker-a    | DEBUG: No updates to service karma_karma!
infra_cioban.1.w78zwf6k9p3c@docker-a    | DEBUG: Trying to update service karma_oauth with image quay.io/pusher/oauth2_proxy:v3.2.0
infra_cioban.1.w78zwf6k9p3c@docker-a    | DEBUG: No updates to service karma_oauth!
infra_cioban.1.w78zwf6k9p3c@docker-a    | DEBUG: Trying to update service smtp_smtp with image registry.gitlab.com/ix.ai/smtp:latest
infra_cioban.1.w78zwf6k9p3c@docker-a    | DEBUG: No updates to service smtp_smtp!
infra_cioban.1.w78zwf6k9p3c@docker-a    | DEBUG: Starting update
infra_cioban.1.w78zwf6k9p3c@docker-a    | DEBUG: Trying to update service karma_karma with image lmierzwa/karma:latest
infra_cioban.1.w78zwf6k9p3c@docker-a    | DEBUG: No updates to service karma_karma!
infra_cioban.1.w78zwf6k9p3c@docker-a    | DEBUG: Trying to update service karma_oauth with image quay.io/pusher/oauth2_proxy:v3.2.0
infra_cioban.1.w78zwf6k9p3c@docker-a    | DEBUG: No updates to service karma_oauth!
infra_cioban.1.w78zwf6k9p3c@docker-a    | DEBUG: Trying to update service smtp_smtp with image registry.gitlab.com/ix.ai/smtp:latest
infra_cioban.1.w78zwf6k9p3c@docker-a    | UPDATE: Service smtp_smtp was updated!

```

#### Docker event log:
```
$ sudo docker events
2019-08-29T15:19:10.077310036+02:00 service update ujyjwt7hdcjgilgzzoy8hqrcw (name=infra_cioban)
2019-08-29T15:19:18.597537438+02:00 service update fw431eab9n74cl7ypqv94g0ta (name=karma_karma)
2019-08-29T15:19:25.852090851+02:00 service update di9gntfu8499fj0u9r51tvvr3 (name=karma_oauth)
[...]
2019-08-29T15:22:46.805237839+02:00 service update kp3o6l3z0ik46bwzpq3x1xsxn (name=smtp_smtp, updatestate.new=updating)
2019-08-29T15:23:18.579770796+02:00 network disconnect pzix6mcc64jhgopxe7re7a0cg (container=e0bbdcb87a20ef4a0467cacc16c9905efc0dd3d7eadbc2dd7bc917743c614140, name=prometheus, type=overlay)
2019-08-29T15:23:29.595400581+02:00 network connect pzix6mcc64jhgopxe7re7a0cg (container=b27d93e2873469104be733f6ad3a37b7b6a04636536004b5d9781f1dd81d75d4, name=prometheus, type=overlay)
2019-08-29T15:23:36.541744915+02:00 service update kp3o6l3z0ik46bwzpq3x1xsxn (name=smtp_smtp, updatestate.new=completed, updatestate.old=updating)
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
