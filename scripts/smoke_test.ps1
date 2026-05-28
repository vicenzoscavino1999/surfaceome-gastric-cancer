$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

python src\utils\compare_outputs.py --self-test
python src\utils\compare_outputs.py --write-bootstrap-status results\tables\bootstrap_status.tsv
Get-Content results\tables\bootstrap_status.tsv
