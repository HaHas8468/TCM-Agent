#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/_common.sh"

require_commands sudo sed install systemctl
template="$REPO_ROOT/deploy/systemd/tcm-agent-cert-renew.service.in"
service_file=/etc/systemd/system/tcm-agent-cert-renew.service
timer_file=/etc/systemd/system/tcm-agent-cert-renew.timer
temporary_service=$(mktemp)
trap 'rm -f "$temporary_service"' EXIT

sed "s|@REPO_ROOT@|$REPO_ROOT|g" "$template" > "$temporary_service"
sudo install -m 0644 "$temporary_service" "$service_file"
sudo install -m 0644 "$REPO_ROOT/deploy/systemd/tcm-agent-cert-renew.timer" "$timer_file"
sudo systemctl daemon-reload
sudo systemctl enable --now tcm-agent-cert-renew.timer
log "已启用每日证书续期检查：systemctl list-timers tcm-agent-cert-renew.timer"
