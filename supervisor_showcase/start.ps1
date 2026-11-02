param([int]$Port = 8780, [switch]$Open, [switch]$Foreground)
# Starts the Supervisor Showcase. Finds a Python that can load the classifier, checks OCR, opens the browser.
$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot
$server = Join-Path $here 'server.py'
$address = "http://127.0.0.1:$Port"
$runtime = Join-Path $here '.runtime'
New-Item -ItemType Directory -Path $runtime -Force | Out-Null

function Test-Python([string[]]$cmd) {
  try {
    $exe = $cmd[0]; $pre = @(); if ($cmd.Count -gt 1) { $pre = $cmd[1..($cmd.Count - 1)] }
    $out = & $exe @pre -c "import sklearn,PIL,numpy,joblib,sys;print(sys.executable+'|'+sklearn.__version__)" 2>$null
    if ($LASTEXITCODE -eq 0 -and $out) { return ($out | Select-Object -Last 1) }
  } catch {}
  return $null
}

# 1. Python: classifier's configured runtime first, then installed versions.
$candidates = @()
$config = Join-Path $here '..\classifier\engine\runtime.local.json'
if (Test-Path -LiteralPath $config) {
  try { $p = (Get-Content -LiteralPath $config -Raw | ConvertFrom-Json).python; if ($p -and (Test-Path -LiteralPath $p)) { $candidates += , @($p) } } catch {}
}
foreach ($v in '-3.14', '-3.13', '-3.12', '-3') { if (Get-Command py -ErrorAction SilentlyContinue) { $candidates += , @('py', $v) } }
if (Get-Command python -ErrorAction SilentlyContinue) { $candidates += , @('python') }
$python = $null; $sk = $null
foreach ($c in $candidates) {
  $found = Test-Python $c
  if ($found) { $python, $sk = $found.Split('|'); break }
}
if (-not $python) {
  throw 'No Python with scikit-learn, Pillow, numpy and joblib was found. Install them with: py -m pip install -r classifier\requirements-demo.txt'
}
if ($sk -ne '1.9.1') { Write-Warning "scikit-learn $sk found; the saved model was trained with 1.9.1. Results may differ." }
if (-not (Get-Command tesseract -ErrorAction SilentlyContinue)) { Write-Warning 'Tesseract OCR is not on PATH. Recorded results will work; live OCR will not.' }

if ($Foreground) { & $python -u $server --port $Port; exit $LASTEXITCODE }

# 2. Reuse a running showcase on this port, otherwise start one.
$ready = $false
try { $info = Invoke-RestMethod "$address/api/info" -TimeoutSec 3; $ready = ($info.app_id -eq 'supervisor-showcase-v1') } catch {}
if (-not $ready) {
  if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) {
    throw "Port $Port is used by another program. Run: .\start.ps1 -Port 8781 -Open"
  }
  $proc = Start-Process -FilePath $python -ArgumentList @('-u', "`"$server`"", '--port', "$Port") -WorkingDirectory $here -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $runtime 'server.log') -RedirectStandardError (Join-Path $runtime 'server-error.log') -PassThru
  $proc.Id | Set-Content (Join-Path $runtime 'server.pid')
  for ($i = 0; $i -lt 60; $i++) {
    Start-Sleep -Milliseconds 400
    try { $info = Invoke-RestMethod "$address/api/info" -TimeoutSec 3; if ($info.app_id -eq 'supervisor-showcase-v1') { $ready = $true; break } } catch {}
    if ($proc.HasExited) { break }
  }
  if (-not $ready) { throw "Showcase did not start. See supervisor_showcase\.runtime\server-error.log" }
}
Write-Output "Supervisor Showcase ready: $address  (Python: $python)"
if ($Open) { Start-Process $address }
