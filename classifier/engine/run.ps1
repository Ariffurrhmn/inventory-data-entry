param(
 [ValidateSet('prepare','split','train','train-printed','finetune','evaluate','predict','predict-image','test')][string]$Action='predict',
 [string]$Image,[string]$Run,[string]$Python
)
$ErrorActionPreference='Stop'
if (!$Python) {
 $runtime=Join-Path $PSScriptRoot 'runtime.local.json'
 if (Test-Path -LiteralPath $runtime) {$Python=(Get-Content -LiteralPath $runtime -Raw | ConvertFrom-Json).python} else {$Python=Join-Path $PSScriptRoot '.venv\Scripts\python.exe'}
}
if (!(Test-Path -LiteralPath $Python)) {throw 'Pass -Python with the environment python.exe path.'}
$legacyRun=if ($Run) {$Run} else {'baseline'}
switch ($Action) {
 'test' {& $Python -m unittest discover -s $PSScriptRoot -p 'test_*.py'}
 'predict' {
  if (!$Image) {throw 'Pass -Image with a printed document image path.'}
  $predictionArguments=@((Join-Path $PSScriptRoot 'predict_text.py'),'--image',$Image)
  if ($Run) {$predictionArguments+=@('--run',$Run)}
  & $Python @predictionArguments
 }
 'predict-image' {if (!$Image) {throw 'Pass -Image.'}; & $Python (Join-Path $PSScriptRoot 'predict.py') $Image --run $legacyRun}
 'train-printed' {
  $trainingArguments=@((Join-Path $PSScriptRoot 'train_printed.py'))
  if ($Run) {$trainingArguments+=@('--run',$Run)}
  & $Python @trainingArguments
 }
 'train' {& $Python (Join-Path $PSScriptRoot 'train.py') --run $legacyRun}
 'finetune' {& $Python (Join-Path $PSScriptRoot 'finetune.py') --run $legacyRun}
 'evaluate' {& $Python (Join-Path $PSScriptRoot 'evaluate.py') --run $legacyRun}
 default {& $Python (Join-Path $PSScriptRoot ($Action+'.py'))}
}
if ($LASTEXITCODE -ne 0) {throw "Classifier command failed with exit code $LASTEXITCODE"}
