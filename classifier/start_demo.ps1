param([int]$Port=8770,[switch]$Open,[switch]$Foreground)
$ErrorActionPreference='Stop'
$config=Join-Path $PSScriptRoot 'runtime.local.json'
if (!(Test-Path -LiteralPath $config)) {$config=Join-Path $PSScriptRoot 'engine/runtime.local.json'}
$pythonPath=(Get-Content -LiteralPath $config -Raw | ConvertFrom-Json).python
if (!(Test-Path -LiteralPath $pythonPath)) {throw 'Python runtime missing. Run Setup Demo.cmd or update classifier/runtime.local.json.'}
if (!(Get-Command tesseract -ErrorAction SilentlyContinue)) {throw 'Tesseract is missing from PATH. See classifier/README.md.'}
$serverScript=Join-Path $PSScriptRoot 'app/server.py'
if ($Foreground) {& $pythonPath -u $serverScript --port $Port;exit $LASTEXITCODE}
$address="http://127.0.0.1:$Port"
$active=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'engine/active_text_model.json') -Raw | ConvertFrom-Json
$ready=$false
try {$info=Invoke-RestMethod "$address/api/info" -TimeoutSec 3;$ready=($info.app_id -eq 'document-lab-supervisor-v1' -and $info.app_root -eq $PSScriptRoot -and $info.model.model_sha256 -eq $active.model_sha256)} catch {}
if (!$ready) {
 $owned=Get-CimInstance Win32_Process | Where-Object {$_.CommandLine -and $_.CommandLine.Contains($serverScript) -and $_.CommandLine -match "--port $Port( |$)"}
 foreach($process in $owned){Stop-Process -Id $process.ProcessId -ErrorAction SilentlyContinue}
 $listener=Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
 if ($listener) {throw "Port $Port belongs to another service. Run start_demo.ps1 -Port 8771."}
 $runtime=Join-Path $PSScriptRoot '.runtime';New-Item -ItemType Directory -Path $runtime -Force | Out-Null
 $process=Start-Process -FilePath $pythonPath -ArgumentList @('-u',"`"$serverScript`"",'--port',"$Port") -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runtime 'demo.log') -RedirectStandardError (Join-Path $runtime 'demo-error.log') -PassThru
 $process.Id | Set-Content (Join-Path $runtime 'demo.pid')
 for($attempt=0;$attempt -lt 50;$attempt++){
  Start-Sleep -Milliseconds 400
  try {$info=Invoke-RestMethod "$address/api/info" -TimeoutSec 3;if($info.app_id -eq 'document-lab-supervisor-v1' -and $info.model.model_sha256 -eq $active.model_sha256){$ready=$true;break}}catch{}
  if($process.HasExited){break}
 }
 if(!$ready){throw "Demo did not start. Read classifier/.runtime/demo-error.log."}
}
Write-Output "Document Lab ready: $address"
if($Open){Start-Process $address}

