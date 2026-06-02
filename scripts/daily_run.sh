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

# 当日エントリのネタ被り監査（実ファイルから台帳を再構築 → 当日衝突をチェック）。
# 監視目的。重複を検出しても日次実行は失敗させない。
log "=== ネタ被り監査 ==="
python3 "$PROJECT_DIR/scripts/build_ledger.py" >> "$LOGFILE" 2>&1 || log "build_ledger スキップ（exit $?）"
if python3 "$PROJECT_DIR/scripts/audit_ledger.py" --new "$DATE" >> "$LOGFILE" 2>&1; then
  log "=== 監査: 当日エントリに既習との衝突なし ==="
else
  log "=== ⚠ 監査: 当日エントリが既習トピックと衝突（上のログ参照・要確認）==="
fi

# 週次（月曜）は全期間の重複サマリーもログに残す
if [ "$(date +%u)" -eq 1 ]; then
  log "=== 週次フル重複監査 ==="
  python3 "$PROJECT_DIR/scripts/audit_ledger.py" >> "$LOGFILE" 2>&1 || true
fi
