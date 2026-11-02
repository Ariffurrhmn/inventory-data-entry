param([int]$Port=8767,[switch]$Open,[switch]$Foreground)
$ErrorActionPreference='Stop'
$pythonPath=(Get-Content -LiteralPath (Join-Path $PSScriptRoot 'runtime.local.json') -Raw | ConvertFrom-Json).python
if (!(Test-Path -LiteralPath $pythonPath)) { throw 'Classifier Python runtime not found. Update runtime.local.json.' }
$address="http://127.0.0.1:$Port"
if ($Foreground) { & $pythonPath -u "$PSScriptRoot\classifier_app.py" --port $Port; exit $LASTEXITCODE }
$active=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'active_text_model.json') -Raw | ConvertFrom-Json
$ready=$false
try { $model=Invoke-RestMethod "$address/api/model" -TimeoutSec 2; $ready=($model.scope_version -eq 'printed-only-v1' -and $model.run -eq $active.run) } catch {}
if (-not $ready) {
 $ownedScript=Join-Path $PSScriptRoot 'classifier_app.py'
 $ownedProcesses=Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine.Contains($ownedScript) -and $_.CommandLine -match "--port $Port( |$)" }
 foreach ($ownedProcess in $ownedProcesses) {Stop-Process -Id $ownedProcess.ProcessId -ErrorAction SilentlyContinue}
 $runtimeDirectory=Join-Path $PSScriptRoot '.runtime'
 New-Item -ItemType Directory -Path $runtimeDirectory -Force | Out-Null
 $serverProcess=Start-Process -FilePath $pythonPath -ArgumentList @('-u',"`"$PSScriptRoot\classifier_app.py`"",'--port',"$Port") -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runtimeDirectory 'classifier.log') -RedirectStandardError (Join-Path $runtimeDirectory 'classifier-error.log') -PassThru
 $serverProcess.Id | Set-Content (Join-Path $runtimeDirectory 'classifier.pid')
 for ($attempt=0;$attempt -lt 40;$attempt++) {
  Start-Sleep -Milliseconds 500
  try { $model=Invoke-RestMethod "$address/api/model" -TimeoutSec 2; if ($model.scope_version -eq 'printed-only-v1' -and $model.run -eq $active.run) { $ready=$true;break } } catch {}
  if ($serverProcess.HasExited) { break }
 }
 if (-not $ready) { throw "Classifier did not start. See $runtimeDirectory\classifier-error.log." }
}
Write-Output "Classifier ready: $address"
if ($Open) { Start-Process $address }
