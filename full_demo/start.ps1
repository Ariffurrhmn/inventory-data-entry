# Starts the end-to-end demo. Close the window (or press Ctrl+C) to stop it.
param([int]$Port=8790,[switch]$Lan,[switch]$Open,[ValidateSet('strict','demo_reconcile')][string]$Policy='demo_reconcile',[string]$ExtractorCmd='')
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$config=Join-Path $root 'classifier/engine/runtime.local.json'
if (!(Test-Path -LiteralPath $config)) {throw 'No Python runtime configured. Run classifier\Setup Demo.cmd first.'}
$python=(Get-Content -LiteralPath $config -Raw | ConvertFrom-Json).python
if (!(Test-Path -LiteralPath $python)) {throw 'Python runtime missing. Run classifier\Setup Demo.cmd.'}
if (!(Get-Command tesseract -ErrorAction SilentlyContinue)) {throw 'Tesseract is missing from PATH. See classifier/README.md.'}
# Optional: segno only draws the QR code. Native stderr must not abort the script on Windows PowerShell 5.1.
$previous=$ErrorActionPreference; $ErrorActionPreference='Continue'
& $python -c "import segno" 2>$null
if ($LASTEXITCODE -ne 0) { & $python -m pip install --quiet segno 2>$null | Out-Null }
$ErrorActionPreference=$previous
$serverArgs=@('-u',(Join-Path $PSScriptRoot 'server.py'),'--port',"$Port",'--policy',$Policy)
if ($Lan) {
  $serverArgs+='--lan'
  Write-Output 'Phone mode: if Windows Firewall asks, allow Python on PRIVATE networks so the phone can connect.'
}
if ($ExtractorCmd) { $serverArgs+=@('--extractor-cmd',$ExtractorCmd) }
if ($Open) { Start-Job { param($u) Start-Sleep 5; Start-Process $u } -ArgumentList "http://127.0.0.1:$Port/" | Out-Null }
& $python @serverArgs
