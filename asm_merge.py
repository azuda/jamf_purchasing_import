# add_order_numbers.py
#
# Overwrites po_number values in assets.csv using orderNumber from
# debug/asm_devices.json (matched by serial number). ASM is treated as the
# source of truth, so any existing po_number is replaced when a match
# is found; rows with no matching serial are left untouched.
#
# Also fills applecare with partNumber from the same ASM record, but only
# for rows currently marked 'Yes' (a placeholder meaning "has AppleCare,
# part number unknown"); 'None' and other existing part numbers are left
# alone.

import csv
import json
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
devices_file = os.path.join(script_dir, "debug/asm_devices.json")
assets_file = os.path.join(script_dir, "assets.csv")

with open(devices_file, "rt") as f:
  devices = json.load(f)

order_numbers = {
  d["attributes"]["serialNumber"]: d["attributes"].get("orderNumber", "")
  for d in devices
}

part_numbers = {
  d["attributes"]["serialNumber"]: d["attributes"].get("partNumber", "")
  for d in devices
}

with open(assets_file, "rt", encoding="utf-8-sig", newline="") as f:
  reader = csv.DictReader(f)
  fieldnames = reader.fieldnames
  rows = list(reader)

overwritten = 0
filled = 0
applecare_filled = 0
for row in rows:
  order_number = order_numbers.get(row["sn"], "")
  if order_number:
    existing = row["po_number"].strip()
    if existing and existing != order_number:
      overwritten += 1
      print(f"overwrite sn={row['sn']}: po_number={existing!r} -> {order_number!r}")
    elif not existing:
      filled += 1
    row["po_number"] = order_number

  if row["applecare"].strip() == "Yes":
    part_number = part_numbers.get(row["sn"], "")
    if part_number:
      row["applecare"] = part_number
      applecare_filled += 1

with open(assets_file, "wt", encoding="utf-8", newline="") as f:
  writer = csv.DictWriter(f, fieldnames=fieldnames)
  writer.writeheader()
  writer.writerows(rows)

print(f"Filled {filled} blank po_number values; overwrote {overwritten} differing po_number values")
print(f"Replaced {applecare_filled} 'Yes' applecare values with a partNumber")
