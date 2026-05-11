#!/bin/bash
# ============================================
# daily_run.sh - 毎朝6時に /learn skill を実行
# ============================================

set -euo pipefail

export PATH="/Users/nao/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
set -a
source "$PROJECT_DIR/config/.env"
set +a
LOG_DIR="$PROJECT_DIR/data/logs"
DATE=$(date +%Y-%m-%d)
LOGFILE="$LOG_DIR/daily_${DATE}.log"

mkdir -p "$LOG_DIR"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOGFILE"
}

log "=== /learn 起動 ==="

cd "$PROJECT_DIR"

if claude -p "/learn" \
  --add-dir "$PROJECT_DIR" \
  --permission-mode bypassPermissions \
  >> "$LOGFILE" 2>&1; then
  log "=== /learn 完了 ==="
else
  log "=== /learn でエラー発生（exit code $?）==="
  exit 1
fi
