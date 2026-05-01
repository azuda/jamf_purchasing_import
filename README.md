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
gpg .env.gpg
```

# usage

- create / rename file `assets.csv` with columns:
  - sn
  - purchase_date
  - vendor
  - price
- above filename and column names must match (case insensitive)
- move / copy `assets.csv` to project dir
- run `./run.sh`

> script run on avg takes ~1 minute / every 500 lines in assets.csv
