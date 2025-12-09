param(
    [string]$PythonBin = "python",
    [string]$VenvDir = ".venv"
)

Write-Host "Welcome to the Doxibox setup (Windows)."
$inputVenv = Read-Host "Virtualenv directory [$VenvDir]"
if ($inputVenv) { $VenvDir = $inputVenv }

Write-Host "Select extras to install (comma-separated). Options: dev,audio,tts,asr,llm,modal,full"
$extrasInput = Read-Host "Extras [dev]"
if (-not $extrasInput) { $extrasInput = "dev" }
$Extras = $extrasInput

if (-not (Get-Command $PythonBin -ErrorAction SilentlyContinue)) {
    Write-Error "Python not found: $PythonBin"
    exit 1
}

if (-not (Test-Path $VenvDir)) {
    & $PythonBin -m venv $VenvDir
}

$activate = Join-Path $VenvDir "Scripts/Activate.ps1"
. $activate

pip install --upgrade pip
pip install -e ".[${Extras}]"

Write-Output @" 
Doxibox environment ready.
- To activate: .\$VenvDir\Scripts\Activate.ps1
- To run tests: pytest

Optional Modal setup (for remote LLM execution):
  pip install modal
  python -m modal setup
"@
