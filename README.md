# description

- read device purchasing data from csv
- match serial numbers with jamf device
- patch endpoint to update purchasing data in jamf 

# setup

```sh
git clone https://github.com/azuda/jamf_purchasing_import
cd jamf_purchasing_import
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e "path/to/jamf_client[truststore]"
```

> Jamf API credentials (`CLIENT_ID` / `CLIENT_SECRET` / `JAMF_URL`) are managed by the
> [`jamf_client`](https://github.com/azuda/jamf_client) library, not this project. Set them in
> `jamf_client`'s own `.env` (see that repo's README) — this project's `.env`/`.env.gpg` are no
> longer read.

# usage

- when new devices are purchased, add new lines to `assets.csv`
- need columns:
  - purchase_date
  - price
  - vendor
  - sn
  - device name / model (optional)
- run `./run.sh`

> script run on avg takes ~1 minute / every 500 lines in assets.csv
