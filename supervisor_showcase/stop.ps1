param([int]$Port = 8780)
# Stops only the showcase server this folder started.
$server = Join-Path $PSScriptRoot 'server.py'
$owned = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine.Contains($server) }
foreach ($p in $owned) { Stop-Process -Id $p.ProcessId -ErrorAction SilentlyContinue }
if ($owned) { Write-Output "Stopped Supervisor Showcase." } else { Write-Output "Supervisor Showcase was not running." }
