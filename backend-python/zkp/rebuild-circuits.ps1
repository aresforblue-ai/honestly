$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Path $MyInvocation.MyCommand.Definition -Parent)

$circuits = @("age", "authenticity", "age_level3", "level3_inequality")
$ptau = "artifacts/common/pot16_final.ptau"
$ptauUrl = "https://hermez.s3-eu-west-1.amazonaws.com/powersOfTau28_hez_final_16.ptau"

Write-Host "=== ZKP rebuild (Windows) ==="
if (!(Test-Path $ptau)) {
  Write-Host "Downloading ptau..."
  Invoke-WebRequest -Uri $ptauUrl -OutFile $ptau
}

npm install

Write-Host "Compiling circuits..."
npm run build:age
npm run build:auth
npm run build:age-level3
npm run build:inequality-level3

Write-Host "Groth16 setup..."
npm run setup:age
npm run setup:auth
npm run setup:age-level3
npm run setup:inequality-level3

Write-Host "Contribute and export vkeys..."
npm run contribute:age; npm run vk:age
npm run contribute:auth; npm run vk:auth
npm run contribute:age-level3; npm run vk:age-level3
npm run contribute:inequality-level3; npm run vk:inequality-level3

Write-Host "Generating integrity hashes..."
python scripts/verify_key_integrity.py generate

Write-Host "Done."

