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
from dateutil.tz import tzoffset
from jamf_credential import JAMF_URL, check_token_expiration, get_token, invalidate_token
import json
import os
import requests
import time
import truststore
import urllib3

truststore.inject_into_ssl()

TESTING = False
# TESTING = True

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
  return dt.strftime(f"%Y-%m-%dT%H:%M:%S.{dt.strftime("%f")[:3]}Z")

# ==================================================================================

def make_session():
  session = requests.Session()
  retry = urllib3.util.retry.Retry(
    total=3,
    backoff_factor=0.5,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET", "PATCH"],
    raise_on_status=False,
  )
  adapter = requests.adapters.HTTPAdapter(max_retries=retry)
  session.mount("https://", adapter)
  return session

def jamf_get(endpoint, token, session):
  token["t"], token["expiration"] = check_token_expiration(token["t"], token["expiration"])
  url = f"{JAMF_URL}{endpoint}"
  headers = {
    "accept": "application/json",
    "authorization": f"Bearer {token["t"]}"
  }
  response = session.get(url, headers=headers)
  return response

def jamf_patch(payload, endpoint, token, session):
  token["t"], token["expiration"] = check_token_expiration(token["t"], token["expiration"])
  url = f"{JAMF_URL}{endpoint}"
  headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "authorization": f"Bearer {token["t"]}"
  }
  response = session.patch(url, json=payload, headers=headers)
  return response

def patch_computer(c, assets, token, session):
  sn = c.get("hardware").get("serialNumber")
  if not sn:
    return
  if c.get("purchasing").get("purchasePrice") is not None:
    print(f"Purchasing info already populated, skipping: {c.get('id')} {sn}")
    return
  # if int(c.get("id")) <= 3392:
  #   return
  asset = assets.get(sn)
  if asset is None:
    print(f"Not in assets.csv, skipping: {c.get('id')} {sn}")
    return
  payload = { "purchasing": {
    "leased": False,
    "purchased": True,
    "poNumber": "",
    "poDate": convert_dt_simple(asset.get("purchase_date", "")),
    "vendor": asset.get("vendor"),
    "purchasePrice": f"${asset.get('price')}",
    "lifeExpectancy": 0,
    "warrantyDate": None,
    "appleCareId": "",
    "leaseDate": None,
    "purchasingAccount": "",
    "purchasingContact": ""
  }}
  # https://developer.jamf.com/jamf-pro/reference/patch_v3-computers-inventory-detail-id
  response = jamf_patch(payload, f"/api/v3/computers-inventory-detail/{c.get('id')}", token, session)
  print(f"c {c.get('id')}\t{sn} → {response.status_code}")

def patch_device(d, assets, token, session):
  sn = d.get("hardware").get("serialNumber")
  if not sn:
    return
  if d.get("purchasing").get("purchasePrice") is not None:
    print(f"Purchasing info already populated, skipping: {d.get('mobileDeviceId')} {sn}")
    return
  # if int(d.get("mobileDeviceId")) <= 1000:
  #   return
  asset = assets.get(sn)
  if asset is None:
    print(f"Not in assets.csv, skipping: {d.get('mobileDeviceId')} {sn}")
    return
  payload = { "ios": { "purchasing": {
    "purchased": True,
    "leased": False,
    "poNumber": "",
    "vendor": asset.get("vendor"),
    "appleCareId": "",
    "purchasePrice": f"${asset.get('price')}",
    "purchasingAccount": "",
    **({"poDate": convert_dt_zoned(asset["purchase_date"])} if asset.get("purchase_date") else {}),
    "lifeExpectancy": 0,
    "purchasingContact": "",
  }}}
  # https://developer.jamf.com/jamf-pro/reference/patch_v2-mobile-devices-id
  response = jamf_patch(payload, f"/api/v2/mobile-devices/{d.get('mobileDeviceId')}", token, session)
  print(f"d {d.get('mobileDeviceId')}\t{sn} → {response.status_code}")

# ==================================================================================

def main():
  # create jamf access token
  access_token, expires_in = get_token()
  token = {
    "t": access_token,
    "expiration": int(time.time()) + expires_in,
  }

  session = make_session()

  # https://developer.jamf.com/jamf-pro/reference/get_v3-computers-inventory
  # https://developer.jamf.com/jamf-pro/reference/get_v2-mobile-devices-detail
  computers = jamf_get("/api/v3/computers-inventory?section=GENERAL&section=HARDWARE&section=PURCHASING&page=0&page-size=2000&sort=id%3Aasc", token, session).json()
  devices = jamf_get("/api/v2/mobile-devices/detail?section=GENERAL&section=HARDWARE&section=PURCHASING&page=0&page-size=100&sort=mobileDeviceId%3Aasc", token, session).json()

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

  # kill jamf access token
  invalidate_token(access_token)

# ==================================================================================

if __name__ == "__main__":
  main()
