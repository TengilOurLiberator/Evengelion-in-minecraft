# Thin wrapper so the voice tools run in the right Python (the D:\voice-assistant environment).
#   .\tools\voices\voices.ps1 sheets
#   .\tools\voices\voices.ps1 audition --compare
#   .\tools\voices\voices.ps1 cut_takes D:\angel-attack\recording\take_MISATO.wav --speaker MISATO
#   .\tools\voices\voices.ps1 transform
#   .\tools\voices\voices.ps1 pack_sounds
# "sheets" is short for script_lines.py. Anything else is the name of a script in this folder.
param([Parameter(Position = 0, Mandatory = $true)][string]$Tool, [Parameter(ValueFromRemainingArguments = $true)]$Rest)

$python = "D:\voice-assistant\.venv\Scripts\python.exe"
$here = $PSScriptRoot
if ($Tool -eq "sheets") { $Tool = "script_lines" }
$script = Join-Path $here (($Tool -replace "\.py$", "") + ".py")
if (-not (Test-Path $script)) { Write-Error "no such tool: $Tool"; exit 2 }
$env:PYTHONWARNINGS = "ignore"
& $python -W ignore $script @Rest
exit $LASTEXITCODE
