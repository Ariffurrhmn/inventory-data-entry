param([int]$Port=8765, [switch]$Open, [switch]$Foreground)
$ErrorActionPreference='Stop'
$pythonPath=(Get-Command python -ErrorAction Stop).Source
$portalUrl="http://127.0.0.1:$Port"
if ($Foreground) { & $pythonPath -u "$PSScriptRoot\server.py" --port $Port; exit $LASTEXITCODE }
$running=$false
try { $response=Invoke-RestMethod "$portalUrl/api/catalog" -TimeoutSec 3; $running=($response.storage -eq 'Dataset/annotations/human_review/reviews.sqlite3') } catch {}
if (-not $running) {
    $runtimeDir=Join-Path $PSScriptRoot '.runtime'
    New-Item -ItemType Directory -Path $runtimeDir -Force | Out-Null
    $process=Start-Process -FilePath $pythonPath -ArgumentList @('-u',"`"$PSScriptRoot\server.py`"",'--port',"$Port") -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runtimeDir 'server.log') -RedirectStandardError (Join-Path $runtimeDir 'server-error.log') -PassThru
    $process.Id | Set-Content (Join-Path $runtimeDir 'server.pid')
    for ($attempt=0; $attempt -lt 30; $attempt++) {
        Start-Sleep -Milliseconds 500
        try { $response=Invoke-RestMethod "$portalUrl/api/catalog" -TimeoutSec 2; if ($response.storage -eq 'Dataset/annotations/human_review/reviews.sqlite3') { $running=$true; break } } catch {}
        if ($process.HasExited) { break }
    }
    if (-not $running) { throw "Portal did not start. See $runtimeDir\server-error.log or select another port with -Port." }
}
Write-Output "Annotation portal ready: $portalUrl"
if ($Open) { Start-Process $portalUrl }
