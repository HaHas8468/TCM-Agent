#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/_common.sh"

require_docker
require_env_file
validate_compose
compose ps

patient_port=$(env_value PATIENT_PORT)
doctor_port=$(env_value DOCTOR_PORT)
curl -fsS --max-time 10 "http://127.0.0.1:${patient_port}/healthz" || true
curl -fsS --max-time 10 "http://127.0.0.1:${doctor_port}/healthz" || true
