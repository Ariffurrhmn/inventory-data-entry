param([string]$Image,[string]$TextFile,[string]$Run)
$ErrorActionPreference='Stop'
$pythonPath=(Get-Content -LiteralPath (Join-Path $PSScriptRoot 'runtime.local.json') -Raw | ConvertFrom-Json).python
$predictionArguments=@((Join-Path $PSScriptRoot 'predict_text.py'))
if ($Image) {$predictionArguments+=@('--image',$Image)} elseif ($TextFile) {$predictionArguments+=@('--text-file',$TextFile)} else {throw 'Pass -Image or -TextFile.'}
if ($Run) {$predictionArguments+=@('--run',$Run)}
& $pythonPath @predictionArguments
if ($LASTEXITCODE -ne 0) {throw 'Classification failed; see the message above.'}
