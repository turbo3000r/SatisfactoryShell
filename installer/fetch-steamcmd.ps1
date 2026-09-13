# Download Valve's SteamCMD zip into installer/redist/ so the Inno compile
# can embed it. If this file is missing, setup downloads the same URL at install time.
$ErrorActionPreference = "Stop"
$destDir = Join-Path $PSScriptRoot "redist"
$dest = Join-Path $destDir "steamcmd.zip"
$url = "https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip"
New-Item -ItemType Directory -Force -Path $destDir | Out-Null
Write-Host "Downloading $url -> $dest"
Invoke-WebRequest -Uri $url -OutFile $dest
Write-Host ("OK {0:N1} MB" -f ((Get-Item $dest).Length / 1MB))
