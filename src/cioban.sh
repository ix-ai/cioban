#!/usr/bin/env bash
set -euo pipefail

log_me() {
  local verbose heartbeat action message show_message
  verbose=${VERBOSE:-}
  heartbeat=${DISABLE_HEARTBEAT:-}
  message="${1}"
  action="${2:-}"
  show_message="false"

  [[ -z "${action}" ]] && action="debug"

  case "${action}" in
    'debug')
      [[ -n "${verbose}" ]] && show_message="true"
      ;;
    'heartbeat')
      [[ -z "${heartbeat}" ]] && show_message="true"
      ;;
    *)
      show_message="true"
      ;;
  esac
  # shellcheck disable=SC2015
  [[ "${show_message}" == true ]] && /bin/echo "${action^^}: ${message}" || true
}

update_services() {
  local supports_detach_option=${1}
  local supports_registry_auth=${2}
  local filter="${FILTER_SERVICES:-}"
  local blacklist="${BLACKLIST_SERVICES:-}"
  local detach_option=""
  local registry_auth=""
  local service_name

  [ "${supports_detach_option}" = true ] && detach_option="--detach=false"
  [ "${supports_registry_auth}" = true ] && registry_auth="--with-registry-auth"

  for service_name in $(IFS=$'\n' docker service ls --quiet --format '{{.Name}}' --filter "${filter}"); do
    local image_with_digest image previous_image current_image

    if [[ " ${blacklist} " != *" ${service_name} "* ]]; then
      image_with_digest="$(docker service inspect "${service_name}" -f '{{.Spec.TaskTemplate.ContainerSpec.Image}}')"
      image=$(echo "${image_with_digest}" | cut -d@ -f1)
      log_me "Trying to update service ${service_name} with image ${image}"
      docker service update "${service_name}" ${detach_option} ${registry_auth} --image="${image}" > /dev/null

      previous_image=$(docker service inspect "${service_name}" -f '{{.PreviousSpec.TaskTemplate.ContainerSpec.Image}}')
      current_image=$(docker service inspect "${service_name}" -f '{{.Spec.TaskTemplate.ContainerSpec.Image}}')

      if [ "${previous_image}" == "${current_image}" ]; then
        log_me "No updates to service ${service_name}!"
      else
        log_me "Service ${service_name} was updated!" update
      fi

    fi
  done
}

# from https://stackoverflow.com/a/24067243/6914434
version_gt() {
  test "$(printf '%s\n' "$@" | sort -V | head -n 1)" != "$1"
}

main() {
  local server_version=""
  local supports_detach_option=false
  local supports_registry_auth=false
  local blacklist="${BLACKLIST_SERVICES:-}"
  local filter="${FILTER_SERVICES:-}"
  local sleep_time="${SLEEP_TIME:-5m}"
  local verbose="${VERBOSE:-}"
  local heartbeat="${DISABLE_HEARTBEAT:-}"

  server_version="$(docker version -f '{{.Server.Version}}')"
  if version_gt "${server_version}" "17.05" ; then
    supports_detach_option=true
    log_me "Server version is ${server_version}. Enabling synchronous service updates" init
  else
    log_me "Server version is ${server_version}. Not enabling synchronous service updates" init
  fi

  if [[ -f "/root/.docker/config.json" ]]; then
    supports_registry_auth=true
    log_me "/root/.docker/config.json found. Sending registry authentication details to swarm agents" init
  else
    log_me "/root/.docker/config.json not found. Not sending registry authentication details to swarm agents" init
  fi

  log_me "Sleep time is set to ${sleep_time}" init

  [[ -n "${blacklist}" ]] && log_me "Excluding services: ${blacklist}" init
  [[ -n "${filter}" ]] && log_me "Service filter is set to: ${filter}" init
  [[ -n "${heartbeat}" ]] && log_me "Heartbeat logging is disabled" init
  [[ -n "${verbose}" ]] && log_me "Verbose logging is enabled" init

  log_me "Starting" init

  while true; do
    log_me "Starting update run" heartbeat
    update_services "${supports_detach_option}" "${supports_registry_auth}"
    log_me "Sleeping ${sleep_time}" heartbeat
    sleep "${sleep_time}"
  done
}

main "$@"
