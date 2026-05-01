#!/bin/sh

PROJECT="$PWD"
VENV="$PROJECT/.venv/bin/python3"

LOG_DIR="$PROJECT/logs"
timestamp=$(date '+%Y%m%d %H%M')
LOG_FILE="$LOG_DIR/$timestamp.log"
export LOG_FILE="$LOG_DIR/$timestamp.log"

mkdir -p "$LOG_DIR"
ls -1t "$LOG_DIR" | tail -n +5 | xargs -I {} rm -f "$LOG_DIR/{}"

echo "Script start @ $(date)\n" | tee -a "$LOG_FILE"

$VENV run.py 2>&1 | tee -a "$LOG_FILE"

echo "\nScript done @ $(date)" | tee -a "$LOG_FILE"
