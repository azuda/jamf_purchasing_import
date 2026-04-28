#!/bin/sh

PROJECT="$PWD"
VENV="$PROJECT/.venv/bin/python3"

LOG_DIR="$PROJECT/logs"
timestamp=$(date '+%Y%m%d %H%M')
LOG_FILE="$LOG_DIR/$timestamp.log"
export LOG_FILE="$LOG_DIR/$timestamp.log"

mkdir -p "$LOG_DIR"
ls -1t "$LOG_DIR" | tail -n +5 | xargs -I {} rm -f "$LOG_DIR/{}"

echo "Script start @ $(date)\n" >> "$LOG_FILE" 2>&1

$VENV run.py >> "$LOG_FILE" 2>&1

echo "\nScript done @ $(date)" >> "$LOG_FILE" 2>&1
