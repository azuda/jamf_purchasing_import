# description

- read device purchasing data from csv
- match serial numbers with device id in jamf
- call jamf api patch endpoint to update purchasing data

# setup

```sh
git clone https://github.com/azuda/jamf_purchasing_import
cd jamf_purchasing_import
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
gpg --output .env --decrypt .env.gpg
```

# usage

- create / rename file `assets.csv` with columns:
  - sn
  - po_date
  - vendor
  - price
- above filename and column names must match (case insensitive)
- move / copy `assets.csv` to project dir
- run `./run.sh`
