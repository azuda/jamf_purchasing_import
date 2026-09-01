# update_device.py
#
# ad hoc: update purchasing info for a single device by serial number
# usage: python3 update_device.py <serial_number>

import sys
import csv
from urllib.parse import quote

import jamf_client
from jamf_client import jamf_session, jamf_get
from run import patch_computer, patch_device, safe_print

# ==================================================================================

def find_computer(sn, token, session):
  response = jamf_get(
    f"/api/v3/computers-inventory"
    f"?filter=hardware.serialNumber%3D%3D%22{quote(sn)}%22"
    "&section=GENERAL&section=HARDWARE&section=PURCHASING",
    token, session,
  ).json()
  results = response.get("results") or []
  return results[0] if results else None

def find_device(sn, token, session):
  response = jamf_get(
    f"/api/v2/mobile-devices/detail"
    f"?filter=hardware.serialNumber%3D%3D%22{quote(sn)}%22"
    "&section=GENERAL&section=HARDWARE&section=PURCHASING",
    token, session,
  ).json()
  results = response.get("results") or []
  return results[0] if results else None

# ==================================================================================

def main():
  if len(sys.argv) != 2:
    print(f"usage: {sys.argv[0]} <serial_number>", file=sys.stderr)
    sys.exit(1)
  sn = sys.argv[1]

  jamf_client.init()

  with jamf_session() as (token, session):
    with open("assets.csv", "r", encoding="utf-8-sig") as f:
      reader = csv.DictReader(f)
      assets = {row["sn"]: {k.lower(): v for k, v in row.items() if k.lower() != "sn"} for row in reader}

    if sn not in assets:
      safe_print(f"{sn} not in assets.csv, aborting")
      return

    computer = find_computer(sn, token, session)
    if computer:
      patch_computer(computer, assets, token, session)
      return

    device = find_device(sn, token, session)
    if device:
      patch_device(device, assets, token, session)
      return

    safe_print(f"{sn} not found in jamf, aborting")

# ==================================================================================

if __name__ == "__main__":
  main()
