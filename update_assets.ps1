# usage: .\update_assets.ps1 {encrypt|decrypt}

param(
  [Parameter(Mandatory = $true)]
  [ValidateSet("encrypt", "decrypt")]
  [string]$Action
)

$KeyFile = "..\.age\jamf.txt"

switch ($Action) {
  "encrypt" {
    $PublicKey = (Select-String -Path $KeyFile -Pattern "public key").Line.Split()[-1]
    age -r $PublicKey -o assets.csv.age assets.csv
  }
  "decrypt" {
    age -d -i $KeyFile -o assets.csv assets.csv.age
  }
}
