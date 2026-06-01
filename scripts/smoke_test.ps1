$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

function Invoke-PythonChecked {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$PythonArgs
    )
    & python @PythonArgs
    if ($LASTEXITCODE -ne 0) {
        throw "python $($PythonArgs -join ' ') failed with exit code $LASTEXITCODE"
    }
}

Invoke-PythonChecked src\utils\compare_outputs.py --self-test
Invoke-PythonChecked src\utils\compare_outputs.py --check-phase1-inventory
Invoke-PythonChecked src\utils\compare_outputs.py --check-phase2-downloads
Invoke-PythonChecked src\utils\compare_outputs.py --check-phase2-batch-diagnostic
Invoke-PythonChecked src\utils\compare_outputs.py --check-phase3-identifier-map
Invoke-PythonChecked src\utils\compare_outputs.py --check-phase4-surfaceome-universe
Invoke-PythonChecked src\utils\compare_outputs.py --check-phase4b-ranking-resolution
Invoke-PythonChecked src\utils\compare_outputs.py --check-phase5-tumor-expression
Invoke-PythonChecked src\utils\compare_outputs.py --check-phase6-normal-selectivity
Invoke-PythonChecked src\utils\compare_outputs.py --check-phase7-protein-evidence
Invoke-PythonChecked src\utils\compare_outputs.py --check-phase8-single-cell-tme
Invoke-PythonChecked src\utils\compare_outputs.py --check-phase9-topology-isoforms
Invoke-PythonChecked src\utils\compare_outputs.py --check-phase13-mvp-scoring
Invoke-PythonChecked src\utils\compare_outputs.py --check-phase14-preflight
Invoke-PythonChecked src\utils\compare_outputs.py --check-phase14-stability
Invoke-PythonChecked src\utils\compare_outputs.py --check-phase15-tiering
Invoke-PythonChecked src\utils\compare_outputs.py --check-phase16-figures-tables
Invoke-PythonChecked src\utils\compare_outputs.py --write-bootstrap-status results\tables\bootstrap_status.tsv
Get-Content results\tables\bootstrap_status.tsv
