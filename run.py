# run.py

"""
- get all computers and mobile devices from jamf
- read assets.csv to dict
- match computer / device by sn
- patch purchasing date, vendor, price to jamf
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
from dateutil import parser
from dateutil.relativedelta import relativedelta
from dateutil.tz import tzoffset
import jamf_client
from jamf_client import jamf_session, jamf_get, jamf_patch
import json
import os
import requests
import sys
import threading
import time

# on windows, stdout/stderr default to the legacy console codepage (eg cp1252)
# when not attached to a real console (Task Scheduler, piped through
# Tee-Object, etc), which can't encode arbitrary unicode and crashes print()
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

SEMAPHORE = threading.Semaphore(20)
PRINT_LOCK = threading.Lock()

TESTING = False
# TESTING = True

# RUN_ALL = False
RUN_ALL = True

# ==================================================================================

# define ambiguous timezones
TZ_INFO = {
  "EDT": tzoffset("EDT", -4 * 3600),  # UTC-4
  "EST": tzoffset("EST", -5 * 3600),  # UTC-5
  "CDT": tzoffset("CDT", -5 * 3600),  # UTC-5
  "CST": tzoffset("CST", -6 * 3600),  # UTC-6
  "MDT": tzoffset("MDT", -6 * 3600),  # UTC-6
  "MST": tzoffset("MST", -7 * 3600),  # UTC-7
  "PDT": tzoffset("PDT", -7 * 3600),  # UTC-7
  "PST": tzoffset("PST", -8 * 3600),  # UTC-8
}

def convert_dt_simple(timestamp):
  dt = parser.parse(timestamp)
  return dt.strftime("%Y-%m-%d")

def convert_dt_zoned(timestamp):
  dt = parser.parse(timestamp, tzinfos=TZ_INFO)
  milliseconds = dt.strftime("%f")[:3]
  return dt.strftime(f"%Y-%m-%dT%H:%M:%S.{milliseconds}Z")

def warranty_date_simple(po_date):
  if not po_date:
    return None
  dt = parser.parse(po_date) + relativedelta(years=3)
  return dt.strftime("%Y-%m-%d")

def warranty_date_zoned(po_date):
  if not po_date:
    return None
  dt = parser.parse(po_date, tzinfos=TZ_INFO) + relativedelta(years=3)
  milliseconds = dt.strftime("%f")[:3]
  return dt.strftime(f"%Y-%m-%dT%H:%M:%S.{milliseconds}Z")

# ==================================================================================

def patch_computer(c, assets, token, session):
  with SEMAPHORE:
    sn = c.get("hardware").get("serialNumber")
    if not sn:
      return
    if not RUN_ALL:
      if c.get("purchasing").get("purchasePrice"):
        safe_print(f"c Purchasing info already populated, skipping: {c.get('id')} {sn}")
        return
    # if int(c.get("id")) <= 3392:
    #   return
    asset = assets.get(sn)
    if asset is None:
      safe_print(f"c Not in assets.csv, skipping: {c.get('id')} {sn}")
      return
    payload = { "purchasing": {
      "leased": False,
      "purchased": True,
      "poNumber": asset.get("po_number", ""),
      "poDate": convert_dt_simple(asset.get("po_date", "")),
      "vendor": asset.get("vendor"),
      "purchasePrice": f"${asset.get('price')}",
      "lifeExpectancy": 0,
      "warrantyDate": warranty_date_simple(asset.get("po_date")),
      "appleCareId": asset.get("applecare", ""),
      "leaseDate": None,
      "purchasingAccount": "",
      "purchasingContact": ""
    }}
    try:
      # https://developer.jamf.com/jamf-pro/reference/patch_v3-computers-inventory-detail-id
      response = jamf_patch(payload, f"/api/v3/computers-inventory-detail/{c.get('id')}", token, session, raise_for_status=False)
      safe_print(f"c {c.get('id')}\t{sn} -> {response.status_code}")
      time.sleep(0.1)
    except requests.exceptions.Timeout:
      safe_print(f"c {c.get('id')}\t{sn} -> timed out, skipping")
    except requests.exceptions.ConnectionError as e:
      safe_print(f"c {c.get('id')}\t{sn} -> connection error: {e}, skipping")

def patch_device(d, assets, token, session):
  sn = d.get("hardware").get("serialNumber")
  if not sn:
    return
  if not RUN_ALL:
    if d.get("purchasing").get("purchasePrice"):
      safe_print(f"d Purchasing info already populated, skipping: {d.get('mobileDeviceId')} {sn}")
      return
  # if int(d.get("mobileDeviceId")) <= 1000:
  #   return
  asset = assets.get(sn)
  if asset is None:
    safe_print(f"d Not in assets.csv, skipping: {d.get('mobileDeviceId')} {sn}")
    return
  payload = { "ios": { "purchasing": {
    "purchased": True,
    "leased": False,
    "poNumber": asset.get("po_number", ""),
    "vendor": asset.get("vendor"),
    "appleCareId": asset.get("applecare", ""),
    "purchasePrice": f"${asset.get('price')}",
    "purchasingAccount": "",
    **({"poDate": convert_dt_zoned(asset["po_date"])} if asset.get("po_date") else {}),
    # note: jamf's PATCH /api/v2/mobile-devices/{id} throws a 500 if a date
    # field (eg warrantyExpiresDate, leaseExpiresDate) is sent as null, so
    # these are omitted entirely instead of set to None when there's no value
    **({"warrantyExpiresDate": warranty_date_zoned(asset["po_date"])} if asset.get("po_date") else {}),
    "lifeExpectancy": 0,
    "purchasingContact": "",
  }}}
  # https://developer.jamf.com/jamf-pro/reference/patch_v2-mobile-devices-id
  response = jamf_patch(payload, f"/api/v2/mobile-devices/{d.get('mobileDeviceId')}", token, session, raise_for_status=False)
  safe_print(f"d {d.get('mobileDeviceId')}\t{sn} -> {response.status_code}")

def safe_print(*args, **kwargs):
  with PRINT_LOCK:
    print(*args, **kwargs)

# ==================================================================================

def main():
  jamf_client.init()

  with jamf_session() as (token, session):
    # https://developer.jamf.com/jamf-pro/reference/get_v3-computers-inventory
    # https://developer.jamf.com/jamf-pro/reference/get_v2-mobile-devices-detail
    computers = jamf_get("/api/v3/computers-inventory?section=GENERAL&section=HARDWARE&section=PURCHASING&page=0&page-size=2000&sort=id%3Aasc", token, session).json()
    devices = jamf_get("/api/v2/mobile-devices/detail?section=GENERAL&section=HARDWARE&section=PURCHASING&page=0&page-size=2000&sort=mobileDeviceId%3Aasc", token, session).json()

    # parse assetsonar csv to dict
    with open("assets.csv", "r", encoding="utf-8-sig") as f:
      reader = csv.DictReader(f)
      assets = {row["sn"]: {k.lower(): v for k, v in row.items() if k.lower() != "sn"} for row in reader}

    # write raw data handling stuff for debug
    if not os.path.exists("debug"):
      os.makedirs("debug")
    with open("debug/c.json", "w") as f:
      f.write(json.dumps(computers, indent=2))
    with open("debug/d.json", "w") as f:
      f.write(json.dumps(devices, indent=2))
    with open("debug/a.json", "w") as f:
      f.write(json.dumps(assets, indent=2))

    computer_list = computers["results"][:10] if TESTING else computers["results"]
    device_list = devices["results"][:10] if TESTING else devices["results"]

    # computers
    with ThreadPoolExecutor(max_workers=10) as executor:
      futures = [executor.submit(patch_computer, c, assets, token, session) for c in computer_list]
      for f in as_completed(futures):
        f.result()

    # devices
    with ThreadPoolExecutor(max_workers=10) as executor:
      futures = [executor.submit(patch_device, d, assets, token, session) for d in device_list]
      for f in as_completed(futures):
        f.result()

# ==================================================================================

if __name__ == "__main__":
  main()
