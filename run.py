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
  computers = jamf_get("/JSSResource/computers/subset/basic", token)
  # mobile devices
  devices = jamf_get("/JSSResource/mobiledevices", token)

  # write raw
  if not os.path.exists("debug"):
    os.makedirs("debug")
  with open("debug/c.json", "w") as f:
    f.write(json.dumps(computers.json(), indent=2))
  with open("debug/d.json", "w") as f:
    f.write(json.dumps(devices.json(), indent=2))

  # parse assetsonar csv to dict
  AS_DATA = {}
  with open("data/as.csv", "r") as f:
    reader = csv.reader(f)
    for row in reader:
      AS_DATA[row[0]] = {}

  # update jamf pro with purchasing info from assetsonar
  for c in computers:
    jamf_id = c["id"]
    sn = c["serial_number"]
    if False: # if match with assetsonar row
      print(f"Updating computer {sn} with id {jamf_id}")
      as_row = AS_DATA.get(sn)
      payload = { "purchasing": {
        "leased": False,
        "purchased": True,
        "poNumber": "",
        "poDate": "",
        "vendor": "",
        "purchasePrice": "",
        "lifeExpectancy": 0,
        "warrantyDate": "",
        "appleCareId": "",
        "leaseDate": "",
        "purchasingAccount": "",
        "purchasingContact": ""
        }}
      jamf_patch(payload, f"/api/v1/computers-inventory-detail/{jamf_id}", token)

# same for devices



  # kill jamf access token
  invalidate_token(access_token)

  # # write results
  # if not os.path.exists("data"):
  #   os.makedirs("data")
  # with open("data/computers.json", "w") as f:
  #   f.write(json.dumps(computers, indent=2))
  # print("--- Jamf computers saved to ./data/computers.json ---")
  # with open("data/devices.json", "w") as f:
  #   f.write(json.dumps(devices, indent=2))
  # print("--- Jamf devices saved to ./data/devices.json ---")

  print("\nDone")

# ==================================================================================

if __name__ == "__main__":
  urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
  main()
