# util.py

"""
- helper functions
"""

from dateutil import parser
from dateutil.tz import tzoffset

# ==================================================================================

# datetime handling

# define ambiguous timezones thx claude
TZ_INFO = {
  "CDT": tzoffset("CDT", -5 * 3600),  # UTC-5
  "CST": tzoffset("CST", -6 * 3600),  # UTC-6
  "EDT": tzoffset("EDT", -4 * 3600),  # UTC-4
  "EST": tzoffset("EST", -5 * 3600),  # UTC-5
  "MDT": tzoffset("MDT", -6 * 3600),  # UTC-6
  "MST": tzoffset("MST", -7 * 3600),  # UTC-7
  "PDT": tzoffset("PDT", -7 * 3600),  # UTC-7
  "PST": tzoffset("PST", -8 * 3600),  # UTC-8
}

def convert_datetime(timestamp):
  dt = parser.parse(timestamp, tzinfos=TZ_INFO)
  return dt.strftime("%Y-%m-%d %H:%M:%S")

def convert_date_epoch(timestamp):
  dt = parser.parse(timestamp, tzinfos=TZ_INFO)
  return int(dt.timestamp())

def convert_date_simple(timestamp):
  dt = parser.parse(timestamp)
  return dt.strftime("%Y-%m-%d")

def convert_zoned_datetime(timestamp):
  dt = parser.parse(timestamp, tzinfos=TZ_INFO)
  return dt.strftime(f"%Y-%m-%dT%H:%M:%S.{dt.strftime("%f")[:3]}Z")
