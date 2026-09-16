# test_org_devices.py
#
# Regenerates the client assertion via asm_client.py, exchanges it for an
# access token, then GETs /v1/orgDevices from the Apple School Manager API.

from dotenv import load_dotenv
import json
import os
import requests
import subprocess
import sys

load_dotenv()

TOKEN_URL = "https://account.apple.com/auth/oauth2/v2/token"
API_URL = "https://api-school.apple.com/v1/orgDevices"

script_dir = os.path.dirname(os.path.abspath(__file__))
client_id = os.environ["ASM_CLIENT_ID"]

# Regenerate asm_client_assertion.txt using asm_client.py.
subprocess.run([sys.executable, os.path.join(script_dir, "asm_client.py")], check=True)

with open(os.path.join(script_dir, "asm_client_assertion.txt"), "rt") as f:
  client_assertion = f.read().strip()

token_response = requests.post(
  TOKEN_URL,
  data={
    "grant_type": "client_credentials",
    "client_id": client_id,
    "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
    "client_assertion": client_assertion,
    "scope": "school.api",
  },
  headers={"Content-Type": "application/x-www-form-urlencoded"},
)

print(f"Token request status: {token_response.status_code}")
if not token_response.ok:
  print(token_response.text)
  sys.exit(1)

access_token = token_response.json()["access_token"]

headers = {"Authorization": f"Bearer {access_token}"}
devices = []
url = API_URL
params = {
  "limit": 1000,
  "fields[orgDevices]": "serialNumber,deviceModel,status,addedToOrgDateTime,releasedFromOrgDateTime,partNumber,orderNumber,purchaseSourceType",
}

while url:
  api_response = requests.get(url, headers=headers, params=params)
  print(f"orgDevices status: {api_response.status_code} (fetched {len(devices)} so far)")
  if not api_response.ok:
    print(api_response.text)
    sys.exit(1)

  page = api_response.json()
  devices.extend(page["data"])

  url = page.get("links", {}).get("next")
  params = None  # cursor is already embedded in the next link

print(f"Total devices: {len(devices)}")

# Keep only devices still in the org (releasedFromOrgDateTime not set).
active_devices = [
  d for d in devices if not d["attributes"].get("releasedFromOrgDateTime")
]

print(f"Active (not released) devices: {len(active_devices)}")

output_file = os.path.join(script_dir, "debug/asm_devices.json")
with open(output_file, "wt") as f:
  json.dump(active_devices, f, indent=2)

print(f"Wrote {len(active_devices)} devices to {output_file}")
