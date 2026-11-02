param([switch]$RegionOcr)
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$runtimePath = Join-Path $projectRoot 'classifier\engine\runtime.local.json'
$pipelinePython = (Get-Content -LiteralPath $runtimePath -Raw | ConvertFrom-Json).python
if (!(Test-Path -LiteralPath $pipelinePython)) { throw 'Classifier Python runtime is unavailable. Configure classifier/engine/runtime.local.json first.' }
Write-Host 'Open http://127.0.0.1:8772 in your browser. Close this terminal to stop the prototype.'
$pipelineArgs = @()
if ($RegionOcr) { $pipelineArgs += '--region-ocr' }
& $pipelinePython (Join-Path $PSScriptRoot 'gateway.py') @pipelineArgs

