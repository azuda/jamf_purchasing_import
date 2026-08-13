#Requires -Version 5.1

$Project = $PSScriptRoot
$Venv = Join-Path $Project ".venv\Scripts\python.exe"

$LogDir = Join-Path $Project "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$Timestamp = Get-Date -Format "yyyyMMdd HHmm"
$LogFile = Join-Path $LogDir "$Timestamp.log"
$env:LOG_FILE = $LogFile

# keep only the 4 most recent logs (plus the one about to be written)
Get-ChildItem $LogDir -File |
  Sort-Object LastWriteTime -Descending |
  Select-Object -Skip 4 |
  Remove-Item -Force

"Script start @ $(Get-Date)" | Tee-Object -FilePath $LogFile -Append

Push-Location $Project
try {
  & $Venv -u run.py 2>&1 | Tee-Object -FilePath $LogFile -Append
}
finally {
  Pop-Location
}

"Script done @ $(Get-Date)" | Tee-Object -FilePath $LogFile -Append
