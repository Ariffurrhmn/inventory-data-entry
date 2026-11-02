param([int]$Port=8770)
$serverScript=Join-Path $PSScriptRoot 'app/server.py'
$owned=Get-CimInstance Win32_Process | Where-Object {$_.CommandLine -and $_.CommandLine.Contains($serverScript) -and $_.CommandLine -match "--port $Port( |$)"}
foreach($process in $owned){Stop-Process -Id $process.ProcessId -ErrorAction SilentlyContinue}
Write-Output 'Document Lab stopped.'

