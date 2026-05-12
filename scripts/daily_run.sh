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

cd "$PROJECT_DIR"

# 気になる人の直近ツイートを取得（data/x/<DATE>.json）。失敗しても /learn は止めない
log "=== X 取得 ==="
if python3 "$PROJECT_DIR/scripts/fetch_x.py" "$DATE" >> "$LOGFILE" 2>&1; then
  log "=== X 取得 完了 ==="
else
  log "=== X 取得 失敗（続行・exit $?）==="
fi

log "=== /learn 起動 ==="

if claude -p "/learn" \
  --add-dir "$PROJECT_DIR" \
  --permission-mode bypassPermissions \
  >> "$LOGFILE" 2>&1; then
  log "=== /learn 完了 ==="
else
  log "=== /learn でエラー発生（exit code $?）==="
  exit 1
fi
