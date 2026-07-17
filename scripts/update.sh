#!/usr/bin/env bash
set -euo pipefail
source "$(cd -- "$(dirname -- "$0")" && pwd)/_common.sh"

target=${1:-origin/main}
cd "$REPO_ROOT"
git diff --quiet && git diff --cached --quiet || die "工作区存在未提交改动；为避免覆盖，请先提交或暂存后再更新。"
current_branch=$(git branch --show-current)
[ "$current_branch" = "main" ] || die "更新脚本只允许在 main 分支执行，当前为 ${current_branch:-detached HEAD}。"
previous_revision=$(git rev-parse HEAD)

git fetch origin
git merge --ff-only "$target"
if ! "$SCRIPT_DIR/deploy.sh"; then
  log "新版本部署失败，正在回滚到 $previous_revision。"
  git reset --hard "$previous_revision"
  "$SCRIPT_DIR/deploy.sh" || die "代码与服务回滚失败，需要人工介入。"
  die "新版本部署失败，已回滚。"
fi
log "已更新并部署到 $(git rev-parse --short HEAD)。"
