param([string]$EnvironmentPath=(Join-Path $env:LOCALAPPDATA 'DocumentLab/python-env'))
$ErrorActionPreference='Stop'
if (!(Get-Command tesseract -ErrorAction SilentlyContinue)) {throw 'Install Tesseract and add it to PATH first; see README.md.'}
if (!(Test-Path -LiteralPath (Join-Path $EnvironmentPath 'Scripts/python.exe'))) {
 # Any Python 3.12+ works; scikit-learn 1.9.1 has wheels for 3.12-3.14.
 $created=$false
 foreach($version in '-3.12','-3.13','-3.14'){
  & py $version -c "pass" 2>$null
  if($LASTEXITCODE -eq 0){& py $version -m venv $EnvironmentPath; if($LASTEXITCODE -eq 0){$created=$true;break}}
 }
 if(!$created){throw 'Python 3.12, 3.13 or 3.14 is required. Install it before running setup.'}
}
$pythonPath=Join-Path $EnvironmentPath 'Scripts/python.exe'
& $pythonPath -m pip install -r (Join-Path $PSScriptRoot 'requirements-demo.txt')
if($LASTEXITCODE){throw 'Dependency setup failed.'}
# engine/runtime.local.json is shared by this demo, services/document_pipeline and supervisor_showcase.
@{python=$pythonPath} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'engine/runtime.local.json') -Encoding utf8
Write-Output 'Ready. Double-click Open Demo.cmd.'
