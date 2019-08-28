#!/usr/bin/env bash
set -euo pipefail

server_version() {
  docker version -f "{{.Server.Version}}"
}

update_services() {
  local blacklist="${1}"
  local supports_detach_option=${2}
  local supports_registry_auth=${3}
  local detach_option=""
  local registry_auth=""
  local service_name
  local verbose=${VERBOSE:-}

  [ "${supports_detach_option}" = true ] && detach_option="--detach=false"
  [ "${supports_registry_auth}" = true ] && registry_auth="--with-registry-auth"

  for service_name in $(IFS=$'\n' docker service ls --quiet --format '{{.Name}}' --filter "${FILTER_SERVICES}"); do
    local image_with_digest image previous_image current_image

    if [[ " ${blacklist} " != *" ${service_name} "* ]]; then
      image_with_digest="$(docker service inspect "${service_name}" -f '{{.Spec.TaskTemplate.ContainerSpec.Image}}')"
      image=$(echo "${image_with_digest}" | cut -d@ -f1)
      [ "${verbose}" = "true" ] && echo "Trying to update service ${service_name} with image ${image}"
      docker service update "${service_name}" ${detach_option} ${registry_auth} --image="${image}" > /dev/null

      previous_image=$(docker service inspect "${service_name}" -f '{{.PreviousSpec.TaskTemplate.ContainerSpec.Image}}')
      current_image=$(docker service inspect "${service_name}" -f '{{.Spec.TaskTemplate.ContainerSpec.Image}}')

      if [ "${previous_image}" == "${current_image}" ]; then
        [ "${verbose}" = "true" ] && echo "No updates to service ${service_name}!"
      else
        echo "Service ${service_name} was updated!"
      fi

    fi
  done
}

# from https://stackoverflow.com/a/24067243/6914434
version_gt() {
  test "$(printf '%s\n' "$@" | sort -V | head -n 1)" != "$1"
}

main() {
  local blacklist sleep_time supports_detach_option supports_registry_auth
  blacklist="${BLACKLIST_SERVICES:-}"
  sleep_time="${SLEEP_TIME:-5m}"

  supports_detach_option=false
  if version_gt "$(server_version)" "17.05" ; then
    supports_detach_option=true
    echo "Enabling synchronous service updates"
  fi

  supports_registry_auth=false
  if [[ -f "/root/.docker/config.json" ]]; then
    supports_registry_auth=true
    echo "Send registry authentication details to swarm agents"
  fi

  [[ "${blacklist}" != "" ]] && echo "Excluding services: ${blacklist}"

  while true; do
    update_services "${blacklist}" "${supports_detach_option}" "${supports_registry_auth}"
    echo "Sleeping ${sleep_time} before next update"
    sleep "${sleep_time}"
  done
}

main "$@"
