$ErrorActionPreference = "Continue"

$previousLang = $env:LANG
$previousLcAll = $env:LC_ALL
$previousLcCtype = $env:LC_CTYPE

Push-Location $PSScriptRoot
try {
    $env:LANG = "C"
    $env:LC_ALL = "C"
    $env:LC_CTYPE = "C"
    $auxiliaryExtensions = @(".aux", ".bbl", ".bcf", ".blg", ".fdb_latexmk", ".fls", ".log", ".out", ".run.xml", ".toc")
    foreach ($extension in $auxiliaryExtensions) {
        $path = Join-Path $PSScriptRoot ("cbc_manuscript" + $extension)
        if (Test-Path -LiteralPath $path) {
            Remove-Item -LiteralPath $path -Force
        }
    }
    latexmk -pdf -interaction=nonstopmode -halt-on-error cbc_manuscript.tex
    if ($LASTEXITCODE -ne 0) {
        throw "latexmk failed with exit code $LASTEXITCODE"
    }
    $rotateScript = Join-Path $PSScriptRoot "..\..\scripts\finalize_landscape_rotation.py"
    python $rotateScript "cbc_manuscript.pdf"
    if ($LASTEXITCODE -ne 0) {
        throw "landscape rotation post-processing failed with exit code $LASTEXITCODE"
    }
}
finally {
    $env:LANG = $previousLang
    $env:LC_ALL = $previousLcAll
    $env:LC_CTYPE = $previousLcCtype
    Pop-Location
}
