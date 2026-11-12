$ErrorActionPreference = 'Stop'
$Script = Join-Path $PSScriptRoot 'vsp.py'
if (Get-Command py -ErrorAction SilentlyContinue) { & py -3 $Script @args }
elseif (Get-Command python -ErrorAction SilentlyContinue) { & python $Script @args }
elseif (Get-Command uv -ErrorAction SilentlyContinue) { & uv run --no-project --python 3.13 python $Script @args }
else { Write-Error 'Python 3.8+ or uv is required to bootstrap. Install Python or uv first.'; exit 1 }
exit $LASTEXITCODE
