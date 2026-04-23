# run.py

"""
- get all computers and mobile devices from jamf api
- save device id and sn to json
"""

import csv
from jamf_credential import JAMF_URL, check_token_expiration, get_token, invalidate_token
import json
import os
import requests
import time
import urllib3

from util import convert_date_simple, convert_zoned_datetime

TESTING = True

# ==================================================================================

def jamf_get(endpoint, token):
  token["t"], token["expiration"] = check_token_expiration(token["t"], token["expiration"])

  url = f"{JAMF_URL}{endpoint}"
  headers = {
    "accept": "application/json",
    "authorization": f"Bearer {token["t"]}"
  }
  response = requests.get(url, headers=headers, verify=False)
  return response

def jamf_put(payload, endpoint, token):
  token["t"], token["expiration"] = check_token_expiration(token["t"], token["expiration"])

  url = f"{JAMF_URL}{endpoint}"
  headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "authorization": f"Bearer {token["t"]}"
  }
  response = requests.put(url, json=payload, headers=headers, verify=False)
  return response

def jamf_patch(payload, endpoint, token):
  token["t"], token["expiration"] = check_token_expiration(token["t"], token["expiration"])

  url = f"{JAMF_URL}{endpoint}"
  headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "authorization": f"Bearer {token["t"]}"
  }
  response = requests.patch(url, json=payload, headers=headers, verify=False)
  return response

# ==================================================================================

def main():
  # create jamf access token
  access_token, expires_in = get_token()
  token = {
    "t": access_token,
    "expiration": int(time.time()) + expires_in,
  }
  token_expiration_epoch = int(time.time()) + expires_in
  print(f"Token valid for {expires_in} seconds")

  # print jamf pro version
  version_url = f"{JAMF_URL}/api/v1/jamf-pro-version"
  headers = {"Authorization": f"Bearer {access_token}"}
  version = requests.get(version_url, headers=headers, verify=False)
  print("Jamf Pro version:", version.json()["version"])

  # computers
  computers = jamf_get("/JSSResource/computers/subset/basic", token).json()
  # mobile devices
  devices = jamf_get("/JSSResource/mobiledevices", token).json()

  # parse assetsonar csv to dict
  with open("data/assets.csv", "r") as f:
    reader = csv.DictReader(f)
    AS_DATA = {row["sn"]: {k: v for k, v in row.items() if k != "sn"} for row in reader}

  # write raw data handling stuff for debug
  if not os.path.exists("debug"):
    os.makedirs("debug")
  with open("debug/c.json", "w") as f:
    f.write(json.dumps(computers, indent=2))
  with open("debug/d.json", "w") as f:
    f.write(json.dumps(devices, indent=2))
  with open("debug/a.json", "w") as f:
    f.write(json.dumps(AS_DATA, indent=2))

  # update jamf pro with purchasing info from assetsonar
  count = 10
  for c in computers["computers"]:
    if TESTING:
      if count < 1:
        break
      count -= 1

    sn = c["serial_number"]
    if sn:
      print(f"Updating computer {c["id"]} {sn}")
      asset = AS_DATA[sn]
      payload = { "purchasing": {
        "leased": False,
        "purchased": True,
        "poNumber": "",
        "poDate": convert_date_simple(asset["po_date"]) if asset.get("po_date") else "",
        "vendor": asset["vendor"],
        "purchasePrice": f"${asset["price"]}",
        "lifeExpectancy": 0,
        "warrantyDate": None,
        "appleCareId": "",
        "leaseDate": None,
        "purchasingAccount": "",
        "purchasingContact": ""
        }}
      response = jamf_patch(payload, f"/api/v1/computers-inventory-detail/{c["id"]}", token)
      # print(response.status_code, response.text)

# same for devices
  count = 10
  for d in devices["mobile_devices"]:
    if TESTING:
      if count < 1:
        break
      count -= 1

    sn = d["serial_number"]
    if sn:
      print(f"Updating device {d["id"]} {sn}")
      try:
        asset = AS_DATA[sn]
      except KeyError as e:
        print(f"Error {e}: {d["id"]} {sn} not found in assets.csv, skipping...")
        continue
      payload = { "ios": { "purchasing": {
        "purchased": True,
        "leased": False,
        "poNumber": "",
        "vendor": asset["vendor"],
        "appleCareId": "",
        "purchasePrice": f"${asset["price"]}",
        "purchasingAccount": "",
        **({"poDate": convert_zoned_datetime(asset["po_date"])} if asset.get("po_date") else {}),
        "lifeExpectancy": 0,
        "purchasingContact": "",
      }}}
      # print(json.dumps(payload, indent=2))
      response = jamf_patch(payload, f"/api/v2/mobile-devices/{d["id"]}", token)
      # print(response.status_code, response.text)

  # kill jamf access token
  invalidate_token(access_token)

  print("\nDone")

# ==================================================================================

if __name__ == "__main__":
  urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
  main()
