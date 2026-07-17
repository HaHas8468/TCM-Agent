#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/_common.sh"

require_docker
require_env_file
validate_compose
compose logs --tail "${TCM_LOG_TAIL:-200}" -f "$@"
