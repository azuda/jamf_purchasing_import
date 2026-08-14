#!/bin/sh
#
# usage: ./update_assets.sh {encrypt|decrypt}

ACTION="$1"
KEY_FILE="$HOME/.age/jamf.txt"

case "$ACTION" in
  encrypt)
    age -r "$(grep "public key" "$KEY_FILE" | awk '{print $NF}')" -o assets.csv.age assets.csv
    ;;
  decrypt)
    age -d -i "$KEY_FILE" -o assets.csv assets.csv.age
    ;;
  *)
    echo "usage: $0 {encrypt|decrypt}" >&2
    exit 1
    ;;
esac
