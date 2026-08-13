# description

- read device purchasing data from csv
- match serial numbers with jamf device
- patch endpoint to update purchasing data in jamf 

# setup

macOS / Linux:

```sh
git clone https://github.com/azuda/jamf_purchasing_import
cd jamf_purchasing_import
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e "path/to/jamf_client[truststore]"
```

Windows Server (PowerShell):

```powershell
git clone https://github.com/azuda/jamf_purchasing_import
cd jamf_purchasing_import
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
pip install -e "path\to\jamf_client[truststore]"
```

> Requires Python 3.11+ (matching `jamf_client`'s `requires-python`).
> If `Activate.ps1` is blocked, run PowerShell as admin once:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

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
- run `./run.sh` (macOS/Linux) or `./run.ps1` (Windows)

> script run on avg takes ~1 minute / every 500 lines in assets.csv

# scheduling on Windows Server

`com.jamfpurchasing.daemon.plist` is the macOS/launchd equivalent; on Windows Server, register a
daily Scheduled Task pointing at `run.ps1` instead:

```powershell
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
  -Argument '-NoProfile -ExecutionPolicy Bypass -File "C:\path\to\jamf_purchasing_import\run.ps1"'
$trigger = New-ScheduledTaskTrigger -Daily -At 5pm
Register-ScheduledTask -TaskName "JamfPurchasingImport" -Action $action -Trigger $trigger
```
